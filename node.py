import socket
import threading
import os
import json
import argparse
import time
import math

import common

PORT_IPC_NODE = 12345

class Node:
    def __init__(self, tracker_address: tuple[str, int], peerid: int, ip: str, port: int):
        self.tracker_address = tracker_address
        self.peerid = peerid
        self.ip = ip
        self.port = port
        self.repository = f"peer_{self.port}_repository"
        os.makedirs(self.repository, exist_ok=True)
        self.files = {}
    

    def scan_repository(self):
        """Scan the repository folder for available files."""
        file_list = os.listdir(self.repository)
        if not file_list:
            print(f"Repository '{self.repository}' is empty. Please add files.")
        return file_list
    
    
    def submit_info(self) -> dict:
        """Register this peer's files with the tracker. Return the response showing the result to the cli"""
        file_list = self.scan_repository()
        file_list_info = []
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.connect(self.tracker_address)
                #s.sendall(f"Submit_info: {self.ip} {self.port}".encode('utf-8'))
                for file_name in file_list:
                    file_info = {}
                    file_path = os.path.join(self.repository, file_name)
                    if os.path.isfile(file_path):
                        file_info['name'] = file_name
                        file_info['piece_len'] = common.PIECE_SIZE
                        file_info['piece_count'] = math.ceil(os.path.getsize(file_path) / file_info['piece_len'])
                        file_list_info.append(file_info)
                # file_list_str = ";".join(file_list)

                data_send = {
                    'func': 'submit_info',
                    'id': self.peerid, 
                    'ip': self.ip, 
                    'port':self.port, 
                    'file_info': file_list_info
                    }
                
                json_data = json.dumps(data_send)
                s.sendall(json_data.encode('utf-8'))
                print(f'Submit files: {file_list}')
                
            except Exception as e:
                print(f'submit_info() failed at node: {e}')
                
            finally:
                # receive response from server
                data_recv = s.recv(common.BUFFER_SIZE).decode(common.CODE)
                tracker_response = json.loads(data_recv)
                
        return tracker_response
    
    
    def get_list(self, magnet_text: str):
        """send a magnet_text to server to request for a list of peers"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
            server_sock.connect(self.tracker_address)
            data_send = {
                'func': 'get_list',
                'id': self.peerid, 
                'ip': self.ip, 
                'port':self.port, 
                'magnet_text': magnet_text
                }
            server_sock.sendall(json.dumps(data_send).encode(common.CODE))
            
            # get response from tracker
            data_recv = server_sock.recv(common.BUFFER_SIZE).decode(common.CODE)
            tracker_response = json.loads(data_recv)
            return tracker_response


    def new_server_incoming(self, conn, addr):
        """handle new connection from other peers"""
        print(addr)
        # TODO: handle incoming connection 
        conn.sendall('Data that need to be sent!')
        conn.close()
        exit()
    
    
    def thread_server(self, ip, port):
        """Thread server running on peers to accept connection from other peers"""
        print("Thread server listening on {}:{}".format(ip, port))
        try:
            serversocket = socket.socket()
            serversocket.bind((ip, port))
            
            serversocket.listen(10)
            while True:
                conn, addr = serversocket.accept()
                nconn = threading.Thread(target=self.new_server_incoming, args=(conn, addr))
                nconn.start()
        except KeyboardInterrupt:
            print('KeyboardInterrupt! Server thread stopped!')
        finally:
            serversocket.close()
            
            
    def thread_client(self, id, serverip, serverport, peerip, peerport):
        """client thread used to connect to other peers"""
        print(f'Thread ID: {id} connecting to {serverip}:{serverport}')
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((peerip, peerport))
            data = sock.recv(1024).decode('utf-8')
            print(data)
        
    

    def thread_agent(self):
        print('Thread agent started!')
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as ipc_sock:
            ipc_sock.bind(('localhost', PORT_IPC_NODE))
            ipc_sock.listen()
            
            while True:
                conn, addr = ipc_sock.accept()
                cli_msg = conn.recv(1024).decode(common.CODE)
                msg_parts = cli_msg.split()
                
                print('----------------------------------------------------------------------------------------')
                if msg_parts[0] == 'submit_info':
                    print(f'Submitting info to tracker server at {self.tracker_address}...')
                    rep = self.submit_info()
                    if rep['failure_reason'] is not None:
                        print(f'submit_info() failed at tracker: {rep['failure_reason']}')
                        
                elif msg_parts[0] == 'get_list':
                    magnet_text = msg_parts[1]
                    print(f'Requesting tracker for torrent: {magnet_text}')
                    rep = self.get_list(magnet_text)
                    if rep['failure_reason'] is None:
                        print(f'Peer list: {rep['peers']}')
                    else:
                        print(f'get_list() failed at server: {rep['failure_reason']}')
                    
                elif msg_parts[0] == 'peer_connect':
                    self.thread_client(1, msg_parts[1], msg_parts[2])
                    
                elif msg_parts[0] == 'peer_transfer':
                    print(f'Transfering data to {msg_parts[1]}:{msg_parts[2]} "{msg_parts[3]}"')
                    
                else:
                    print('Invalid command!')
                
                
                print(rep)    
    
    
if __name__ == '__main__':
    """Initialize node agent"""
    parser = argparse.ArgumentParser(
        prog='Node-CLI',
        description='Node connect to pre-declared server',
        epilog='<-- !!! It requires the server to be running and listening !!!'
    )
    
    parser.add_argument('--id', type=int)
    parser.add_argument('--serverip')
    parser.add_argument('--serverport', type=int)
    args = parser.parse_args()
    
    
    # initialize client thread
    peerip = common.get_host_default_interface_ip()
    peerport = 33357    
    
    node = Node((args.serverip, args.serverport), args.id, peerip, peerport)
    
    # intialize server thread
    tserver = threading.Thread(target=node.thread_server, args=(peerip, peerport))
    
    # # intialize a thread for agent
    time_fetching = 1
    tagent = threading.Thread(target=node.thread_agent)
    
    tserver.start()
    tagent.start()
    
    # never completed
    tserver.join()
    tagent.join()
    