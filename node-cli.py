import argparse
import socket
import common
import json



def submit_info(args):
    """submit the node info and seed the files in repo to the tracker"""
    command = {
        'func': 'submit_info'
    }
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as cli_sock:
        cli_sock.connect(('localhost', common.PORT_IPC_NODE))
        cli_sock.sendall(json.dumps(command).encode(common.CODE))


def get_file(args):
    """download a file"""
    command = {
        'func': 'get_file',
        'magnet_text': args.magnet,
        'filename': args.filename
    }
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as cli_sock:
        cli_sock.connect(('localhost', common.PORT_IPC_NODE))
        cli_sock.sendall(json.dumps(command).encode(common.CODE))

    
class NodeCLI:
    """"""
    def __init__(self):
        self.parser = argparse.ArgumentParser(prog='NodeCLI', 
                                              description='CLI for interacting with Node')
        self.add_subparsers()
        
    
    def add_subparsers(self):
        # the function to execute
        self.parser.add_argument('--func')
        
        # for get_file
        self.parser.add_argument('--magnet')
        self.parser.add_argument('--filename')
        
        
    def run(self):
        args = self.parser.parse_args()
        f = globals()[args.func]
        f(args)
        

if __name__ == '__main__':
    cli = NodeCLI()
    cli.run()