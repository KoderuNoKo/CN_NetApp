import argparse
import socket
import common


PORT_IPC_NODE = 12345

def submit_info(args):
    cli_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    cli_sock.connect(('localhost', PORT_IPC_NODE))
    cli_sock.sendall(f'submit_info {args.serverip} {args.serverport}'.encode(common.CODE))
    
    node_rep = cli_sock.recv(1024).decode(common.CODE)
    print(node_rep)
    cli_sock.close()
    return

def get_list(args):
    cli_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    cli_sock.connect(('localhost', PORT_IPC_NODE))
    cli_sock.sendall(f'get_list {args.serverip} {args.serverport}'.encode(common.CODE))
    
    node_rep = cli_sock.recv(1024).decode(common.CODE)
    print(node_rep)
    cli_sock.close()
    return

    
class NodeCLI:
    """"""
    def __init__(self):
        self.parser = argparse.ArgumentParser(prog='NodeCLI', 
                                              description='CLI for interacting with Node')
        self.add_subparsers()
        
    
    def add_subparsers(self):
        self.parser.add_argument('--func')
        self.parser.add_argument('--serverip')
        self.parser.add_argument('--serverport', type=int)
        
        
    def run(self):
        args = self.parser.parse_args()
        f = globals()[args.func]
        f(args)
        

if __name__ == '__main__':
    cli = NodeCLI()
    cli.run()