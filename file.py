class FileMan:
    """The main class for managing all download/upload at a Peer"""
    def __init__(self) -> None:
        self.downloaded = 0 # total bytes downloaded
        self.uploaded = 0   # total bytes uploaded


class Metainfo:
    """represent a file object on node"""
    def __init__(self, tracker_ip: str) -> None:
        self.tracker_ip = tracker_ip
        self.piece_len = 512 * 1024 # 512KB
        self.piece_count = 0
        self.piece_list = {}
        
        
    def read_from(self, filepath):
        # TODO: read data from a file into a file object, in chunks of 512KB
        pass


class Piece:
    def __init__(self, filename: str, index: int, data: bytes = b'') -> None:
        self.filename = filename # name of the file
        self.index = index # piece index for reassembling
        self.data = data # data contained in a piece