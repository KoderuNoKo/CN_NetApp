import socket
import hashlib
import json


PIECE_SIZE = 2**19 # 512KB
CODE = 'utf-8'
BUFFER_SIZE = 1024
LISTEN_NUM = 10
PORT_IPC_NODE = 12345


def get_host_default_interface_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
       s.connect(('1.1.1.1', 80))    # init a connection to obtain an socket from the OS
       ip = s.getsockname()[0]      # retrieve the IP part from the socket
    except Exception:
       ip = '127.0.0.1'     # default local loopback address
    finally:
       s.close()
    return ip

 
def hash_info(metainfo: dict) -> str:
   metainfo_str = json.dumps(metainfo)
   return hashlib.sha1(metainfo_str.encode(CODE)).hexdigest()