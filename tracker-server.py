import socket
import threading
import common

peerlist = [('127.0.0.1', 12345), ('123.456.789.0', 1)]

class PeerManager:
    def __init__(self) -> None:
        pass

def new_connection(addr, conn: socket.socket):
    print(f'Serving connection from ip={addr}')
    
    try:
        data = conn.recv(1024)
        response = ''
        
        # TODO: implement process at tracker side
        request = data.decode(common.CODE)
        request_parts = request.split()
        
        if request_parts[0] == 'submit_info':
            peerip = request_parts[1]
            peerport = request_parts[2]
            with open('tracker.txt', mode='a') as file:
                peerlist.append((peerip, peerport))
            response = 'Information submitted successfully!'
            
        elif request_parts[0] == 'get_list':
            for peerip, peerport in peerlist:
                response += f'{peerip}:{peerport}\n'
                
        else:
            response = 'Invalid request!'
            
        # response to the requesting peer
        conn.sendall(response.encode(common.CODE))
    
    except Exception:
        print('Error occured!')
        
        
    exit()


def server_program(host, port):
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serversocket.bind((host, port))
    
    serversocket.listen(10)
    while True:
        conn, addr = serversocket.accept()
        nconn = threading.Thread(target=new_connection, args=(addr, conn))
        nconn.start()


if __name__ == '__main__':
    hostip = common.get_host_default_interface_ip()
    port = 22236
    print(f'Listening on {hostip}:{port}')
    server_program(hostip,port)