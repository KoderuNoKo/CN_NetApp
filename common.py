import socket
import hashlib
import json


PIECE_SIZE = 2**19 # 512KB
CODE = 'utf-8'
BUFFER_SIZE = 1024
LISTEN_NUM = 10
PORT_IPC_NODE = 44444


def get_host_default_interface_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
       s.connect(('1.1.1.1', 80))    # init a connection to obtain an socket from the OS
       ip = s.getsockname()[0]      # retrieve the IP part from the socket
    except Exception:
       ip = '127.0.0.1'     # NOTE: change to machine ipaddress manually when run
    finally:
       s.close()
    return ip

 
def hash_info(metainfo: dict) -> str:
   metainfo_str = json.dumps(metainfo)
   return hashlib.sha1(metainfo_str.encode(CODE)).hexdigest()


def parse_raw_msg(msg_raw: bytes) -> dict:
   """Parse the incomming raw bytes into a dict"""
   print('Parsing message: {}'.format(msg_raw.decode(CODE)))
   return json.loads(msg_raw.decode(CODE))


def create_raw_msg(msg: dict) -> bytes:
   """translate a dict into raw bytes"""
   return json.dumps(msg).encode(CODE)