
# TODO: Deal with sending bytes in json message

import socket
from enum import Enum
import base64

import file
import common


# class File:
#     """Empty sample class, represent a file object"""
#     def __init__(self, info_hash: str, num_piece: int) -> None:
#         self.info_hash = info_hash
#         self.num_piece = num_piece
    
    
#     def get_piece_with_index(self, index: int):
#         return 'This is piece {} of file {}\n'.format(index, self.info_hash)
    
    
#     def get_bitfield(self) -> str:
#         return str.join('', ['1' for i in range(self.num_piece)])


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
    def __init__(self, selfid, peerid, peer_addr, info_hash) -> None:
        # connection information
        # self.self_addr = self_addr 
        self.selfid = selfid
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
        
    def close_connection(self) -> None:
        self.is_active = False
        
    
class PeerConnectionIn(PeerConnection):
    """Handle incoming connection from another peer"""
    def __init__(self, selfid, conn: socket.socket, peer_addr: str, files: file.File_upload) -> None:
        # establish connection
        self.conn = conn
        self.files = files
        peerid, info_hash = self.accept_handshake()
        print('handshake completed - Accepted! Communating with peerid={} over {}'.format(peerid, conn.getsockname()))
        if peerid is None:
            return
        super().__init__(selfid, peerid, peer_addr, info_hash)
        
    
    def accept_handshake(self) -> tuple:
        """receive + parse the incomming handshake msg"""
        msg_raw = self.conn.recv(common.BUFFER_SIZE)
        msg = common.parse_raw_msg(msg_raw)
        if MsgType(msg['type']) != MsgType.HANDSHAKE:
            self.terminate_connection(reason='Error! Not a handshake message!')
            return None, None
        
        # return bitfield message to requesting peer
        
        # TODO: replace with actual file handler
        self.file = self.files[msg['info_hash']]
        bitfield_msg = {
            'type': MsgType.BITFIELD.value,
            'bitfield': self.file.get_bitfield()
        }
        bitfield_msg_raw = common.create_raw_msg(bitfield_msg)
        self.conn.sendall(bitfield_msg_raw)
        print('Sent bitfield: {}'.format(bitfield_msg['bitfield']))
        print('\n\n\n{}\n\n\n'.format(msg))
        return msg['peerid'], msg['info_hash']
        
    
    def piece(self, index: int) -> None:
        """send msg with data to target peer"""
        data_raw = self.file.get_piece_with_index(index).data
        self.conn.sendall(data_raw)
        print('Piece sent, index = {}'.format(index))
        
        
    def terminate_connection(self, reason) -> None:
        reply = dict(type=MsgType.END.value, reason=reason)
        reply_raw = common.create_raw_msg(reply)
        self.conn.sendall(reply_raw)
        self.close_connection()

        
class PeerConnectionOut(PeerConnection):
    """Handle connection to another peer"""
    def __init__(self, selfid, peerid, peer_addr, info_hash) -> None:
        super().__init__(selfid, peerid, peer_addr, info_hash)
        # establish connection
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn.connect(self.peer_addr)
        self.handshake()
        print('Connection established with {} over {}'.format(peerid, self.conn.getsockname()))
                
        
    def handshake(self):
        """send handshake msg to establish connection with another peer"""
        print('Doing handshake')
        msg = {
            'type': MsgType.HANDSHAKE.value,
            'peerid': self.selfid,
            'info_hash': self.info_hash
        }
        msg_raw = common.create_raw_msg(msg)
        self.conn.sendall(msg_raw)
                
        # receive bitfield info from peer
        msg_raw = self.conn.recv(common.BUFFER_SIZE)
        msg = common.parse_raw_msg(msg_raw)
        self.bitfield = msg['bitfield']
        print('received bitfield from {}: {}'.format(self.peerid, self.bitfield))
        
        
    def request(self, index) -> tuple:
        """
        request data from target peer,
        return index if download successfully, and None otherwise
        """
        # request a piece from server node
        print('requesting from {}, index = {}'.format(self.peerid, index))
        msg = {
            'type': MsgType.REQUEST.value,
            'peerid': self.selfid,
            'index': index
        }
        
        msg_raw = common.create_raw_msg(msg)
        self.conn.sendall(msg_raw)
        
        # get response from node server
        data_raw = self.conn.recv(common.PIECE_SIZE)
        return data_raw, index
    
    
    def terminate_connection(self, reason) -> None:
        reply = dict(type=MsgType.END.value, reason=reason)
        reply_raw = common.create_raw_msg(reply)
        self.conn.sendall(reply_raw)
        self.conn.close()
        self.close_connection()