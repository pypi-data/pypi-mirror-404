import requests
import os
import platform
import tarfile
import zipfile
import io
import shutil
from pathlib import Path
from typing import Optional

from mcshell.constants import *

class PaperDownloader:
    """Handles downloading Paper server JARs and the required JRE from official APIs."""
    API_URL = "https://api.papermc.io/v2/projects/paper"

    def __init__(self, download_dir: Path):
        self.download_dir = download_dir
        self.download_dir.mkdir(parents=True, exist_ok=True)

    def ensure_jre(self, version: str = "21") -> bool:
        """Ensures a local JRE is present in the specified jre directory."""
        if MC_JRE_PATH.exists():
            return True

        print(f"JRE not found at {MC_JRE_PATH}. Downloading JRE {version}...")

        url = self._get_jre_download_url(version)
        if not url:
            print(f"Error: Could not determine JRE URL for {platform.system()} {platform.machine()}.")
            return False

        try:
            temp_archive = self.download_dir / "jre_archive.tmp"
            with requests.get(url, stream=True, timeout=60) as r:
                r.raise_for_status()
                with open(temp_archive, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)

            MC_JRE_DIR.mkdir(parents=True, exist_ok=True)
            temp_extract_path = MC_JRE_DIR / "tmp_extraction"
            temp_extract_path.mkdir(exist_ok=True)

            if url.endswith('.zip') or platform.system().lower() == 'windows':
                with zipfile.ZipFile(temp_archive, 'r') as zip_ref:
                    zip_ref.extractall(temp_extract_path)
            else:
                with tarfile.open(temp_archive, 'r:gz') as tar_ref:
                    tar_ref.extractall(temp_extract_path)

            inner_dir = next(temp_extract_path.iterdir())
            for item in inner_dir.iterdir():
                dest = MC_JRE_DIR / item.name
                if dest.exists():
                    if dest.is_dir(): shutil.rmtree(dest)
                    else: dest.unlink()
                shutil.move(str(item), str(MC_JRE_DIR))

            shutil.rmtree(temp_extract_path)
            temp_archive.unlink()

            if os.name != 'nt' and MC_JRE_PATH.exists():
                MC_JRE_PATH.chmod(MC_JRE_PATH.stat().st_mode | 0o111)

            return True
        except Exception as e:
            print(f"Error: JRE install failed: {e}")
            if MC_JRE_DIR.exists(): shutil.rmtree(MC_JRE_DIR)
            return False

    def _get_jre_download_url(self, version: str) -> Optional[str]:
        """Maps system platform and architecture to an Adoptium API download URL."""
        sys_os = platform.system().lower()
        if sys_os == 'darwin': sys_os = 'mac'
        arch = platform.machine().lower()
        if arch in ('x86_64', 'amd64'): arch = 'x64'
        elif arch in ('arm64', 'aarch64'): arch = 'aarch64'
        return f"https://api.adoptium.net/v3/binary/latest/{version}/ga/{sys_os}/{arch}/jre/hotspot/normal/eclipse"

    def get_jar_path(self, mc_version: str) -> Optional[Path]:
        """Returns local path to Paper JAR, downloading if missing."""
        build_info = self._get_latest_build_for_version(mc_version)
        if not build_info:
            return None

        # FIX: Use the mc_version passed into the function directly.
        # The build_info dict in v2 API results does not contain a 'version' key.
        project = build_info.get('project_id', 'paper')
        build_num = build_info.get('build')
        jar_name = build_info.get('downloads', {}).get('application', {}).get('name')

        if not jar_name:
            print("Error: JAR filename not found in API response.")
            return None

        jar_path = self.download_dir / jar_name
        if jar_path.exists():
            return jar_path

        # Construct the download URL using the verified mc_version string
        download_url = f"https://api.papermc.io/v2/projects/{project}/versions/{mc_version}/builds/{build_num}/downloads/{jar_name}"
        return self._download_jar(download_url, jar_path)

    def _get_latest_build_for_version(self, mc_version: str) -> Optional[dict]:
        """Fetches the latest build metadata for a given Minecraft version."""
        builds_url = f"{self.API_URL}/versions/{mc_version}/builds"
        try:
            response = requests.get(builds_url)
            response.raise_for_status()
            data = response.json()
            builds = data.get('builds', [])
            return builds[-1] if builds else None
        except Exception as e:
            print(f"Error: Could not fetch build info for version {mc_version}: {e}")
            return None

    def _download_jar(self, download_url: str, jar_path: Path) -> Optional[Path]:
        """Downloads the specified JAR file."""
        print(f"Downloading Paper JAR from: {download_url}")
        try:
            with requests.get(download_url, stream=True) as r:
                r.raise_for_status()
                with open(jar_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            return jar_path
        except Exception as e:
            print(f"Error: Failed to download JAR file. {e}")
            if jar_path.exists(): jar_path.unlink()
            return None

    def install_plugins(self, plugin_urls: list[str], world_plugins_dir: Path) -> list[str]:
        """Downloads and installs a list of plugins."""
        if not plugin_urls: return []
        world_plugins_dir.mkdir(exist_ok=True)
        successful_installs = []
        for url in plugin_urls:
            filename = url.split('/')[-1]
            dest = world_plugins_dir / filename
            if filename.endswith(".jar") and self._download_file(url, dest):
                successful_installs.append(filename)
            elif filename.endswith(".zip"):
                jar = self._download_and_extract_zip(url, world_plugins_dir)
                if jar: successful_installs.append(jar)
        return successful_installs

    def _download_file(self, url: str, destination: Path) -> bool:
        try:
            with requests.get(url, stream=True, timeout=30) as r:
                r.raise_for_status()
                with open(destination, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192): f.write(chunk)
            return True
        except: return False

    def _download_and_extract_zip(self, url: str, destination_dir: Path) -> Optional[str]:
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            with zipfile.ZipFile(io.BytesIO(response.content)) as thezip:
                for member in thezip.namelist():
                    if member.endswith('.jar') and ('paper' in member.lower() or 'bukkit' in member.lower()):
                        thezip.extract(member, path=destination_dir)
                        ext_path = destination_dir / member
                        final_path = destination_dir / Path(member).name
                        if ext_path != final_path: shutil.move(str(ext_path), str(final_path))
                        return final_path.name
            return None
        except: return None