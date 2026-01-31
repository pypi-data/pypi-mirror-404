from mcshell.vendored.pyncraft.minecraft import Minecraft
from mcshell.constants import *

from functools import lru_cache
class _DEBUG:
    data = False

class MCClientException(Exception):
    pass

class MCClient:
    def __init__(self, host=MC_SERVER_HOST, port=MC_SERVER_PORT,rcon_port=MC_RCON_PORT, fj_port=FJ_PLUGIN_PORT, password='' ):

        self.host = host
        self.port = port
        self.rcon_port = rcon_port
        self.password = password
        self.fruit_juice_port  = fj_port


    @property
    def server_args(self):
        """For helping create fellow players on the same server"""
        return dict(zip(('host','port','rcon_port','fj_port','password'),(self.host,self.port,self.rcon_port,self.fruit_juice_port,self.password)))

    def run(self, *args):
        """
        Executes a command via RCON.

        Args:
            *args: Command components. Will be joined by spaces.
        """
        if not self.password:
            print('A password is required!')
            return

        if not args:
            raise MCClientException("Arguments required!")

        # Join arguments into a single command string
        full_command = " ".join(str(a) for a in args)

        with Client(self.host, self.rcon_port, passwd=self.password) as client:
            # client.run/command handles the basic send/recv cycle.
            # Note: Automatic reassembly of fragmented >4KB packets depends on the
            # underlying mcrcon library version.
            _response = client.run(full_command)

        return _response

    @lru_cache(maxsize=1)
    def py_client(self,player_name=None):
        player_name = '' if player_name is None else player_name
        return Minecraft.create(address=self.host,port=self.fruit_juice_port,playerName=player_name)

    def help(self,*args):
        if not self.password:
            print('A password is required!')
            return
        _help_cmd = 'minecraft:help'
        _response = self.run(_help_cmd,*args)
        return _response

    def data(self, operation, *args):
        if not self.password:
            print('A password is required!')
            return

        _response = self.run('data', operation, *args)
        try:
            _response = _response[_response.index(':') + 1:]
            return json.loads(self._fix_json(_response.strip()))
        except Exception as e:
            if _DEBUG.data:
                print(e)
                print(_response)
            return {}

    async def data_async(self,varname,namespace,operation,*args):
        if not self.password:
            print('A password is required!')
            return
        async with AioClient(host=self.host, port=self.rcon_port, password=self.password) as client:
            _response = await client.send_cmd(' '.join(['data',operation,*args]))
        if isinstance(_response,tuple):
            _response = _response[0]
            try:
                _response = _response[_response.index(':')+1:]
                namespace.update({varname:json.loads(self._fix_json(_response))})
            except Exception as e:
                if _DEBUG.data:
                    print(e)
                    print(_response)
        else:
            namespace.update({varname:_response})


    def _fix_nbt_values(self, _text):
        """Removes NBT suffixes and converts to appropriate Python types."""
        _text = re.sub(r"(\d+)b", r"False", _text)  # Bytes to booleans
        _text = re.sub(r"(\d+)s", r"\1", _text)  # Shorts to ints
        _text = re.sub(r"(\d+)l", r"\1", _text)  # Longs to ints
        _text = re.sub(r"(\d+(?:\.\d+)?)f", r"\1", _text)  # Floats to floats
        _text = re.sub(r"(\d+(?:\.\d+)?)d", r"\1", _text)  # Doubles to floats

        # Fix NBT arrays (e.g., [I; 1, 2, 3] to [1, 2, 3])
        _text = re.sub(r"\[[BISL];\s*([^\]]+)\]", r"[\1]", _text)
        return _text

    def _fix_json(self,json_string):
        _pattern = r"(?<!\")\b(\w+):\s*"
        _fixed_string = re.sub(_pattern, r'"\1":', json_string)
        _fixed_string = self._fix_nbt_values(_fixed_string)
        _fixed_string = re.sub(rf"\s*:({RE_NON_JSON_VALUE})", r':"\1"',_fixed_string)
        _fixed_string = _fixed_string.replace('False','false').replace('True','true').replace("\'","")
        _fixed_string = _fixed_string.replace('-false','false').replace('-true','true').replace("\'","")
        return _fixed_string
