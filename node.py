import socket
import threading
import os
import json
import argparse

import common

PORT_IPC_NODE = 12345

class Node:
    def __init__(self, tracker_address, peerid, ip, port):
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
    
    
    def submit_info(self):
        """Register this peer's files with the tracker."""
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
                        file_info["file_size"] = str(os.path.getsize(file_path))
                        file_list_info.append(file_info)
                # file_list_str = ";".join(file_list)

                data_to_send = {
                    'func': 'submit_info',
                    'id': self.peerid, 
                    "ip": self.ip, 
                    "port":self.port, 
                    "file_info": file_list_info
                    }
                
                json_data = json.dumps(data_to_send)
                s.sendall(json_data.encode('utf-8'))
                print(f"Submit with tracker: {file_list}")
            except Exception as e:
                print(f"Error registering with tracker: {e}")
                

    def new_server_incoming(self, conn, addr):
        print(addr)
        # TODO: handle incoming connection 
        conn.sendall('Data that need to be sent!')
        conn.close()
        exit()
    
    
    def thread_server(self, ip, port):
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
        print(f'Thread ID: {id} connecting to {serverip}:{serverport}')
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((peerip, peerport))
            data = sock.recv(1024).decode('utf-8')
            print(data)
        
    

    def thread_agent(self, time_fetching: int, peerip: str, peerport: int):
        print('Thread agent started!')
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as ipc_sock:
            ipc_sock.bind(('localhost', PORT_IPC_NODE))
            ipc_sock.listen()
            
            try:
                while True:
                    conn, addr = ipc_sock.accept()
                    cli_msg = conn.recv(1024).decode(common.CODE)
                    msg_parts = cli_msg.split()
                    rep = ''
                    
                    if msg_parts[0] == 'submit_info':
                        serverip = msg_parts[1]
                        serverport = int(msg_parts[2])
                        print(f'Submitting info to server {serverip}:{serverport}')
                        
                        # send request to server
                        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
                            server_sock.connect((serverip, serverport))
                            msg = f'submit_info {peerip} {peerport}'
                            server_sock.sendall(msg.encode(common.CODE))
                            
                            # get response from server
                            rep = server_sock.recv(common.BUFFER_SIZE).decode(common.CODE)
                            
                    elif msg_parts[0] == 'get_list':
                        serverip = msg_parts[1]
                        serverport = int(msg_parts[2])
                        print(f'Requesting server {serverip}:{serverport} for list of peer...')
                        
                        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
                            server_sock.connect((serverip, serverport))
                            msg = f'get_list'
                            server_sock.sendall(msg.encode(common.CODE))
                            
                            # get response from server
                            rep = server_sock.recv(common.BUFFER_SIZE).decode(common.CODE)
                        
                    elif msg_parts[0] == 'peer_connect':
                        self.thread_client(1, msg_parts[1], msg_parts[2])
                        
                    elif msg_parts[0] == 'peer_transfer':
                        print(f'Transfering data to {msg_parts[1]}:{msg_parts[2]} "{msg_parts[3]}"')
                        
                    else:
                        print('Invalid command!')
                    
                    time.sleep(time_fetching)
                    
                    print(rep)    
                    conn.sendall(rep.encode(common.CODE))
                    
            except KeyboardInterrupt:
                print('KeyboardInterrupt! Node agent stopped!')
                exit()
    
    
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
    node.submit_info()
    # intialize server thread
    # tserver = threading.Thread(target=node.thread_server, args=(peerip, peerport))
    
    # # intialize a thread for agent
    # time_fetching = 1
    # tagent = threading.Thread(target=node.thread_agent, args=(time_fetching, peerip, peerport))
    
    # tserver.start()
    
    # tagent.start()
    
    # # never completed
    # tserver.join()
    # tagent.join()
    