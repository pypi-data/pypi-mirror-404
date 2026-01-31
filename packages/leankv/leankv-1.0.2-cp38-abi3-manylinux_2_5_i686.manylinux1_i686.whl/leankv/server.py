import argparse
from typing import Optional, List
import logging, asyncio

from . import _leankv

# Configure Logging
logging.basicConfig(level=logging.INFO, format='[LeanKV] %(message)s')
logger = logging.getLogger("LeanKV")

class RespProtocol:
    """
    Minimal implementation of Redis Serialization Protocol (RESP).
    """
    def encode_simple_string(self, s: str) -> bytes:
        return f"+{s}\r\n".encode()

    def encode_error(self, msg: str) -> bytes:
        return f"-ERR {msg}\r\n".encode()

    def encode_integer(self, i: int) -> bytes:
        return f":{i}\r\n".encode()

    def encode_bulk_string(self, s: Optional[bytes]) -> bytes:
        if s is None:
            return b"$-1\r\n"
        return f"${len(s)}\r\n".encode() + s + b"\r\n"

    def encode_array(self, items: List[bytes]) -> bytes:
        if items is None:
            return b"*-1\r\n"
        res = f"*{len(items)}\r\n".encode()
        for item in items:
            res += item
        return res

class LeanKVRedisHandler:
    def __init__(self, db_path: str):
        # We access the raw Rust object directly to avoid Pickling.
        # Redis expects raw bytes, not Python objects.
        self.db = _leankv.LeanKV(db_path)
        self.proto = RespProtocol()
        self.commands = {
            'PING': self.cmd_ping,
            'SET': self.cmd_set,
            'GET': self.cmd_get,
            'DEL': self.cmd_del,
            'KEYS': self.cmd_keys,
            'DBSIZE': self.cmd_dbsize,
            'SAVE': self.cmd_save,
            'BGSAVE': self.cmd_save, # We don't actually fork, but we implement the hook
            'VACUUM': self.cmd_vacuum, # Custom command
            'FLUSHDB': self.cmd_flush,
            'QUIT': self.cmd_quit
        }

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        addr = writer.get_extra_info('peername')
        logger.info(f"Connection from {addr}")

        try:
            while True:
                # 1. Parse RESP Command
                try:
                    data = await self._read_resp_command(reader)
                except asyncio.IncompleteReadError:
                    break
                
                if not data:
                    break

                # 2. Execute Command
                cmd_name = data[0].decode('utf-8', errors='ignore').upper()
                args = data[1:]
                
                if cmd_name in self.commands:
                    try:
                        response = self.commands[cmd_name](args)
                    except Exception as e:
                        logger.error(f"Command Error {cmd_name}: {e}")
                        response = self.proto.encode_error(str(e))
                else:
                    response = self.proto.encode_error(f"unknown command '{cmd_name}'")

                # 3. Write Response
                writer.write(response)
                await writer.drain()

                if cmd_name == 'QUIT':
                    break

        except ConnectionResetError:
            pass
        finally:
            writer.close()
            await writer.wait_closed()
            logger.info(f"Connection closed {addr}")

    async def _read_resp_command(self, reader: asyncio.StreamReader) -> Optional[List[bytes]]:
        """
        Parses a RESP Array from the stream.
        Clients send commands as: *<num_args>\r\n$<len>\r\n<arg>\r\n...
        """
        line = await reader.readline()
        if not line:
            return None
        
        # Redis commands are always Arrays (*)
        if not line.startswith(b'*'):
            # Handle inline commands (simple telnet style)
            return line.strip().split()

        try:
            num_args = int(line[1:].strip())
        except ValueError:
            raise Exception("Invalid protocol format")

        args = []
        for _ in range(num_args):
            line = await reader.readline()
            if not line.startswith(b'$'):
                raise Exception("Expected bulk string")
            
            str_len = int(line[1:].strip())
            if str_len == -1:
                args.append(None)
            else:
                arg_data = await reader.readexactly(str_len)
                await reader.readexactly(2) # Consume trailing \r\n
                args.append(arg_data)
        
        return args

    # --- Command Implementations ---

    def cmd_ping(self, args):
        if args:
            return self.proto.encode_simple_string(args[0].decode())
        return self.proto.encode_simple_string("PONG")

    def cmd_set(self, args):
        if len(args) < 2:
            return self.proto.encode_error("wrong number of arguments for 'set' command")
        
        # Redis Keys are bytes, but LeanKV currently expects String keys.
        # We must decode key to UTF-8. Value stays as bytes.
        try:
            key = args[0].decode('utf-8')
        except UnicodeDecodeError:
            return self.proto.encode_error("LeanKV only supports UTF-8 keys")

        val = args[1]
        
        # Handle 'SET key value EX 10' (Ignore TTL for now, just simple SET)
        # To support TTL, Rust struct needs to be updated.
        self.db.set_bytes(key, val)
        return self.proto.encode_simple_string("OK")

    def cmd_get(self, args):
        if len(args) != 1:
            return self.proto.encode_error("wrong number of arguments for 'get' command")
        
        try:
            key = args[0].decode('utf-8')
        except UnicodeDecodeError:
            return self.proto.encode_error("LeanKV only supports UTF-8 keys")

        # get_bytes returns `bytes` or `None`
        val = self.db.get_bytes(key) 
        return self.proto.encode_bulk_string(val)

    def cmd_del(self, args):
        if len(args) < 1:
            return self.proto.encode_error("wrong number of arguments for 'del' command")
        
        count = 0
        for arg in args:
            try:
                key = arg.decode('utf-8')
                if self.db.delete(key):
                    count += 1
            except:
                pass
        return self.proto.encode_integer(count)

    def cmd_keys(self, args):
        # Warning: This implementation fetches ALL keys. 
        # In Redis, KEYS pattern is supported. Here we assume KEYS *
        # LeanKV currently only exposes listing all keys.
        
        # Get list of strings from Rust
        all_keys = self.db.keys() 
        
        # Filter if pattern provided (basic implementation)
        pattern = args[0].decode('utf-8') if args else "*"
        
        # Simple glob-like filter
        import fnmatch
        matches = [k.encode() for k in all_keys if fnmatch.fnmatch(k, pattern)]
        
        # Encode as Array of Bulk Strings
        encoded_matches = [self.proto.encode_bulk_string(m) for m in matches]
        return self.proto.encode_array(encoded_matches)

    def cmd_dbsize(self, args):
        return self.proto.encode_integer(self.db.len())

    def cmd_save(self, args):
        self.db.persist()
        return self.proto.encode_simple_string("OK")

    def cmd_vacuum(self, args):
        self.db.vacuum()
        return self.proto.encode_simple_string("OK")
    
    def cmd_flush(self, args):
        # Naive flush: iterate and delete. 
        # Ideally, Rust core should have a truncate method.
        keys = self.db.keys()
        for k in keys:
            self.db.delete(k)
        self.db.persist()
        return self.proto.encode_simple_string("OK")

    def cmd_quit(self, args):
        return self.proto.encode_simple_string("OK")

async def run_server(host, port, db_path):
    """The async logic to start the server."""
    handler = LeanKVRedisHandler(db_path)
    server = await asyncio.start_server(
        handler.handle_client, host, port
    )

    addr = server.sockets[0].getsockname()
    logger.info(f"⚡ LeanKV Redis-Compatible Server running on {addr}")
    logger.info(f"📂 Storage path: {db_path}")

    async with server:
        await server.serve_forever()
    
def main():
    """The synchronous entry point for the CLI."""
    parser = argparse.ArgumentParser(description="LeanKV Redis Interface")
    parser.add_argument("--port", type=int, default=6379, help="Port to listen on")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--dir", type=str, default="./redis_data", help="Data directory")
    
    args = parser.parse_args()
    
    try:
        # This properly starts the event loop
        asyncio.run(run_server(args.host, args.port, args.dir))
    except KeyboardInterrupt:
        logger.info("Shutting down...")

if __name__ == '__main__':
    main()