import subprocess
import pexpect
import threading
import json
import time
import sys
import yaml
from pathlib import Path
from typing import Optional

from mcshell.constants import *
from mcshell.ppdownloader import PaperDownloader

class PaperServerManager:
    """Manages the lifecycle of a single Paper server subprocess using a local JRE."""

    def __init__(self, world_name: str, world_directory: Path):
        self.world_name = world_name
        self.world_directory = world_directory
        self.process: Optional[pexpect.spawn] = None
        self.thread: Optional[threading.Thread] = None

        # Load the world manifest to determine the JAR path
        manifest_path = self.world_directory / 'world_manifest.json'
        with manifest_path.open('rb') as f:
            self.world_manifest = json.load(f)

        # Path to the Paper JAR is stored relative to the worlds base directory
        self.jar_path = self.world_directory.parent / self.world_manifest.get('server_jar_path')

    def apply_manifest_settings(self):
        """
        Applies settings from world_manifest.json to server.properties,
        FruitJuice/config.yml, and paper-global.yml.
        """
        print(f"--- Applying settings from manifest to world: {self.world_name} ---")

        try:
            # 1. Update server.properties
            settings_to_apply = self.world_manifest.get("server_properties", {})
            properties_path = self.world_directory / "server.properties"

            properties = {}
            if properties_path.exists():
                with open(properties_path, 'r') as f:
                    for line in f:
                        if '=' in line and not line.startswith('#'):
                            key, value = line.strip().split('=', 1)
                            properties[key] = value

            for key, value in settings_to_apply.items():
                properties[key] = str(value)

            with open(properties_path, 'w') as f:
                f.write("# Minecraft server properties (managed by mc-shell)\n")
                for key, value in properties.items():
                    f.write(f"{key}={value}\n")

            # 2. Update FruitJuice config
            fj_data = self.world_manifest.get('FruitJuice')
            if fj_data:
                fj_config_path = self.world_directory / "plugins" / "FruitJuice" / "config.yml"
                fj_config_path.parent.mkdir(parents=True, exist_ok=True)
                with fj_config_path.open('w') as file:
                    yaml.dump(fj_data, file, sort_keys=False)

            # 3. Update Paper global settings
            paper_settings = self.world_manifest.get('paper', {})
            if paper_settings:
                paper_config_path = self.world_directory / 'config' / 'paper-global.yml'
                if not paper_config_path.exists():
                    paper_config_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(paper_config_path, 'w') as f:
                        f.write(MC_PAPER_GLOBAL_TEMPLATE.read_text())

                with open(paper_config_path, 'r') as f:
                    paper_config = yaml.safe_load(f) or {}

                def merge_dicts(source, destination):
                    for key, value in source.items():
                        if isinstance(value, dict) and key in destination and isinstance(destination[key], dict):
                            merge_dicts(value, destination[key])
                        else:
                            destination[key] = value
                    return destination

                updated_config = merge_dicts(paper_settings, paper_config)
                with open(paper_config_path, 'w') as f:
                    yaml.dump(updated_config, f, default_flow_style=False, sort_keys=False)

            print("--- Manifest settings applied successfully. ---")

        except Exception as e:
            print(f"Error applying settings: {e}")

    def _execute_server(self):
        """
        The main execution function. Starts the Paper server using the local JRE
        and logs its output in real-time.
        """
        command = [
            str(MC_JRE_PATH),
            '-Xms2G', '-Xmx2G',
            '-jar', str(self.jar_path),
            'nogui'
        ]

        print(f"Starting Paper server for world '{self.world_name}'...")
        try:
            self.process = pexpect.spawn(
                ' '.join(command),
                cwd=str(self.world_directory),
                encoding='utf-8'
            )

            while self.process.isalive():
                try:
                    index = self.process.expect(['\r\n', pexpect.TIMEOUT, pexpect.EOF], timeout=0.1)
                    if index == 0:
                        line = self.process.before
                        # Filter noisy logs
                        if "Thread RCON Client" in line or "FruitJuice" in line:
                            continue
                        if line:
                            sys.stdout.write(f"[{self.world_name}] {line}\n")
                            sys.stdout.flush()
                except pexpect.exceptions.TIMEOUT:
                    continue
                except pexpect.exceptions.EOF:
                    break

        except Exception as e:
            print(f"An error occurred while launching the Paper server: {e}")
        finally:
            print(f"\nPaper server process for world '{self.world_name}' has terminated.")
            if self.process and self.process.isalive():
                self.process.close(force=True)
            self.process = None

    def start(self):
        """
        Ensures the environment is ready and starts the server in a background thread.
        Handles JRE acquisition and first-time configuration automatically.
        """
        # 1. Ensure the managed JRE is present
        downloader = PaperDownloader(MC_WORLDS_BASE_DIR / 'server-jars')
        if not downloader.ensure_jre():
            print("Abort: Managed JRE 21 could not be initialized.")
            return

        # 2. Check if the world needs initialization (config generation)
        if not (self.world_directory / "server.properties").exists():
            print("First-time setup: Initializing server to generate configuration files...")
            try:
                # Run with --initSettings to generate files, then exit
                subprocess.run(
                    [str(MC_JRE_PATH), "-jar", str(self.jar_path), "--initSettings"],
                    cwd=self.world_directory,
                    check=True,
                    capture_output=True
                )
            except subprocess.CalledProcessError as e:
                print(f"Error during initialization: {e.stderr.decode()}")
                return

        # 3. Always apply manifest settings before starting to ensure ports/passwords are synced
        self.apply_manifest_settings()

        if self.is_alive():
            print(f"Server for world '{self.world_name}' is already running.")
            return

        # 4. Start the server management thread
        self.thread = threading.Thread(target=self._execute_server, daemon=True)
        self.thread.start()

        print("Waiting for server to initialize (this may take up to 20 seconds)...")
        time.sleep(15)

        if not self.is_alive():
            print(f"Error: Server for '{self.world_name}' failed to stay alive. Check logs above.")

    def stop(self):
        """Stops the running Paper server gracefully."""
        if not self.is_alive():
            print(f"Server for '{self.world_name}' is not running.")
            return

        print(f"Sending 'stop' command to Paper server for '{self.world_name}'...")
        try:
            self.process.sendline('stop')
            self.thread.join(timeout=30)
        except Exception as e:
            print(f"Graceful shutdown failed: {e}. Forcing termination.")
            if self.process:
                self.process.terminate(force=True)

    def is_alive(self) -> bool:
        """Checks if the server process is currently running."""
        return self.process is not None and self.process.isalive()