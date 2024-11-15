import argparse
import socket
import common


PORT_IPC_NODE = 12345

def submit_info():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as cli_sock:
        cli_sock.connect(('localhost', PORT_IPC_NODE))
        cli_sock.sendall('submit_info'.encode(common.CODE))
        cli_sock.close()


def get_list():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as cli_sock:
        cli_sock.connect(('localhost', PORT_IPC_NODE))
        cli_sock.sendall(f'get_list test.txt'.encode(common.CODE))
        cli_sock.close()

    
class NodeCLI:
    """"""
    def __init__(self):
        self.parser = argparse.ArgumentParser(prog='NodeCLI', 
                                              description='CLI for interacting with Node')
        self.add_subparsers()
        
    
    def add_subparsers(self):
        self.parser.add_argument('--func')
        
        
    def run(self):
        args = self.parser.parse_args()
        f = globals()[args.func]
        f()
        

if __name__ == '__main__':
    cli = NodeCLI()
    cli.run()