from mcshell.mcplayer import MCPlayer
# Use new file for base class import
from mcshell.mcactions_base import MCActionsBase
from blockapily import mced_block
from typing import Optional

class PyncraftActions(MCActionsBase):
    """
    Exposes direct pyncraft API methods as Blockly blocks with multi-player support.
    Uses minecraft.py as the definitive source of truth for available methods.
    """
    def __init__(self, mc_player_instance, delay_between_blocks=0):
        super().__init__(mc_player_instance, delay_between_blocks)

    # --- Player Control (CmdPlayer) ---

    @mced_block(
        label="Get Health for [player]",
        player_name={'label': 'Player', 'shadow': 'text'},
        output_type="Number"
    )
    def get_health_by_name(self, player_name: str = "SELF") -> float:
        """Returns the health of the specified player."""
        return self._get_player_by_name(player_name).pc.player.getHealth()

    @mced_block(
        label="Get Food Level for [player]",
        player_name={'label': 'Player', 'shadow': 'text'},
        output_type="Number"
    )
    def get_food_level_by_name(self, player_name: str = "SELF") -> int:
        """Returns the food level of the specified player."""
        return self._get_player_by_name(player_name).pc.player.getFoodLevel()

    @mced_block(
        label="Get Pitch for [player]",
        player_name={'label': 'Player', 'shadow': 'text'},
        output_type="Number"
    )
    def get_pitch_by_name(self, player_name: str = "SELF") -> float:
        """Returns the pitch (vertical rotation) of the specified player."""
        return self._get_player_by_name(player_name).pc.player.getPitch()

    @mced_block(
        label="Get Yaw for [player]",
        player_name={'label': 'Player', 'shadow': 'text'},
        output_type="Number"
    )
    def get_yaw_by_name(self, player_name: str = "SELF") -> float:
        """Returns the yaw (horizontal rotation) of the specified player."""
        return self._get_player_by_name(player_name).pc.player.getYaw()

    @mced_block(
        label="Get Rotation for [player]",
        player_name={'label': 'Player', 'shadow': 'text'},
        output_type="Number"
    )
    def get_rotation_by_name(self, player_name: str = "SELF") -> float:
        """Returns the rotation of the specified player."""
        return self._get_player_by_name(player_name).pc.player.getRotation()

    @mced_block(
        label="Get Position for [player]",
        player_name={'label': 'Player', 'shadow': 'text'},
        output_type="3DVector"
    )
    def get_position_by_name(self, player_name: str = "SELF"):
        """Returns the 3D vector position of the specified player."""
        return self._get_player_by_name(player_name).pc.player.getPos()

    @mced_block(
        label="Get Tile Position for [player]",
        player_name={'label': 'Player', 'shadow': 'text'},
        output_type="3DVector"
    )
    def get_tile_position_by_name(self, player_name: str = "SELF"):
        """Returns the integer tile position of the specified player."""
        return self._get_player_by_name(player_name).pc.player.getTilePos()

    @mced_block(
        label="Set Position for [player]",
        position={'label': 'To Position'},
        player_name={'label': 'Player', 'shadow': 'text'}
    )
    def set_position_by_name(self, position: 'Vec3', player_name: str = "SELF"):
        """Sets the position of the specified player."""
        self._get_player_by_name(player_name).pc.player.setPos(position.x, position.y, position.z)

    @mced_block(
        label="Set Tile Position for [player]",
        position={'label': 'To Tile Position'},
        player_name={'label': 'Player', 'shadow': 'text'}
    )
    def set_tile_position_by_name(self, position: 'Vec3', player_name: str = "SELF"):
        """Sets the tile position of the specified player."""
        self._get_player_by_name(player_name).pc.player.setTilePos(int(position.x), int(position.y), int(position.z))

    @mced_block(
        label="Set Rotation for [player]",
        yaw={'label': 'Yaw', 'shadow': '<shadow type="math_number"><field name="NUM">0</field></shadow>'},
        pitch={'label': 'Pitch', 'shadow': '<shadow type="math_number"><field name="NUM">0</field></shadow>'},
        player_name={'label': 'Player', 'shadow': 'text'}
    )
    def set_rotation_by_name(self, yaw: float, pitch: float, player_name: str = "SELF"):
        """Sets the rotation (yaw and pitch) of the specified player."""
        self._get_player_by_name(player_name).pc.player.setRotation(yaw, pitch)

    @mced_block(
        label="Set Direction for [player]",
        direction={'label': 'Direction Vector'},
        player_name={'label': 'Player', 'shadow': 'text'}
    )
    def set_direction_by_name(self, direction: 'Vec3', player_name: str = "SELF"):
        """Sets the direction the player is facing."""
        self._get_player_by_name(player_name).pc.player.setDirection(direction.x, direction.y, direction.z)

    @mced_block(
        label="Get Direction for [player]",
        player_name={'label': 'Player', 'shadow': 'text'},
        output_type="3DVector"
    )
    def get_direction_by_name(self, player_name: str = "SELF"):
        """Returns the direction vector the player is facing."""
        return self._get_player_by_name(player_name).pc.player.getDirection()

    @mced_block(
        label="Send Title to [player]",
        title={'label': 'Title', 'shadow': 'text'},
        subtitle={'label': 'Subtitle', 'shadow': 'text'},
        stay={'label': 'Stay (Ticks)', 'shadow': '<shadow type="math_number"><field name="NUM">70</field></shadow>'},
        player_name={'label': 'Player', 'shadow': 'text'}
    )
    def send_title_by_name(self, title: str = "", subtitle: str = "", stay: int = 70, player_name: str = "SELF"):
        """Sends a title and subtitle to the specified player's screen."""
        self._get_player_by_name(player_name).pc.player.sendTitle(title=title, subTitle=subtitle, stay=stay)

    # --- World Manipulation (Minecraft Class) ---

    @mced_block(
        label="Set Block",
        position={'label': 'At Position'},
        block_type={'label': 'Block Type'}
    )
    def set_block(self, position: 'Vec3', block_type: 'Block'):
        """Sets a block at the specified position."""
        self.mcplayer.pc.setBlock(int(position.x), int(position.y), int(position.z), block_type)

    @mced_block(
        label="Set Blocks",
        p1={'label': 'Position 1'},
        p2={'label': 'Position 2'},
        block_type={'label': 'Block Type'}
    )
    def set_blocks(self, p1: 'Vec3', p2: 'Vec3', block_type: 'Block'):
        """Sets a cuboid of blocks defined by two corners."""
        self.mcplayer.pc.setBlocks(int(p1.x), int(p1.y), int(p1.z), int(p2.x), int(p2.y), int(p2.z), block_type)

    @mced_block(
        label="Get Block",
        position={'label': 'At Position'},
        output_type="String"
    )
    def get_block(self, position: 'Vec3') -> str:
        """Returns the block type at the specified position."""
        return str(self.mcplayer.pc.getBlock(int(position.x), int(position.y), int(position.z)))

    @mced_block(
        label="Get Block With Data",
        position={'label': 'At Position'},
        output_type="String"
    )
    def get_block_with_data(self, position: 'Vec3') -> str:
        """Returns the block type and data at the specified position."""
        # Returns Block object, converting to string representation
        return str(self.mcplayer.pc.getBlockWithData(int(position.x), int(position.y), int(position.z)))

    @mced_block(
        label="Get Height",
        x={'label': 'X', 'shadow': '<shadow type="math_number"><field name="NUM">0</field></shadow>'},
        z={'label': 'Z', 'shadow': '<shadow type="math_number"><field name="NUM">0</field></shadow>'},
        output_type="Number"
    )
    def get_height(self, x: int, z: int) -> int:
        """Returns the height of the world (y-coordinate) at the given x and z coordinates."""
        return int(self.mcplayer.pc.getHeight(x, z))

    @mced_block(
        label="Get Player Entity IDs",
        output_type="Array"
    )
    def get_player_entity_ids(self) -> list:
        """Returns a list of entity IDs for all connected players."""
        return self.mcplayer.pc.getPlayerEntityIds()

    @mced_block(
        label="Get Player Entity ID",
        name={'label': 'Player Name', 'shadow': 'text'},
        output_type="Number"
    )
    def get_player_entity_id(self, name: str) -> int:
        """Returns the entity ID of the named player."""
        return self.mcplayer.pc.getPlayerEntityId(name)

    @mced_block(
        label="Spawn Entity",
        position={'label': 'At Position'},
        entity_id={'label': 'Entity ID', 'shadow': '<shadow type="math_number"><field name="NUM">1</field></shadow>'},
        output_type="Number"
    )
    def spawn_entity(self, position: 'Vec3', entity_id: int) -> int:
        """Spawns an entity at the specified position."""
        return self.mcplayer.pc.spawnEntity(int(position.x), int(position.y), int(position.z), entity_id)

    @mced_block(
        label="Create Explosion",
        position={'label': 'At Position'},
        power={'label': 'Power', 'shadow': '<shadow type="math_number"><field name="NUM">4</field></shadow>'}
    )
    def create_explosion(self, position: 'Vec3', power: int = 4):
        """Creates an explosion at the specified position."""
        self.mcplayer.pc.createExplosion(int(position.x), int(position.y), int(position.z), power)

    @mced_block(
        label="Set Sign Text",
        position={'label': 'At Position'},
        line1={'label': 'Line 1', 'shadow': 'text'},
        line2={'label': 'Line 2', 'shadow': 'text'},
        line3={'label': 'Line 3', 'shadow': 'text'},
        line4={'label': 'Line 4', 'shadow': 'text'},
        sign_type={'label': 'Sign Material (e.g. OAK)', 'shadow': 'text'},
        direction={'label': 'Direction (0-15)', 'shadow': '<shadow type="math_number"><field name="NUM">0</field></shadow>'}
    )
    def set_sign(self, position: 'Vec3', sign_type: str = "OAK", direction: int = 0,
                 line1: str = "", line2: str = "", line3: str = "", line4: str = ""):
        """Sets the text and type of a sign at the specified position."""
        self.mcplayer.pc.setSign(int(position.x), int(position.y), int(position.z),
                                 sign_type, direction, line1, line2, line3, line4)

    # TODO: what would it take to support this in FruitJuice?
    # @mced_block(
    #     label="Save Checkpoint",
    #     tooltip="Saves the current state of the world as a checkpoint."
    # )
    # def save_checkpoint(self):
    #     """Saves a checkpoint of the world."""
    #     self.mcplayer.pc.saveCheckpoint()
    #
    # @mced_block(
    #     label="Restore Checkpoint",
    #     tooltip="Restores the world to the last saved checkpoint."
    # )
    # def restore_checkpoint(self):
    #     """Restores the world to the last checkpoint."""
    #     self.mcplayer.pc.restoreCheckpoint()
