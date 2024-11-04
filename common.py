import socket


PIECE_SIZE = 512
CODE = 'utf-8'
BUFFER_SIZE = 1024
LISTEN_NUM = 10


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

