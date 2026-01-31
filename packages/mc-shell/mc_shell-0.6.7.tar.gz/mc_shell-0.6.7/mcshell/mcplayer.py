from mcshell.mcclient import MCClient
from mcshell.constants import *
import time
import numpy as np
import re
import json
import asyncio

# Define a tolerance for floating-point comparisons near zero
DEFAULT_TOLERANCE = 1e-9

class MCPlayer(MCClient):
    def __init__(self, name, host=MC_SERVER_HOST, port=MC_SERVER_PORT,rcon_port=MC_RCON_PORT, fj_port=FJ_PLUGIN_PORT, password=None,  cancel_event=None):
        super().__init__(host, port, rcon_port, fj_port,password)
        self.name = name
        self.state = {}
        self.cancel_event = cancel_event

    def get_data(self,data_path):
        _args = ['get','entity',f'@p[name={self.name}]',data_path]
        return self.data(*_args)

    def build(self):
        for _data_path in DATA_PATHS:
            if _data_path in FORBIDDEN_DATA_PATHS:
                continue
            _data = self.get_data(_data_path)
            self.state[_data_path] = _data
        _recipe_book_data = {}
        for _data_path in RECIPE_BOOK_DATA_PATHS:
            if _data_path in FORBIDDEN_DATA_PATHS:
                continue
            _data = self.get_data(f"recipeBook.{_data_path}")
            _recipe_book_data[_data_path] = _data
        self.state['recipeBook'] = _recipe_book_data
        return self

    # broken due to truncated server responses
    async def get_data_async(self,data_path):
        _args = f"entity @p[name={self.name}] {data_path}".split()
        await self.data_async(data_path,self.state,'get',*_args)

    async def build_player_data_async(self):
        for _data_path in DATA_PATHS:
            if _data_path in FORBIDDEN_DATA_PATHS:
                continue
            await self.get_data_async(_data_path)
        for _data_path in RECIPE_BOOK_DATA_PATHS:
            if _data_path in FORBIDDEN_DATA_PATHS:
                continue
            _data = await self.get_data_async(f"recipeBook.{_data_path}")

    def build_async(self):
        asyncio.run(self.build_player_data_async())
        return self

    def set_direction(self,dir:Vec3):
        return self.pc.player.setDirection(*dir)

    @property
    def pc(self):
        return self.py_client(self.name)

    @property
    def position(self):
        return Vec3(*self.pc.player.getPos())

    @property
    def tile_position(self):
        return Vec3(*self.pc.player.getTilePos())

    @property
    def direction(self):
        # note the cast from pyncraft.vec3.Vec3 to mcshell.Vec3.Vec3
        return Vec3(*self.pc.player.getDirection())

    @property
    def here(self):
        return Vec3(*self.get_sword_hit_position())

    @property
    def compass_direction(self):
        return self._get_compass_direction(self.direction.to_tuple())

    def set_compass_direction(self,dir:str):
        compass_vectors = {
            'N': np.array([0., 0., -1.]),
            'NE': np.array([0.7071, 0., -0.7071]),  # sqrt(2)/2
            'E': np.array([1., 0., 0.]),
            'SE': np.array([0.7071, 0., 0.7071]),
            'S': np.array([0., 0., 1.]),
            'SW': np.array([-0.7071, 0., 0.7071]),
            'W': np.array([-1., 0., 0.]),
            'NW': np.array([-0.7071, 0., -0.7071]),
        }
        _vec = compass_vectors.get(dir,[0., 0., -1])
        return self.pc.player.setDirection(*compass_vectors.get(dir,[0, 0, -1]))

    def set_position(self, pos:Vec3):
        return self.pc.player.setPos(*pos)

    # --- New Methods for Event Actions ---

    def clear_events(self):
        """Clears all queued events on the server for this client."""
        self.pc.events.clearAll()

    def get_sword_hit_position(self):
        '''
            The following sword hits will all be detected:
            DIAMOND_SWORD,
            GOLDEN_SWORD,
            IRON_SWORD,
            STONE_SWORD,
            WOODEN_SWORD
        '''
        print('Waiting for a sword strike...')
        while True:

            if self.cancel_event and self.cancel_event.isSet():
                raise PowerCancelledException

            _hits = self.pc.events.pollBlockHits()
            if _hits:
                _hit = _hits[0]
                # We must check that our player did the strike!
                if not _hit.entityId == self.pc.playerId:
                    continue
                _v0 = _hit.pos.clone()

                return _hit.pos.clone()

            time.sleep(0.1)

    def wait_for_chat_post(self, entity_id=None):
        """
        Polls for chat posts. If entity_id is provided, filters for that player.
        Returns the message string.
        """
        print('Waiting for chat post...')
        while True:
            if self.cancel_event and self.cancel_event.isSet():
                raise PowerCancelledException

            posts = self.pc.events.pollChatPosts()
            if posts:
                for post in posts:
                    if entity_id is None or post.entityId == entity_id:
                        return post.message

            time.sleep(0.1)

    def wait_for_projectile_hit(self):
        """
        Polls for projectile hits.
        Returns the Vec3 position of the hit.
        """
        print('Waiting for projectile hit...')
        while True:
            if self.cancel_event and self.cancel_event.isSet():
                raise PowerCancelledException

            hits = self.pc.events.pollProjectileHits()
            if hits:
                # Return the position of the first hit detected
                return hits[0].pos

            time.sleep(0.1)

    def _get_compass_direction(self,direction_vector: tuple[float, float, float]) -> str:
        """
        Determines the closest 8-point compass direction from a 3D direction vector.
        """
        # Define the 8 compass directions as normalized 2D vectors (x, z)
        # Note: In Minecraft, negative Z is North and positive X is East.
        compass_vectors = {
            'N':  np.array([0, -1]),
            'NE': np.array([0.7071, -0.7071]), # sqrt(2)/2
            'E':  np.array([1, 0]),
            'SE': np.array([0.7071, 0.7071]),
            'S':  np.array([0, 1]),
            'SW': np.array([-0.7071, 0.7071]),
            'W':  np.array([-1, 0]),
            'NW': np.array([-0.7071, -0.7071]),
        }

        # Extract x and z from the input vector
        try:
            x, _, z = direction_vector
        except (ValueError, TypeError):
            # Handle Vec3-like objects
            if hasattr(direction_vector, 'x') and hasattr(direction_vector, 'z'):
                x, z = direction_vector.x, direction_vector.z
            else:
                raise TypeError("Input must be a 3-component vector or have .x and .z attributes.")

        # Create a 2D vector for the horizontal direction
        player_xz_vector = np.array([x, z])

        # Normalize the player's direction vector to make it a unit vector
        norm = np.linalg.norm(player_xz_vector)
        if norm < 1e-9: # Handle case where player is looking straight up or down
            return 'N'  # Default to North if there's no horizontal component

        normalized_player_vector = player_xz_vector / norm

        max_dot_product = -1
        closest_direction = 'N'

        for direction, compass_vec in compass_vectors.items():
            dot_product = np.dot(normalized_player_vector, compass_vec)
            if dot_product > max_dot_product:
                max_dot_product = dot_product
                closest_direction = direction

        return closest_direction