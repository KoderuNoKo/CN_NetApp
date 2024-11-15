import socket
import threading
import common
import json

DEFAULT_TRACKER_ID = 1

class torrent:
    pass   


class Tracker:
    def __init__(self, ip, port):
        # tracker info
        self.id = DEFAULT_TRACKER_ID
        self.ip = ip
        self.port = port
        
        # file_tracking
        self.file_track = {}
        
        
    def tracker_response(self, failure_reason: str = None, warning_msg: str = None, tracker_id: int = None, peers: list = None) -> bytes:
        """generate a string response to the peer"""
        response = {
                    'failure_reason': failure_reason, 
                    'warning_msg': warning_msg, 
                    'tracker_id': tracker_id,
                    'peers': peers
                }
        str_response = json.dumps(response)
        return str_response
    
    # def tracker_approve(self, approved=True) -> str:
    #     """Approval of node request during handshaking"""
    #     return 'OK'
        

    def parse_node_submit_info(self, peer_msg: dict) -> None:
        """Parse the message, record the files' info as a torrent file, raise exception if error occurs"""
        peerid = peer_msg['id']
        peerip = peer_msg['ip']
        peerport = peer_msg['port']
        files = peer_msg['file_info']
        for file in files:
            print(file)
            filename = file['name']
            print(filename)
            # new unregistered file
            if filename not in self.file_track.keys():
                self.file_track[filename] = {
                    'trackerip': self.ip,
                    'piece_len': file['piece_len'],
                    'piece_count': file['piece_count'],
                    'seeders': set() # enfore no duplicate peer for one file
                }
            # add seeder peer
            self.file_track[filename]['seeders'].add((peerid, peerip, peerport))
            
            
    def return_peer_list_for_file(self, file_id: str) -> list:
        """return list of peers holding a file, return None if file not found"""
        if file_id not in self.file_track:
            return None
        
        return list(self.file_track[file_id]['seeders'])
        

    def new_connection(self, addr, conn: socket.socket):
        print(f'Serving connection from {addr}')
        response = ''

        try:
            data = conn.recv(1024).decode(common.CODE)
            peer_request = json.loads(data)
            
            if peer_request['func'] == 'submit_info':
                # get information submitted from node
                data = self.parse_node_submit_info(peer_request)
                response = self.tracker_response() # nothing to response
                                
            elif peer_request['func'] == 'get_list':
                # TODO: return a list of peers with request['magnet_text']
                file_id = peer_request['magnet_text']
                peerlist = self.return_peer_list_for_file(file_id)
                if peerlist is None:
                    response = self.tracker_response(warning_msg=f'No file with name {file_id} is found! Returned empty list', 
                                                        tracker_id=self.id)
                else:
                    response = self.tracker_response(peers=peerlist)
            else:
                raise ValueError(f'Invalid request! No function named {peer_request['func']} is found!')
                
            print(f'Request from peer {peer_request['id']}::{addr}\n {peer_request['func']} DONE!')

        except Exception as e:
            response = self.tracker_response(failure_reason=str(e))
            print(f'Request from peer {peer_request['id']}::{addr}\n {peer_request['func']} FAILED!\n {e}')
            
        finally:
            conn.sendall(response.encode(common.CODE))
            conn.close()
        
        exit()


    def server_program(self):
        serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serversocket.bind((self.ip, self.port))
        serversocket.listen(5)
        print(f'Listening on {self.ip}:{self.port}')

        while True:
            conn, addr = serversocket.accept()
            threading.Thread(target=self.new_connection, args=(addr, conn)).start()


if __name__ == '__main__':
    hostip = common.get_host_default_interface_ip()
    port = 22236
    tracker = Tracker(hostip, port)
    tracker.server_program()