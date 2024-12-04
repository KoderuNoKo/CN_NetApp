import socket
import threading
import common
import math

import json

DEFAULT_TRACKER_ID = 1 # single centralized tracker server

# class Torrent: 
#     """represent the metainfo file on tracker"""
#     def __init__(self, tracker_ip: str, filename: str, filesize: int, piece_size: int, pieces_list: list=None) -> None:
#         self.info = {
#             'name': filename,
#             'piece_length': piece_size,
#             # 'pieces': pieces_list, not yet implemented
#             'piece_count': math.ceil(filesize/piece_size)
#         }
#         self.announce = tracker_ip  # announce URL of the tracker
        
        
#     def to_dict(self):
#         return {
#             "metainfo": self.info,
#             "announce": self.announce
#         }


class Tracker:
    def __init__(self, ip, port):
        # tracker info
        self.id = DEFAULT_TRACKER_ID
        self.ip = ip
        self.port = port
        
        # file_tracking
        self.torrent_track = {}
        
        
    def tracker_response(self, failure_reason: str = None, warning_msg: str = None, tracker_id: int = None, peers: list = None) -> dict:
        """generate a string response to the peer"""
        return {
                    'failure_reason': failure_reason, 
                    'warning_msg': warning_msg, 
                    'tracker_id': tracker_id,
                    'peers': peers
        }
    
    # def tracker_approve(self, approved=True) -> str:
    #     """Approval of node request during handshaking"""
    #     return 'OK'
    
    
    def update_torrents_list(self) -> None:
        """Write torrents into a text file for peers to view"""
        with open('torrents_list.txt', mode='w') as file:
            [file.write('{}: {}\n\n'.format(key, item['torrent'])) for key, item in self.torrent_track.items()]
        

    def parse_node_submit_info(self, peer_msg: dict) -> None:
        """Parse the message, record the files' info as a torrent file, raise exception if error occurs"""
        # TODO: fix new record remove the old one
        peerid = peer_msg['id']
        peerip = peer_msg['ip']
        peerport = peer_msg['port']
        files = peer_msg['file_info']
        hash_codes = [file['total_hash'] for file in files]
        self.torrent_track = {
            hash_code: {
                'torrent': self.torrent_track[hash_code]['torrent']
                if hash_code in self.torrent_track
                else file,
                
                'peers': self.torrent_track[hash_code]['peers'] + [(peerid, peerip, peerport)]
                if hash_code in self.torrent_track
                else [(peerid, peerip, peerport)],
            }
            for hash_code, file in zip(hash_codes, files)
        }  
        self.update_torrents_list()
            
            
    def return_peer_list_for_file(self, info_hash: str) -> list:
        """return list of peers holding a file, return None if file not found"""
        if info_hash not in self.torrent_track.keys():
            return None
        
        return self.torrent_track[info_hash]['peers']
        

    def new_connection(self, addr, conn: socket.socket):
        print('Serving connection from {}'.format(addr))
        response = ''

        try:
            data_raw = conn.recv(common.BUFFER_SIZE)
            peer_request = common.parse_raw_msg(data_raw)
            print(json.dumps(peer_request, indent=4))
            
            if peer_request['func'] == 'submit_info':
                # get information submitted from node
                self.parse_node_submit_info(peer_request)
                response = self.tracker_response() # nothing to response
                                
            elif peer_request['func'] == 'GET':
                info_hash = peer_request['magnet_text']
                peerlist = self.return_peer_list_for_file(info_hash)
                if peerlist is None:
                    response = self.tracker_response(warning_msg='No file with name {} is found! Returned empty list'.format(info_hash), 
                                                        tracker_id=self.id)
                else:
                    response = self.tracker_response(peers=peerlist)
            else:
                raise ValueError('Invalid request! No function named {} is found!'.format(peer_request['func']))
                
            print('Request from peer {}::{}\n {} DONE!'.format(peer_request['id'], addr, peer_request['func']))

        except Exception as e:
            response = self.tracker_response(failure_reason=str(e))
            print('Request from peer {}::{}\n {} FAILED!\n {}'.format(peer_request['id'], addr, peer_request['func'], e))
            
        finally:
            response_raw = common.create_raw_msg(response)
            conn.sendall(response_raw)
            conn.close()
        
        exit()


    def server_program(self):
        serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serversocket.bind((self.ip, self.port))
        serversocket.listen(5)
        print('Listening on {}:{}'.format(self.ip, self.port))

        while True:
            conn, addr = serversocket.accept()
            threading.Thread(target=self.new_connection, args=(addr, conn)).start()


if __name__ == '__main__':
    hostip = common.get_host_default_interface_ip()
    port = 22236
    tracker = Tracker(hostip, port)
    tracker.server_program()