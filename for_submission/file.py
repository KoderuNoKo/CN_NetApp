import os
import math
import hashlib
import common
import json

class Piece:
    def __init__(self, index, data: bytes):
        self.index = index
        self.data = data
        self.hash = self.compute_sha1()


    def compute_sha1(self):
        """Compute SHA-1 hash of the piece."""
        sha1 = hashlib.sha1()
        sha1.update(self.data)  # Binary data is hashed directly
        return sha1.hexdigest()  # Return hex digest for consistency


class File_upload:
    def __init__(self, path: str, metainfo=None):
        self.metainfo = metainfo or {}
        self.pieces = []  # Store pieces of the file
        self.path = path
        self.piece_idx_upload = []
        # self.total_hash = b""
        self.__initialize_file_info()


    def __initialize_file_info(self) -> None:
        if os.path.exists(self.path):
            self.metainfo["name"] = os.path.basename(self.path)
            self.metainfo["length"] = os.path.getsize(self.path)
            self.metainfo["piece_size"] = common.PIECE_SIZE  # Default piece size in bytes
            self.metainfo["num_pieces"] = math.ceil(self.metainfo["length"] / self.metainfo["piece_size"])
            self.metainfo["pieces"] = ""  # Concatenated SHA1 hashes for each piece
            self.split_file()
            self.metainfo['total_hash'] = self.hash_metadata()
            self.piece_idx_upload = list(range(self.metainfo["num_pieces"]))
        else:
            raise FileNotFoundError("File '{}' not found!".format(self.path))


    def split_file(self):
        """Split the file into pieces and compute their hashes."""
        with open(self.path, "rb") as file:
            idx = 0
            while True:
                partial_file = file.read(self.metainfo["piece_size"])
                if not partial_file:
                    break
                piece = Piece(idx, partial_file)
                self.pieces.append(piece)
                self.metainfo["pieces"] += piece.hash  # Concatenate SHA1 hashes
                idx += 1
                

    def hash_metadata(self) -> str:
        sorted_dict = json.dumps(self.metainfo, sort_keys=True).encode(common.CODE)

        # Use hashlib to compute the hash
        sha1_hash = hashlib.sha1(sorted_dict).hexdigest()
        return sha1_hash


    def get_metainfo(self) -> dict:
        """Return the file's metadata."""
        return {k: v for k, v in self.metainfo.items() if k != 'pieces'}


    def get_piece_with_index(self, index):
        if 0 <= index < len(self.pieces):
            return self.pieces[index]
        else:
            print ("Piece with index {} is out of range.".format(index))


    def get_bitfield(self):
        """Return a bitfield indicating which pieces are available."""
        bitfield = ""
        for i in range(self.metainfo["num_pieces"]):
            bitfield += "1" if i in self.piece_idx_upload else "0"
        return bitfield

class File_download:
    def __init__(self):
        self.num_piece = None
        self.piece_idx_downloaded = []
        
        
    def set_num_pieces(self, n: int):
        self.num_piece = n
        self.pieces = [None] * n

    def save_complete_file(self, repo, file_name):
        """Save the complete file to the specified repository."""
        if len(self.piece_idx_downloaded) < self.num_piece:
            print("All pieces of the file are not downloaded yet!")
            return None

        file_path = os.path.join(repo, file_name)

        with open(file_path, "wb") as complete_file:
            for piece in sorted(self.pieces, key=lambda p: p.index if p else -1):
                if piece is None:
                    print("Missing Piece {} during save process!".format(piece.index))
                    return
                complete_file.write(piece.data)
                print("Piece {} saved to file '{}'".format(piece.index, file_name))

        print("Complete file saved to '{}'.".format(file_path))

    def add_piece(self, data, index):
        """
        Add a downloaded piece to the list of pieces.
        """
        if 0 <= index < self.num_piece:
            if self.pieces[index] is None:
                piece = Piece(index, data)
                self.pieces[index] = piece
                self.piece_idx_downloaded.append(piece.index)
                print("Piece {} added successfully.".format(piece.index))
            else:
                print("Piece {} already downloaded.".format(index))
        else:
            print("Invalid piece index: {}".format(index))






