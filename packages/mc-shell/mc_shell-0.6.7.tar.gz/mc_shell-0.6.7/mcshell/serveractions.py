from mcshell.mcactions_base import MCActionsBase
from mcshell.constants import Vec3
from blockapily import mced_block
import time
import re
from typing import Union

class ServerActions(MCActionsBase):
    """
    Blocks for controlling server state, game rules, and global settings.
    Exposes commands like /time, /weather, /gamemode, and /gamerule.
    """
    def __init__(self, mc_player_instance, delay_between_blocks=0):
        super().__init__(mc_player_instance, delay_between_blocks)

    def _run_command(self, cmd: str) -> str:
        """
        Helper to execute a raw server command using the MCClient's run method.
        This handles authentication and the RCON connection properly.

        Args:
            cmd (str): The full command string (e.g., "time set day").

        Returns:
            str: The response from the server, or None if failed.
        """
        # 1. Clean the command string
        if cmd.startswith("/"):
            cmd = cmd[1:]

        # 2. Normalize command syntax
        parts = cmd.split(' ', 1)
        verb = parts[0].replace('_', '-')
        if len(parts) > 1:
            cmd = f"{verb} {parts[1]}"
        else:
            cmd = verb

        print(f"Sending Server Command: {cmd}")

        try:
            # 3. Execute via RCON
            response = self.mcplayer.run(cmd)

            # 4. Handle Response
            if response:
                print(f"Server Response: {response}")
                return response

        except Exception as e:
            # 5. Error Handling
            print(f"Error executing command '{cmd}': {e}")
            pass

        if self.delay_between_blocks > 0:
            time.sleep(self.delay_between_blocks)

        return ""


    # --- Stage 1: Basic World Control ---

    @mced_block(
        label="Set Time to [time]",
        time_option={'label': 'Time'}
    )
    def server_set_time(self, time_option: 'Time'):
        """Sets the world time."""
        self._run_command(f"time set {time_option}")

    @mced_block(
        label="Set Weather to [weather]",
        weather_option={'label': 'Weather'}
    )
    def server_set_weather(self, weather_option: 'Weather'):
        """Sets the world weather."""
        self._run_command(f"weather {weather_option}")

    @mced_block(
        label="Set Difficulty to [difficulty]",
        difficulty_option={'label': 'Difficulty'}
    )
    def server_set_difficulty(self, difficulty_option: 'Difficulty'):
        """Sets the game difficulty."""
        self._run_command(f"difficulty {difficulty_option}")

    @mced_block(
        label="Set Gamemode [mode] for [target]",
        mode={'label': 'Mode'},
        target={'label': 'Target Player', 'shadow': '<shadow type="text"><field name="TEXT">SELF</field></shadow>'}
    )
    def server_set_gamemode(self, mode: 'Gamemode', target: str = "SELF"):
        """
        Sets the gamemode for a specific player.
        """
        if not target or target.strip().upper() == "SELF":
            target_name = self.mcplayer.name
        else:
            target_name = target

        self._run_command(f"gamemode {mode} {target_name}")

    # --- Stage 2: Game Rules ---

    @mced_block(
        label="Set Game Rule [rule] to [value]",
        rule={'label': 'Rule'},
        value={'label': 'Enabled', 'shadow': '<shadow type="logic_boolean"><field name="BOOL">TRUE</field></shadow>'}
    )
    def server_set_gamerule(self, rule: 'GameRule', value: bool):
        """Sets a boolean game rule."""
        str_value = "true" if value else "false"
        self._run_command(f"gamerule {rule} {str_value}")

    @mced_block(
        label="Set Integer Game Rule [rule] to [value]",
        rule={'label': 'Rule'},
        value={'label': 'Value'}
    )
    def server_set_integer_gamerule(self, rule: 'IntegerGameRule', value: int):
        """Sets a boolean game rule."""
        self._run_command(f"gamerule {rule} {value}")

    # --- Stage 3: Advanced Utility ---

    @mced_block(
        label="Locate [type] [target]",
        locate_type={'label': 'Type'},
        target={'label': 'Structure/Biome/POI', 'shadow': 'text'},
        output_type="3DVector",
        tooltip="Finds coordinates of nearest structure/biome/poi. Returns a Vec3."
    )
    def server_locate(self, locate_type: 'LocateType', target: Union['Structure','Biome','Poi']) -> Vec3:
        """
        Locates a structure, biome, or POI and returns its coordinates.
        Example response: "The nearest minecraft:mason is at [-389, ~, 268] (132 blocks away)"
        Failure response: 'Could not find a biome of type "minecraft:warped_forest" within reasonable distance'
        """
        # Execute command
        response = self._run_command(f"locate {locate_type} {target}")

        if not response:
            print("Locate failed: No response from server.")
            # Return current position as fallback to prevent crashes, but warn user.
            return self.mcplayer.position

        # Check for failure message
        if "Could not find" in response:
            print(f"Locate failed: {response}")
            # Return current position as fallback
            return self.mcplayer.position

        # Parse output using regex to find [x, y, z] pattern
        # Matches numbers or '~' inside square brackets: [-389, ~, 268]
        match = re.search(r'\[(.*?)\]', response)

        if match:
            # Extract content inside brackets: "-389, ~, 268"
            coords_str = match.group(1)
            # Split by comma
            parts = [p.strip() for p in coords_str.split(',')]

            if len(parts) >= 3:
                try:
                    # Parse X
                    x = float(parts[0])

                    # Parse Y (Handle tilde '~')
                    if parts[1] == '~':
                        # Use player's current Y if unknown, or default to world surface
                        y = self.mcplayer.position.y
                    else:
                        y = float(parts[1])

                    # Parse Z
                    z = float(parts[2])

                    return Vec3(x, y, z)
                except ValueError:
                    print(f"Locate failed: Could not parse coordinates from '{coords_str}'")

        print(f"Locate failed: Could not find coordinate pattern in response '{response}'")
        return self.mcplayer.position

    @mced_block(
        label="Clear Inventory of [target]",
        target={'label': 'Target Player', 'shadow': '<shadow type="text"><field name="TEXT">SELF</field></shadow>'}
    )
    def server_clear_inventory(self, target: str = "SELF"):
        """Clears items from a player's inventory."""
        if not target or target.strip().upper() == "SELF":
            target_name = self.mcplayer.name
        else:
            target_name = target
        self._run_command(f"clear {target_name}")

    @mced_block(
        label="Execute Command",
        command={'label': 'Command', 'shadow': 'text'},
        tooltip="Executes any arbitrary server command."
    )
    def server_execute_command(self, command: str):
        """Executes a custom command string."""
        self._run_command(command)