import socket
import threading
import os
import json
import argparse
import time
import math

import common
# import file

class Node:
    def __init__(self, tracker_address: tuple[str, int], peerid: int, ip: str, port: int):
        # tracker
        self.tracker_address = tracker_address
        
        # peer server
        self.peerid = peerid
        self.ip = ip
        self.port = port
        
        # file
        self.repository = 'peer_{}_repository'.format(self.port)
        os.makedirs(self.repository, exist_ok=True)
        self.files = {}
        self.uploaded = 0
        self.downloaded = 0
    

    def scan_repository(self):
        """Scan the repository folder for available files."""
        file_list = os.listdir(self.repository)
        if not file_list:
            print('Repository {} is empty. Please add files.'.format(self.repository))
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
                        file_info['piece_length'] = common.PIECE_SIZE
                        file_info['size'] = os.path.getsize(file_path)
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
                print('submit files: {}'.format(file_list))
                
            except Exception as e:
                print('submit_info() failed at node: {}'.format(e))
                
            finally:
                # receive response from server
                data_recv = s.recv(common.BUFFER_SIZE).decode(common.CODE)
                tracker_response = json.loads(data_recv)
                
        return tracker_response
    
    
    def get_list(self, magnet_text: str):
        """send a magnet_text to server to request a list of peers"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
            server_sock.connect(self.tracker_address)
            data_send = {
                'func': 'GET',
                'uploaded': self.uploaded,
                'downloaded': self.downloaded,
                # 'left': ??? maybe this is unnecessary in the first request
                'id': self.peerid, 
                'ip': self.ip, 
                'port':self.port, 
                'event': 'started',
                'magnet_text': magnet_text
            }
            server_sock.sendall(json.dumps(data_send).encode(common.CODE))
            
            # get response from tracker
            data_recv = server_sock.recv(common.BUFFER_SIZE).decode(common.CODE)
            tracker_response = json.loads(data_recv)
            return tracker_response


    def serve_incoming_connection(self, conn, addr):
        """handle incoming connection from other peers"""
        print('Serving connection from {}'.format(addr))
        msg = 'This is peer {} responding!'.format(self.peerid)
        conn.sendall(msg.encode(common.CODE))
        conn.close()
        print('Finished serving! Connection with {} is closed!'.format(addr))
        
        # TODO: implement file transfering
        exit()
    
    
    def thread_server(self, ip, port):
        """Thread server running on peers to accept connection from other peers"""
        print('Thread server listening on {}:{}'.format(ip, port))
        try:
            serversocket = socket.socket()
            serversocket.bind((ip, port))
            
            serversocket.listen(10)
            while True:
                conn, addr = serversocket.accept()
                nconn = threading.Thread(target=self.serve_incoming_connection, args=(conn, addr))
                nconn.start()
        except KeyboardInterrupt:
            print('KeyboardInterrupt! Server thread stopped!')
        finally:
            serversocket.close()
            
            
    def thread_client(self, thread_id, node_serverid, node_serverip, node_serverport):
        """client thread used to connect to other peers"""
        print('Thread ID {}: Connecting to Peer {} at {}:{}'.format(thread_id, node_serverid, node_serverip, node_serverport))
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((node_serverip, node_serverport))
            msg = '{} to other peer! Just hanging around!'.format(self.peerid)
            sock.sendall(msg.encode(common.CODE))
            data = sock.recv(common.BUFFER_SIZE).decode('utf-8')
            print(data)
            
        # TODO: request file
        exit()
        
    

    def thread_agent(self):
        print('Thread agent started!')
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as ipc_sock:
            ipc_sock.bind(('localhost', common.PORT_IPC_NODE))
            ipc_sock.listen()
            
            while True:
                conn, addr = ipc_sock.accept()
                cli_command = json.loads(conn.recv(common.BUFFER_SIZE).decode(common.CODE))
                
                print('\n----------------------------------------------------------------------------------------\n')
                if cli_command['func'] == 'submit_info':
                    print('Submitting info to tracker server at {}...'.format(self.tracker_address))
                    rep = self.submit_info()
                    if rep['failure_reason'] is not None:
                        print('submit_info() failed at tracker: {}'.format(rep['failure_reason']))
                        
                elif cli_command['func'] == 'get_file':
                    magnet_text = cli_command['magnet_text']
                    print('Requesting tracker for torrent: {}'.format(magnet_text))
                    rep = self.get_list(magnet_text)
                    
                    # request failed at server
                    if rep['failure_reason'] is not None:
                        print('get_list() failed at server: {}'.format(rep['failure_reason']))
                        continue
                    elif rep['warning_msg'] is not None:
                        print('Warning: {}'.format(rep['warning_msg']))
                        
                    # TODO: proceed to connects to each peer for file
                    peerlist = rep['peers']
                    print('Peer list: {}'.format(peerlist))
                    # TODO: peer selection algorithm
                    client_threads = [threading.Thread(target=self.thread_client, args=(peer[0], peer[1], peer[2])) for peer in peerlist]
                    [t.start() for t in client_threads]
                    [t.join() for t in client_threads]
                    
                # elif cli_command['p'] == 'peer_connect':
                #     self.thread_client(1, cli_command[1], cli_command[2])
                    
                # elif cli_command[0] == 'peer_transfer':
                #     print(f'Transfering data to {cli_command[1]}:{cli_command[2]} "{cli_command[3]}"')
                    
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
    parser.add_argument('--port', type=int)
    parser.add_argument('--serverip')
    parser.add_argument('--serverport', type=int)
    args = parser.parse_args()
    
    
    # initialize client thread
    peerip = common.get_host_default_interface_ip()
    peerport = args.port
    
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
    
    