import math
import json
import hashlib


def hash_info(metainfo: dict) -> str:
   metainfo_str = json.dumps(metainfo)
   return hashlib.sha1(metainfo_str.encode('utf-8')).hexdigest()


class Torrent: 
    """represent the metainfo file on tracker"""
    def __init__(self, tracker_ip: str, filename: str, filesize: int, piece_size: int, pieces_list: list) -> None:
        self.info = {
            'name': filename,
            'piece_length': piece_size,
            'pieces': pieces_list,
            'piece_count': math.ceil(filesize/piece_size)
        }
        self.announce = tracker_ip  # announce URL of the tracker
        
        
    def to_dict(self):
        return {
            "metainfo": self.info,
            "announce": self.announce
        }


class Tracker:
    def __init__(self, ip, port):
        # tracker info
        self.id = 1
        self.ip = ip
        self.port = port
        
        # file_tracking
        self.torrent_track = dict()
        
        
    def tracker_response(self, failure_reason: str = None, warning_msg: str = None, tracker_id: int = None, peers: list = None) -> bytes:
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
        

    def parse_node_submit_info(self, peer_msg: dict) -> None:
        """Parse the message, record the files' info as a torrent file, raise exception if error occurs"""
        peerid = peer_msg['id']
        peerip = peer_msg['ip']
        peerport = peer_msg['port']
        files = peer_msg['file_info']
        hash_codes = [hash_info(file) for file in files]
        self.torrent_track = {
            hash_code: {
                'torrent': self.torrent_track[hash_code]['torrent']
                if hash_code in self.torrent_track
                else Torrent(self.id, file['name'], file['size'], file['piece_size'], file['pieces']),
                
                'peers': self.torrent_track[hash_code]['peers'] + [(peerid, peerip, peerport)]
                if hash_code in self.torrent_track
                else [(peerid, peerip, peerport)],
            }
            for hash_code, file in zip(hash_codes, files)
        }

        
        
peer_msg_new_files = {
    "id": "peer1",
    "ip": "192.168.1.10",
    "port": 6881,
    "file_info": [
        {
            "name": "file1.txt",
            "size": 100,
            "piece_size": 10,
            "pieces": ["hash1", "hash2"]
        },
        {
            "name": "file2.txt",
            "size": 200,
            "piece_size": 20,
            "pieces": ["hash3", "hash4"]
        }
    ]
}

peer_msg_existing_files = {
    "id": "peer2",
    "ip": "192.168.1.11",
    "port": 6882,
    "file_info": [
        {
            "name": "file1.txt",
            "size": 100,
            "piece_size": 10,
            "pieces": ["hash1", "hash2"]
        }
    ]
}

peer_msg_mixed_files = {
    "id": "peer3",
    "ip": "192.168.1.12",
    "port": 6883,
    "file_info": [
        {
            "name": "file1.txt",
            "size": 100,
            "piece_size": 10,
            "pieces": ["hash1", "hash2"]
        },
        {
            "name": "file3.txt",
            "size": 300,
            "piece_size": 30,
            "pieces": ["hash5", "hash6"]
        }
    ]
}

        
tracker = Tracker("1.1.1.1", 4567)
tracker.parse_node_submit_info(peer_msg_new_files)
tracker.parse_node_submit_info(peer_msg_existing_files)
tracker.parse_node_submit_info(peer_msg_mixed_files)
print(json.dumps(tracker.torrent_track, indent=4, default=lambda o: o.to_dict()))