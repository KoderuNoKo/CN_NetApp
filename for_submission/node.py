import socket
import threading
import os
import argparse

import common
import file
import tcp  # peer wire protocol 


class Downloader:
    def __init__(self, selfid, info_hash, peerlist, repo_path, filename) -> None:
        self.info_hash = info_hash
        self.peerlist = peerlist
        self.selfid = selfid
        self.num_pieces = None
        self.repo_path = repo_path
        self.filename = filename
        
        self.returned_bitfields = dict()                            # bitfields returned by server nodes, updated by multiple thread_client()
        self._lock_returned_bitfields = threading.Lock()            # lock to protect returned_bitfields
        self._cond_get_bitfield_completed = threading.Condition()   # notify that all bitfields from peers obtained
        self._is_get_bitfield_completed = False                     # associate with condition
        
        self.request_list = None                            # result returned by select_peer(), thread_client() download based on this
        self._cond_select_completed = threading.Condition() # notify the threads to start downloading after selection is completed
        self._is_select_completed = False                   # associate with condition
        
        self.file_obj = file.File_download()    # object to assemble pieces into file
        self._lock_file_obj = threading.Lock()  # lock to protect file object
        
        
    def start_download(self) -> None:
        # create threads to connect to server nodes
        tclients = [threading.Thread(target=self.thread_client, args=(peer[0], peer[1], peer[2], self.info_hash)) for peer in (self.peerlist)]
        [tclient.start() for tclient in tclients]
        
        # As the threads are created, they obtain bitfield immediately after handshake
        # then use the bitfields obtained to select peer
        # wait until all bitfields are returned
        with self._cond_get_bitfield_completed:
            while not self._is_get_bitfield_completed:
                self._cond_get_bitfield_completed.wait()
            self.select_peer()
            
        # TODO: check if all pieces downloaded successfully
        [tclient.join() for tclient in tclients]
        self.file_obj.save_complete_file(self.repo_path, self.filename)
        return
        
        
    def thread_client(self, node_serverid, node_serverip, node_serverport, info_hash) -> None:
        """client thread that to connect to 1 other peer"""
        # establish connection (handshake)
        print('Thread ID {}: Connecting to Peer {} at {}:{}'.format(threading.get_ident(), node_serverid, node_serverip, node_serverport))
        connection = tcp.PeerConnectionOut(self.selfid, node_serverid, (node_serverip, node_serverport), info_hash)
        
        # return the bitfield obtained after handshake
        
        with self._lock_returned_bitfields:
            print('Thread ID {}: Writing bitfield'.format(threading.get_ident()))
            self.returned_bitfields[node_serverid] = connection.bitfield
            if len(self.returned_bitfields) == len(self.peerlist):
                with self._cond_get_bitfield_completed:
                    self._is_get_bitfield_completed = True
                    self._cond_get_bitfield_completed.notify()        # getting bitfield completed
                print('Received all bitfields!')
        
        # wait for select_peer() to complete
        with self._cond_select_completed:
            while not self._is_select_completed:
                self._cond_select_completed.wait()
        
        # download from target peer
        success = [connection.request(index) for index, peerid in enumerate(self.request_list) if peerid == node_serverid]
        with self._lock_file_obj:
            [self.file_obj.add_piece(data, index) for data, index in success if index is not None]
        connection.terminate_connection(reason='Completed')
        exit()
        
    
    def select_peer(self) -> None:
        """decide to request which piece(s) from which peer
        Args:
            bitfields (dict): peerid: bitfield
        Returns:
            None: a list of tuples (peerid, piece_index) is written to self.request_list
        """
        print('Selecting peer...')  
        self.num_pieces = len(list(self.returned_bitfields.values())[0])
        if not all(len(bitfield) == self.num_pieces for bitfield in self.returned_bitfields.values()):
            raise Exception('Download {} - FAILED! Length of all bitfields must be equal in length!'.format(self.info_hash))
        
        peer_piece_count = {peer: 0 for peer in self.returned_bitfields}    # count of pieces each peer has
        pieces_needed = list(range(self.num_pieces))                             # track pieces to be assigned
        piece_peers = {i: [] for i in range(self.num_pieces)}                    # available peers for each piece
        for peer, bitfield in self.returned_bitfields.items():
            for i, has_piece in enumerate(bitfield):
                if has_piece:
                    piece_peers[i].append(peer)
                    
        self.request_list = [None] * self.num_pieces                     # selected peers for each piece
        
        for piece_index in pieces_needed:
            available_peers = piece_peers[piece_index]
            available_peers.sort(key=lambda peer: peer_piece_count[peer])
            selected_peer = available_peers[0]
            self.request_list[piece_index] = selected_peer
            peer_piece_count[selected_peer] += 1
        
        # prepare file object
        self.file_obj.set_num_pieces(self.num_pieces)
        
        # notify the client_threads to start downloading
        with self._cond_select_completed:
            self._is_select_completed = True
            self._cond_select_completed.notify_all()
            print('Peer selection completed: {}'.format(self.request_list))
        
         
class Node:
    def __init__(self, tracker_address: tuple, peerid: int, ip: str, port: int):
        # tracker
        self.tracker_address = tracker_address
        
        # peer node server
        self.peerid = peerid
        self.ip = ip
        self.port = port
        tserver = threading.Thread(target=self.thread_server)
        tagent = threading.Thread(target=self.thread_agent)
        
        # file
        self.repository_path = 'peer_{}_repository'.format(self.port)
        os.makedirs(self.repository_path, exist_ok=True)        
        # init self.files
        file_list = self.scan_repository()
        self.file_list_info = dict()
        
        for file_name in file_list:
            file_path = os.path.join(self.repository_path, file_name)
            temp = file.File_upload(file_path)
            self.file_list_info[temp.metainfo['total_hash']] = temp

        tserver.start()
        tagent.start()
        tserver.join()
        tagent.join()
        

    def scan_repository(self):
        """Scan the repository folder for available files."""
        file_list = os.listdir(self.repository_path)
        if not file_list:
            print('Repository {} is empty. Please add files.'.format(self.repository_path))
        return file_list
    
    
    def submit_info(self) -> dict:
        """Register this peer's files with the tracker. Return the response showing the result to the cli"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.connect(self.tracker_address)
                data_send = {
                    'func': 'submit_info',
                    'id': self.peerid, 
                    'ip': self.ip, 
                    'port':self.port, 
                    'file_info': [file.get_metainfo() for key, file in self.file_list_info.items()]
                }
                
                data_raw = common.create_raw_msg(data_send)
                print('Submitting data to tracker')
                s.sendall(data_raw)
                print('Submit to server completed')
                print('submit files: {}'.format([file_info.get_metainfo()['name'] for key, file_info in self.file_list_info.items()]))
                                
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
                'id': self.peerid, 
                'ip': self.ip, 
                'port':self.port, 
                'magnet_text': magnet_text
            }
            data_raw = common.create_raw_msg(data_send)
            server_sock.sendall(data_raw)
            
            # get response from tracker
            data_raw = server_sock.recv(common.BUFFER_SIZE)
            tracker_response = common.parse_raw_msg(data_raw)
            return tracker_response


    def serve_incoming_connection(self, conn: socket.socket, addr):
        """handle incoming connection from other peers"""
        print('Starting connection from {}'.format(addr))
        connection = tcp.PeerConnectionIn(selfid=self.peerid, conn=conn, peer_addr=addr, files=self.file_list_info)  
        while connection.is_active:
            msg_raw = conn.recv(common.BUFFER_SIZE)
            msg = common.parse_raw_msg(msg_raw)
            if tcp.MsgType(msg['type']) == tcp.MsgType.REQUEST:
                connection.piece(msg['index'])
            elif tcp.MsgType(msg['type']) == tcp.MsgType.END:
                print('Peer closed connection: {}'.format(msg['reason']))
                connection.close_connection()
                conn.close()
        print('Finished serving! Connection with {} is closed!'.format(addr))
        exit()
    
    
    def thread_server(self):
        """Thread server running on peers to accept connection from other peers"""
        print('Thread server listening on {}:{}'.format(self.ip, self.port))
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as serversocket:
            serversocket.bind((self.ip, self.port))
            serversocket.listen(10)
            while True:
                conn, addr = serversocket.accept()
                nconn = threading.Thread(target=self.serve_incoming_connection, args=(conn, addr))
                nconn.start()
        
                
    def thread_download(self, info_hash: str, filename: str, peerlist: list):
        d = Downloader(self.peerid, info_hash, peerlist, self.repository_path, filename)
        d.start_download()
        print('Download completed!')
        exit()
    

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
                    magnet_texts = cli_command['magnet_text']
                    filenames = cli_command['filename']
                    for magnet_text, filename in zip(magnet_texts.split(','), filenames.split(',')):
                        if cli_command['magnet_text'] in self.file_list_info.keys():
                            print('File already exist! check repository!^_^')
                            continue
                        print('Requesting tracker for torrent: {}'.format(magnet_text))
                        rep = self.get_list(magnet_text)
                        
                        # request failed at server
                        if rep['failure_reason'] is not None:
                            print('get_list() failed at server: {}'.format(rep['failure_reason']))
                            continue
                        
                        elif rep['warning_msg'] is not None:
                            print('Warning: {}'.format(rep['warning_msg']))
                            
                        tdownload = threading.Thread(target=self.thread_download, args=(magnet_text, filename, rep['peers']))
                        tdownload.start()
                    
                else:
                    print('Invalid command!')
                    
    
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
    
    peerip = common.get_host_default_interface_ip()
    peerport = args.port
    
    node = Node((args.serverip, args.serverport), args.id, peerip, peerport)