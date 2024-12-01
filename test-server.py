import socket

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.bind(('192.168.1.107', 22237))
    sock.listen(10)
    print('listening on 192.168.1.107:22236')
    conn, addr = sock.accept()
    data = conn.recv(1024).decode('utf-8')
    print(data)
    
