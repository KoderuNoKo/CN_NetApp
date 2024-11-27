import socket
import threading
from enum import Enum

import common


class MsgType(Enum):
    HANDSHAKE = 0       # first msg exhanged between peers
    BITFIELD = 1        # notify the requesting peer of the pieces that it has
    # CHOKE = 2           # update state info
    # UNCHOKE = 3         # ...
    # INTERESTED = 4      # ...
    # NOT_INTERESTED = 5  # ...
    REQUEST = 6         # request for a piece in torrent using index
    PIECE = 7           # send a piece away
    END = 8             # closing connection


class PeerConnection:
    """A management template for 1 peer to manage the connection with another peer"""
    # downloaded = dict()
    # uploaded = dict()
    # lock = threading.Lock()     # ensure thread_safety
    def __init__(self, peerid, peer_addr, info_hash) -> None:
        # connection information
        # self.selfid = selfid
        # self.self_addr = self_addr 
        self.peerid = peerid
        self.peer_addr = peer_addr
        
        # state information
        self.is_active = True       # the connection is alive
        # with PeerConnection.lock:
        #     PeerConnection.downloaded[peerid] = 0
        #     PeerConnection.uploaded[peerid] = 0
        # self.am_choking = True          # this peer is choking the target peer
        # self.am_interested = False      # this peer is interested in the target peer
        # self.peer_choking = True        # the target peer is choking this peer
        # self.peer_interested = False    # the target peer is interested in this peer
        
        # other information
        self.info_hash = info_hash  # info_hash info included in the handshake message
        
        
    # def control_am(self, choking: bool, interested: bool):
    #     self.am_choking = choking
    #     self.am_interested = interested
        
        
    # def control_peer(self, choking: bool, interested: bool):
    #     self.peer_choking = choking
    #     self.peer_interested = interested
                
        
    # def to_dict(self):
    #     return {
    #         'am_choking': self.am_choking,
    #         'am_interested': self.am_interested,
    #         'peer_choking': self.peer_choking,
    #         'peer_interested': self.peer_interested
    #     }
        
    
class PeerConnectionIn(PeerConnection):
    """Handle incoming connection from another peer"""
    def __init__(self, conn: socket.socket, peer_addr: str) -> None:
        # establish connection
        self.conn = conn
        peerid, info_hash = self.accept_handshake()
        if peerid is None:
            return
        super().__init__(peerid, peer_addr, info_hash)
        self.bitfield()
    
    
    def accept_handshake(self) -> dict:
        """receive + parse the incomming handshake msg"""
        msg_raw = self.conn.recv(common.BUFFER_SIZE)
        msg = common.parse_raw_msg(msg_raw)
        if MsgType(msg['type']) != MsgType.HANDSHAKE:
            self.terminate_connection(reason='Error! Not a handshake message!')
            return None, None
        return (msg['peerid'], msg['info_hash'])
    
    
    def bitfield(self):
        """TODO: send a bitfield msg to target peer"""
        pass
    
    
    def piece(self, index: int) -> None:
        """TODO: send msg with data to target peer"""
        pass
    
    
    def terminate_connection(self, reason: str) -> None:
        reply = dict(type=MsgType.END.value(), reason=reason)
        reply_raw = common.create_raw_msg(reply)
        self.conn.sendall(reply_raw)
        self.is_active = False

        
class PeerConnectionOut(PeerConnection):
    """Handle connection to another peer"""
    def __init__(self, peerid, peer_addr, info_hash) -> None:
        super().__init__(peerid, peer_addr, info_hash)
        # establish connection
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn.connect(self.peer_addr)
        self.handshake()
        
        # receive bitfield info from peer
        msg_raw = self.conn.recv(common.BUFFER_SIZE)
        msg = common.parse_raw_msg(msg_raw)
        self.bitfield = msg['bitfield']
        
        
    def handshake(self):
        """send handshake msg to establish connection with another peer"""
        msg = {
            'type': MsgType.HANDSHAKE.value,
            'peerid': self.selfid,
            'info_hash': self.info_hash
        }
        msg_raw = common.create_raw_msg(msg)
        self.conn.sendall(msg_raw)
        
        
    def request(self, index) -> bytes:
        """TODO: request data from target peer"""
        pass 