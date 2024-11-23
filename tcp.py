import socket
import threading
import json
from enum import Enum

import common


class MsgType(Enum):
    HANDSHAKE = 0       # first msg exhanged between peers
    BITFIELD = 1        # notify the requesting peer of the pieces it has
    CHOKE = 2           # update state info
    UNCHOKE = 3         # ...
    INTERESTED = 4      # ...
    NOT_INTERESTED = 5  # ...
    REQUEST = 6         # request for a piece with torrent info_hash + index
    PIECE = 7           # send a piece away


class PeerConnection:
    """A management template for 1 peer to manage the connection with 1 other peer"""
    def __init__(self, selfid, self_addr, peerid, peer_addr, info_hash) -> None:
        # connection information
        self.selfid = selfid
        self.self_addr = self_addr
        self.peerid = peerid
        self.peer_addr = peer_addr
        
        # state information
        self.am_choking = True          # this peer is choking the target peer
        self.am_interested = False      # this peer is interested in the target peer
        self.peer_choking = True        # the target peer is choking this peer
        self.peer_interested = False    # the target peer is interested in this peer
        self.active_status = True       # the connection is alive 
        
        # other information
        self.info_hash = info_hash  # info_hash info included in the handshake message
        self.downloaded = 0         # amount of data the target peer downloaded from this peer
        self.uploaded = 0           # amount of data the target peer uploaded to this peer
        
        
    def control_am(self, choking: bool, interested: bool):
        self.am_choking = choking
        self.am_interested = interested
        
        
    def control_peer(self, choking: bool, interested: bool):
        self.peer_choking = choking
        self.peer_interested = interested
                
        
    # def to_dict(self):
    #     return {
    #         'am_choking': self.am_choking,
    #         'am_interested': self.am_interested,
    #         'peer_choking': self.peer_choking,
    #         'peer_interested': self.peer_interested
    #     }
        
    
class PeerConnectionIn(PeerConnection):
    """Handle incoming connection from another peer"""
    def __init__(self, selfid, self_addr, connection: socket.socket, peer_addr: str) -> None:
        # establish connection
        self.conn = connection
        peerid, info_hash = self.accept_handshake()
        super().__init__(selfid, self_addr, peerid, peer_addr, info_hash)
        
    
    def __del__(self):
        self.conn.close()
    
    
    def accept_handshake(self) -> dict: 
        """receive + parse the incomming handshake msg"""
        msg_raw = self.conn.recv(common.BUFFER_SIZE)
        msg = json.loads(msg_raw.decode(common.CODE))
        if MsgType(msg['type']) != MsgType.HANDSHAKE:
            raise Exception('Error! Not a handshake request!')
        return (msg['peerid'], msg['info_hash'])
    
    
    def bitfield(self, bitfield: str):
        """TODO: send a bitfield msg to target peer"""    
    
    
    def piece(self, index: int) -> None:
        """TODO: send msg with data to target peer"""
        pass

        
        
class PeerConnectionOut(PeerConnection):
    """Handle connection to another peer"""
    def __init__(self, selfid, self_addr, peerid, peer_addr, info_hash) -> None:
        super().__init__(selfid, self_addr, peerid, peer_addr, info_hash)
        # establish connection
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn.connect(self.peer_addr)
        self.handshake()
        
        # receive bitfield info from peer
        msg_raw = self.conn.recv(common.BUFFER_SIZE)
        msg = json.loads(msg_raw.decode(common.CODE))
        
        
    def handshake(self):
        """send handshake msg to establish connection with another peer"""
        msg = {
            'type': MsgType.HANDSHAKE.value,
            'peerid': self.selfid,
            'info_hash': self.info_hash
        }
        msg_raw = json.dumps(msg).encode(common.CODE)
        self.conn.sendall(msg_raw)
        
        
    def request(self, index) -> bytes:
        """TODO: request data from target peer"""
        pass 
        