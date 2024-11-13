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
        
        
    def tracker_response(self, failure_reason: str, warning_msg: str, tracker_id: int, peers: list) -> bytes:
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
        

    def parse_node_submit_info(self, data: dict) -> None:
        """Parse the message, record the files' info as a torrent file, raise exception if error occurs"""
        peerinfo = data
        peerid = peerinfo['id']
        peerip = peerinfo['ip']
        peerport = peerinfo['port']
        files = peerinfo['file_info']
        for file in files.items():
            filename = file['name']
            # new unregistered file
            if filename not in self.file_track:
                self.file_track[filename] = {
                    'trackerip': self.ip,
                    'piece_len': file['piece_len'],
                    'piece_count': file['piece_count'],
                    'seeders': {}
                }
            # add seeder peer
            self.file_track[filename]['seeders'][peerid] = {
                'peerip': peerip,
                'peerport': peerport
            }
        

    def new_connection(self, addr, conn: socket.socket):
        print(f'Serving connection from {addr}')

        try:
            data = conn.recv(1024).decode(common.CODE)
            request = json.loads(data)
            print(request)
            
            if request['func'] == 'submit_info':
                # get information submitted from node
                try:
                    data = self.parse_node_submit_info(request)
                    response = self.tracker_response(failure_reason=None,
                                                     warning_msg=None,
                                                     tracker_id=self.id,
                                                     peers=None)
                except Exception as e:
                    response = self.tracker_response(failure_reason=str(e),
                                                     warning_msg=None,
                                                     tracker_id=self.id,
                                                     peers=None)
                              
            elif request['func'] == 'get_list':
                # TODO: return a list of peers with request['magnet_text']
                pass
                
                    
            else:
                raise ValueError('Invalid request!')
            
            conn.sendall(response.encode(common.CODE))
        except Exception as e:
            print(f'Error occurred while serving {addr}: {e}')
        finally:
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