from mcshell.mcplayer import MCPlayer
# Use new file for base class import
from mcshell.mcactions_base import MCActionsBase
from mcshell.constants import Vec3
from blockapily import mced_block

class EventActions(MCActionsBase):
    """
    Consolidated class for all Event-driven blocks.
    """
    def __init__(self, mc_player_instance, delay_between_blocks=0):
        super().__init__(mc_player_instance, delay_between_blocks)

    @mced_block(
        label="Clear All Events",
        tooltip="Clears the queue of old chat, hit, and projectile events. Useful to call before waiting."
    )
    def clear_events(self):
        """
        Directly calls the player's clear_events method to flush the buffer.
        """
        self.mcplayer.clear_events()

    @mced_block(
        label="Wait for Sword Strike from [player]",
        player_name={'label': 'Player', 'shadow': 'text'},
        output_type="3DVector",
        tooltip="Pauses execution until the specified player hits a block with a sword. Returns the block's position."
    )
    def wait_for_sword_strike_by_name(self, player_name: str = "SELF") -> Vec3:
        """
        Resolves the target player and waits for them to strike a block.
        """
        target = self._get_player_by_name(player_name)
        pos = target.get_sword_hit_position()
        return Vec3(pos.x, pos.y, pos.z)

    @mced_block(
        label="Wait for Chat from [player]",
        player_name={'label': 'Player', 'shadow': 'text'},
        output_type="String",
        tooltip="Pauses execution until the specified player types a message in chat. Returns the message text."
    )
    def wait_for_chat_by_name(self, player_name: str = "SELF") -> str:
        """
        Resolves the target player and waits for a chat message from them.
        """
        target = self._get_player_by_name(player_name)
        target_id = target.pc.getPlayerEntityId(target.name)
        return target.wait_for_chat_post(entity_id=target_id)

    @mced_block(
        label="Wait for Arrow Hit from [player]",
        player_name={'label': 'Player', 'shadow': 'text'},
        output_type="3DVector",
        tooltip="Pauses execution until an arrow (or projectile) hits a block. Returns the hit position."
    )
    def wait_for_projectile_by_name(self, player_name: str = "SELF") -> Vec3:
        """
        Resolves the target player and waits for a projectile hit event.
        """
        target = self._get_player_by_name(player_name)
        vec = target.wait_for_projectile_hit()
        return Vec3(vec.x, vec.y, vec.z)