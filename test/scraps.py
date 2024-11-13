def split_file_into_pieces(file_path):
    CHUNK_SIZE = 512 * 1024  # 512 KB
    pieces = []  # List to store the chunks

    with open(file_path, 'rb') as file:
        while True:
            # Read a chunk of 512 KB
            chunk = file.read(CHUNK_SIZE)
            
            # Break if we've reached the end of the file
            if not chunk:
                break

            # Add the chunk to the list
            pieces.append(chunk)

    return pieces

# Example usage
file_path = 'test.txt'  # Replace with your actual file path
pieces = split_file_into_pieces(file_path)

print(f"Total number of pieces: {len(pieces)}")
for i, piece in enumerate(pieces):
    print(f"Piece {i + 1}: {len(piece)} bytes")
