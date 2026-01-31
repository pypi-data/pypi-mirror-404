from mcshell.mcplayer import MCPlayer
from mcshell.constants import *
import time
import numpy as np
import pickle
from typing import Optional

# Advanced Digital Geometry and Turtle
from mcshell.mcturtle import (
    DigitalTurtle,
    generate_metric_ball,
    generate_digital_plane_coordinates as generate_arithmetic_plane,
    generate_linear_path,
    DigitalSet
)

# Global turtle instance (needed by subclasses)
_GLOBAL_TURTLE = DigitalTurtle()

class MCActionsBase:
    """
    Base class for all Action groups.
    Handles shared utilities like block placement, entity ID mapping, and player resolution.
    """
    def __init__(self, mc_player_instance:MCPlayer, delay_between_blocks:float):
        self.mcplayer = mc_player_instance
        self.bukkit_to_entity_id_map = {}
        self._initialize_entity_id_map()
        self.delay_between_blocks = delay_between_blocks

    def _place_blocks_from_coords(self, coords_list, block_type_from_blockly,
                                  placement_offset_vec3=None):
        """
        Helper method to take a list of coordinates and a Blockly block type,
        parse the block type, and set the blocks in the world.
        """
        if not coords_list:
            print("No coordinates generated, nothing to place.")
            return

        # we use Bukkit IDs which are output in mc-ed
        minecraft_block_id = block_type_from_blockly

        offset_x, offset_y, offset_z = (0,0,0)
        if placement_offset_vec3: # If a Vec3 object is given for overall placement
            offset_x, offset_y, offset_z = int(placement_offset_vec3.x), int(placement_offset_vec3.y), int(placement_offset_vec3.z)

        for x, y, z in coords_list:

            final_x = x + offset_x
            final_y = y + offset_y
            final_z = z + offset_z
            self.mcplayer.pc.setBlock(int(final_x), int(final_y), int(final_z), minecraft_block_id)

            # Pause execution for a fraction of a second to create animation effects
            if self.delay_between_blocks > 0:
                time.sleep(self.delay_between_blocks)

    def _place_digital_set(self, dset: DigitalSet, block_type):
        """
        Helper to render a DigitalSet (mathematical shape) into the world.
        """
        if not dset: return
        coords = dset.to_list()
        self._place_blocks_from_coords(coords, block_type)

    def _initialize_entity_id_map(self):
        """Loads the mapping of Bukkit entity names to Integer IDs."""
        try:
            with MC_ENTITY_ID_MAP_PATH.open('rb') as f:
                self.bukkit_to_entity_id_map = pickle.load(f)
        except Exception:
            self.bukkit_to_entity_id_map = {}

    def _get_entity_id_from_bukkit_name(self, bukkit_enum_string: str) -> Optional[int]:
        """
        Converts a Bukkit enum string (e.g., 'WITHER_SKELETON') to its Minecraft numeric ID.
        """
        return self.bukkit_to_entity_id_map.get(bukkit_enum_string)

    def _get_player_by_name(self, player_name: str) -> MCPlayer:
        """
        Helper to resolve a string name to an MCPlayer object.

        Logic:
        1. If name is None or empty -> Return self (Current Player)
        2. If name is 'SELF' (case-insensitive) -> Return self (Current Player)
        3. If name matches self.name -> Return self
        4. Otherwise -> Create new MCPlayer instance for target
        """
        from mcshell.mcplayer import MCPlayer

        # Check for empty or special "SELF" keyword
        if not player_name or player_name.strip().upper() == "SELF":
            return self.mcplayer

        # Check for explicit self-name
        if player_name.lower() == self.mcplayer.name.lower():
            return self.mcplayer

        try:
            # Create a contextual peer using server arguments from our own player.
            target = MCPlayer(player_name, **self.mcplayer.server_args)
            return target
        except Exception:
            # Fallback to executor if connection fails
            return self.mcplayer

class Pickers:
    """Registry of custom picker options for blocks (Dropdown menus)."""
    Metric = [("Euclidean", "euclidean"), ("Manhattan", "manhattan"), ("Chebyshev", "chebyshev")]
    Direction = [("Forward", "forward"), ("Back", "back"), ("Up", "up"), ("Down", "down"), ("Left", "left"), ("Right", "right")]
    Axis = [("Yaw (Y)", "y"), ("Pitch (X)", "x"), ("Roll (Z)", "z")]
    Compass = [
        ("North (-Z)", "N"), ("South (+Z)", "S"),
        ("East (+X)", "E"), ("West (-X)", "W"),
        ("North-East", "NE"), ("North-West", "NW"),
        ("South-East", "SE"), ("South-West", "SW")]

    Time = [
        ("Day (1000)", "day"),
        ("Noon (6000)", "noon"),
        ("Sunset (12000)", "sunset"),
        ("Night (13000)", "night"),
        ("Midnight (18000)", "midnight"),
        ("Sunrise (23000)", "sunrise")
    ]

    Weather = [
        ("Clear", "clear"),
        ("Rain", "rain"),
        ("Thunder", "thunder")
    ]

    Difficulty = [
        ("Peaceful", "peaceful"),
        ("Easy", "easy"),
        ("Normal", "normal"),
        ("Hard", "hard")
    ]

    Gamemode = [
        ("Survival", "survival"),
        ("Creative", "creative"),
        ("Adventure", "adventure"),
        ("Spectator", "spectator")
    ]

    LocateType = [
        ("Structure", "structure"),
        ("Biome", "biome"),
        ("Point of Interest (POI)", "poi")
    ]

    # Structures (Minecraft 1.19+)
    Structures = [
        ("Ancient City", "ancient_city"),
        ("Bastion Remnant", "bastion_remnant"),
        ("Buried Treasure", "buried_treasure"),
        ("Desert Pyramid", "desert_pyramid"),
        ("End City", "end_city"),
        ("Fortress", "fortress"),
        ("Igloo", "igloo"),
        ("Jungle Pyramid", "jungle_pyramid"),
        ("Mansion", "mansion"),
        ("Mineshaft", "mineshaft"),
        ("Monument", "monument"),
        ("Nether Fossil", "nether_fossil"),
        ("Ocean Ruin", "ocean_ruin"),
        ("Pillager Outpost", "pillager_outpost"),
        ("Ruined Portal", "ruined_portal"),
        ("Shipwreck", "shipwreck"),
        ("Stronghold", "stronghold"),
        ("Swamp Hut", "swamp_hut"),
        ("Village", "village"),
        ("Woodland Mansion", "mansion")
    ]

    # Biomes (Common selection)
    Biomes = [
        ("Badlands", "badlands"),
        ("Bamboo Jungle", "bamboo_jungle"),
        ("Beach", "beach"),
        ("Birch Forest", "birch_forest"),
        ("Cherry Grove", "cherry_grove"),
        ("Dark Forest", "dark_forest"),
        ("Deep Dark", "deep_dark"),
        ("Desert", "desert"),
        ("Dripstone Caves", "dripstone_caves"),
        ("End Highlands", "end_highlands"),
        ("End Midlands", "end_midlands"),
        ("Forest", "forest"),
        ("Frozen Peaks", "frozen_peaks"),
        ("Grove", "grove"),
        ("Ice Spikes", "ice_spikes"),
        ("Jagged Peaks", "jagged_peaks"),
        ("Jungle", "jungle"),
        ("Lush Caves", "lush_caves"),
        ("Mangrove Swamp", "mangrove_swamp"),
        ("Meadow", "meadow"),
        ("Mushroom Fields", "mushroom_fields"),
        ("Nether Wastes", "nether_wastes"),
        ("Ocean", "ocean"),
        ("Plains", "plains"),
        ("River", "river"),
        ("Savanna", "savanna"),
        ("Snowy Beach", "snowy_beach"),
        ("Snowy Plains", "snowy_plains"),
        ("Snowy Taiga", "snowy_taiga"),
        ("Soul Sand Valley", "soul_sand_valley"),
        ("Stony Peaks", "stony_peaks"),
        ("Swamp", "swamp"),
        ("Taiga", "taiga"),
        ("The End", "the_end"),
        ("The Void", "the_void"),
        ("Warm Ocean", "warm_ocean"),
        ("Warped Forest", "warped_forest")
    ]

    # Points of Interest (Villager jobs + others)
    Poi = [
        ("Armorer", "armorer"),
        ("Butcher", "butcher"),
        ("Cartographer", "cartographer"),
        ("Cleric", "cleric"),
        ("Farmer", "farmer"),
        ("Fisherman", "fisherman"),
        ("Fletcher", "fletcher"),
        ("Leatherworker", "leatherworker"),
        ("Librarian", "librarian"),
        ("Mason", "mason"),
        ("Shepherd", "shepherd"),
        ("Toolsmith", "toolsmith"),
        ("Weaponsmith", "weaponsmith"),
        ("Beehive", "beehive"),
        ("Bee Nest", "bee_nest"),
        ("End Portal", "end_portal"),
        ("Home", "home"),
        ("Lightning Rod", "lightning_rod"),
        ("Lodestone", "lodestone"),
        ("Meeting", "meeting"),
        ("Nether Portal", "nether_portal")
    ]

    # Boolean GameRules (True/False) - Snake Case for 1.21.11+
    GameRule = [
        ("Advance Time", "advance_time"),
        ("Advance Weather", "advance_weather"),
        ("Allow Entering Nether", "allow_entering_nether_using_portals"),
        ("Block Drops", "block_drops"),
        ("Block Explosion Drop Decay", "block_explosion_drop_decay"),
        ("Command Block Output", "command_block_output"),
        ("Command Blocks Work", "command_blocks_work"),
        ("Disable Elytra Movement Check", "elytra_movement_check"),
        ("Disable Raids", "raids"),
        ("Do Entity Drops", "entity_drops"),
        ("Drowning Damage", "drowning_damage"),
        ("Ender Pearls Vanish On Death", "ender_pearls_vanish_on_death"),
        ("Fall Damage", "fall_damage"),
        ("Fire Damage", "fire_damage"),
        ("Forgive Dead Players", "forgive_dead_players"),
        ("Freeze Damage", "freeze_damage"),
        ("Global Sound Events", "global_sound_events"),
        ("Immediate Respawn", "immediate_respawn"),
        ("Keep Inventory", "keep_inventory"),
        ("Lava Source Conversion", "lava_source_conversion"),
        ("Limit Crafting", "limited_crafting"),
        ("Locator Bar", "locator_bar"),
        ("Log Admin Commands", "log_admin_commands"),
        ("Mob Drops", "mob_drops"),
        ("Mob Explosion Drop Decay", "mob_explosion_drop_decay"),
        ("Mob Griefing", "mob_griefing"),
        ("Natural Health Regeneration", "natural_health_regeneration"),
        ("Player Movement Check", "player_movement_check"),
        ("Projectiles Can Break Blocks", "projectiles_can_break_blocks"),
        ("PVP", "pvp"),
        ("Reduced Debug Info", "reduced_debug_info"),
        ("Send Command Feedback", "send_command_feedback"),
        ("Show Advancement Messages", "show_advancement_messages"),
        ("Show Death Messages", "show_death_messages"),
        ("Spawn Mobs", "spawn_mobs"),
        ("Spawn Monsters", "spawn_monsters"),
        ("Spawn Patrols", "spawn_patrols"),
        ("Spawn Phantoms", "spawn_phantoms"),
        ("Spawn Wandering Traders", "spawn_wandering_traders"),
        ("Spawn Wardens", "spawn_wardens"),
        ("Spawner Blocks Work", "spawner_blocks_work"),
        ("Spectators Generate Chunks", "spectators_generate_chunks"),
        ("Spread Vines", "spread_vines"),
        ("TNT Explodes", "tnt_explodes"),
        ("TNT Explosion Drop Decay", "tnt_explosion_drop_decay"),
        ("Universal Anger", "universal_anger"),
        ("Water Source Conversion", "water_source_conversion")
    ]

    # Integer GameRules (Numeric Inputs) - Snake Case for 1.21.11+
    IntegerGameRule = [
        ("Fire Spread Radius", "fire_spread_radius_around_player"),
        ("Max Block Modifications", "max_block_modifications"),
        ("Max Command Forks", "max_command_forks"),
        ("Max Command Sequence Length", "max_command_sequence_length"),
        ("Max Entity Cramming", "max_entity_cramming"),
        ("Max Snow Accumulation Height", "max_snow_accumulation_height"),
        ("Players Nether Portal Creative Delay", "players_nether_portal_creative_delay"),
        ("Players Nether Portal Default Delay", "players_nether_portal_default_delay"),
        ("Players Sleeping Percentage", "players_sleeping_percentage"),
        ("Random Tick Speed", "random_tick_speed"),
        ("Respawn Radius", "respawn_radius")
    ]