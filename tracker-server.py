import socket
import threading
import common
import json

DEFAULT_TRACKER_ID = 1

class torrent:
    pass   


class Tracker:
    def __init__(self, ip, port):
        self.id = DEFAULT_TRACKER_ID
        self.ip = ip
        self.port = port
        
        
    def tracker_response(self, failure_reason: str, warning_msg: str, tracker_id: int, peers: dict) -> str:
        """generate a string response to the peer"""
        response = {
                    'failure_reason': failure_reason, 
                    'warning_msg': warning_msg, 
                    'tracker_id': tracker_id,
                    'peers': peers
                }
        str_response = json.dump(response)
        print(str_response)
        
    
    def tracker_approve(self, approved=True) -> str:
        """Approval of node request during handshaking"""
        return 'OK'
        

    def parse_node_submit_info(self, data: bytes):
        """TODO: Parse the message, record the files' info as a torrent file, raise exception if error occurs"""
        

    def new_connection(self, addr, conn: socket.socket):
        print(f'Serving connection from {addr}')

        try:
            data = conn.recv(1024)
            request = data.decode(common.CODE)
            request_parts = request.split()

            if request_parts[0] == 'submit_info':
                # approve the request
                response = self.tracker_approve()
                conn.sendall(response.encode(common.CODE))
                # get information submitted from node
                try:
                    data = self.parse_node_submit_info(conn.recv(common.BUFFER_SIZE))
                    response = self.tracker_response(failure_reason=None,
                                                     warning_msg=None,
                                                     tracker_id=self.id,
                                                     peers=None)
                    conn.sendall(response.encode(common.CODE))
                except Exception as e:
                    response = self.tracker_response(failure_reason=str(e),
                                                     warning_msg=None,
                                                     tracker_id=self.id,
                                                     peers=None)
                    conn.sendall(response.encode(common.CODE))
                finally:
                    conn.close()
                    exit()
                              
            elif request_parts[0] == 'get_list':
                for peerip, peerport in self.peer_manager.peerlist:
                    response += f'{peerip}:{peerport}\n'
            else:
                response = 'Invalid request!'

            conn.sendall(response.encode(common.CODE))
        except Exception as e:
            print(f"Error occurred: {e}")
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