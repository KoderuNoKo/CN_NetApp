import socket
import threading
import os
import argparse

import common
# import file
import tcp  # peer wire protocol 


class Downloader:
    def __init__(self, info_hash, peerlist, self_bitfield) -> None:
        self.info_hash = info_hash
        self.peerlist = peerlist
        self.self_bitfield = self_bitfield
        
        self.returned_bitfields = dict()                    # bitfields returned by server nodes, updated by multiple thread_client()
        self._lock_returned_bitfields = threading.Lock()    # lock to protect returned_bitfields
        self.request_queue = list()                         # result returned by select_peer(), thread_client() download based on this
        self._select_completed = threading.Condition()      # notify the threads to start downloading after selection is completed
        
        
    def start_download(self):
        # create threads to connect to server nodes
        [threading.Thread(target=self.thread_client, args=(peer[0], peer[1], peer[2], self.info_hash)) for peer in (self.peerlist)]
        
        # As the threads are created, they obtain bitfield immediately after handshake
        # then use the bitfields obtained to select peer
        self.select_peer()
        
    
    def thread_client(self, node_serverid, node_serverip, node_serverport, info_hash) -> None:
        """client thread that to connect to 1 other peer"""
        # establish connection (handshake)
        print('Thread ID {}: Connecting to Peer {} at {}:{}'.format(threading.get_ident(), node_serverid, node_serverip, node_serverport))
        connection = tcp.PeerConnectionOut(peerid=node_serverid, info_hash=info_hash)
        
        # return the bitfield obtained after handshake
        with self._lock_returned_bitfields:
            self.request_queue[node_serverid] = connection.bitfield
        
        # download from target peer
        with self._select_completed:    # wait for select_peer() to complete
            # TODO: read from self.request_queue and request for pieces
            connection.request()
            
        exit()
        
    
    def select_peer(self) -> list:
        """TODO: decide to request which piece(s) from which peer

        Args:
            bitfields (dict): peerid: bitfield

        Returns:
            list: a list of tuples (peerid, piece_index)
        """
        pass
         
class Node:
    def __init__(self, trackerip: str, trackerport: int, peerid: int, ip: str, port: int):
        # tracker
        self.tracker_address = (trackerip, trackerport)
        
        # peer wire protocol
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
                
                data_raw = common.create_raw_msg(data_send)
                s.sendall(data_raw.encode('utf-8'))
                print('submit files: {}'.format(file_list))
                
            except Exception as e:
                print('submit_info() failed at node: {}'.format(e))
                
            finally:
                # receive response from server
                data_raw = s.recv(common.BUFFER_SIZE)
                tracker_response = common.parse_raw_msg(data_raw)
                
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
            data_raw = common.create_raw_msg(data_send)
            server_sock.sendall(data_raw)
            
            # get response from tracker
            data_raw = server_sock.recv(common.BUFFER_SIZE)
            tracker_response = common.parse_raw_msg(data_raw)
            return tracker_response


    def serve_incoming_connection(self, conn: socket.socket, addr:socket._RetAddress):
        """handle incoming connection from other peers"""
        print('Starting connection from {}'.format(addr))
        connection = tcp.PeerConnectionIn(self_addr=(self.ip, self.port), conn=conn, peer_addr=addr)  
        while connection.is_active:
            msg_raw = conn.recv(common.CODE)
            msg = common.parse_raw_msg(msg_raw)
            if tcp.MsgType(msg['type'] == tcp.MsgType.BITFIELD):
                connection.bitfield()
            if tcp.MsgType(msg['type']) == tcp.MsgType.REQUEST:
                connection.piece(msg['index'])
        print('Finished serving! Connection with {} is closed!'.format(addr))
        exit()
    
    
    def thread_server(self, ip, port):
        """Thread server running on peers to accept connection from other peers"""
        print('Thread server listening on {}:{}'.format(ip, port))
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as serversocket:
            serversocket.bind((ip, port))
            serversocket.listen(10)
            while True:
                conn, addr = serversocket.accept()
                nconn = threading.Thread(target=self.serve_incoming_connection, args=(conn, addr))
                nconn.start()
    

    def thread_agent(self):
        print('Thread agent started!')
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as ipc_sock:
            ipc_sock.bind(('localhost', common.PORT_IPC_NODE))
            ipc_sock.listen()
            
            while True:
                conn, addr = ipc_sock.accept()
                cli_command_raw = conn.recv(common.BUFFER_SIZE)
                cli_command = common.parse_raw_msg(cli_command_raw)
                
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
                    client_threads = [threading.Thread(target=self.thread_client, args=(i, peer[0], peer[1], peer[2], magnet_text)) for i, peer in enumerate(peerlist)]
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
    
    