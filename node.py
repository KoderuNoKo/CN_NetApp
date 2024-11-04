import time
import argparse
import socket
import threading

import common


PORT_IPC_NODE = 12345


def new_server_incoming(addr, conn):
    print(addr)
    # TODO: handle incoming connection 
    
    
def thread_server(host, port):
    print("Thread server listening on {}:{}".format(host, port))
    try:
        serversocket = socket.socket()
        serversocket.bind((host, port))
        
        serversocket.listen(10)
        while True:
            addr, conn = serversocket.accept()
            nconn = threading.Thread(target=new_server_incoming, args=(addr, conn))
            nconn.start()
    except KeyboardInterrupt:
        print('KeyboardInterrupt! Server thread stopped!')
    finally:
        serversocket.close()
        
        
def thread_client(id, serverip, serverport, peerip, peerport):
    print(f'Thread ID: {id} connecting to {serverip}:{serverport}')
    

def thread_agent(time_fetching: int, peerip: str, peerport: int):
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
                    thread_client(1, msg_parts[1], msg_parts[2])
                    
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
    
    # initialize client thread
    peerip = common.get_host_default_interface_ip()
    peerport = 33357    
    # intialize server thread
    tserver = threading.Thread(target=thread_server, args=(peerip, peerport))
    
    # intialize a thread for agent
    time_fetching = 1
    tagent = threading.Thread(target=thread_agent, args=(time_fetching, peerip, peerport))
    
    tserver.start()
    
    tagent.start()
    
    # never completed
    tserver.join()
    tagent.join()
    