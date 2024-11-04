# import socket

# # Server setup
# server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# server_socket.bind(('localhost', 12345))
# server_socket.listen()

# print("Server waiting for connection...")
# conn, addr = server_socket.accept()
# print("Connected by", addr)

# # Receive message
# message = conn.recv(1024).decode()
# print("Received from client:", message)

# # Send response
# conn.sendall("Hello from server!".encode())
# conn.close()

import socket
from threading import Thread


def new_connection(conn, addr):
    print(f'Serving {addr}')
    receiveData = conn.recv(1024)
    data = receiveData.decode("utf-8") # convert bytes to string
    print(f"Received: {data}")


def get_host_default_interface_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
       s.connect(('8.8.8.8',1))
       ip = s.getsockname()[0]
    except Exception:
       ip = '127.0.0.1'
    finally:
       s.close()
    return ip


def server_program(host, port):
    serversocket = socket.socket()
    serversocket.bind((host, port))
    serversocket.listen(10)
    
    while True:
        conn, addr = serversocket.accept()
        nconn = Thread(target=new_connection, args=(conn, addr))
        nconn.start()


if __name__ == "__main__":
    #hostname = socket.gethostname()
    hostip = get_host_default_interface_ip()
    port = 22236
    print("Listening on: {}:{}".format(hostip,port))
    server_program(hostip, port)