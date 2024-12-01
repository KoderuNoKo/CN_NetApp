import random

# Example: 10 pieces and 5 peers
num_pieces = 10
peer_bitfields = {
    "peer_1": [1, 0, 1, 1, 0, 0, 1, 0, 1, 0],  # Peer 1 has pieces 1, 3, 4, 6, 8
    "peer_2": [0, 1, 1, 0, 1, 1, 0, 1, 0, 1],  # Peer 2 has pieces 2, 3, 5, 6, 8, 10
    "peer_3": [1, 1, 0, 1, 0, 1, 0, 1, 0, 1],  # Peer 3 has pieces 1, 2, 4, 6, 8, 10
    "peer_4": [1, 0, 0, 1, 1, 0, 1, 1, 0, 0],  # Peer 4 has pieces 1, 4, 6, 7
    "peer_5": [0, 1, 0, 0, 1, 1, 1, 0, 0, 1],  # Peer 5 has pieces 2, 5, 6, 10
}

# Function to calculate how many peers have each piece
def calculate_piece_availability(peer_bitfields):
    piece_availability = [0] * num_pieces  # Initialize the availability count for each piece
    for bitfield in peer_bitfields.values():
        for i, has_piece in enumerate(bitfield):
            if has_piece:
                piece_availability[i] += 1
    return piece_availability

# Function to select peers as evenly as possible
def select_peers_evenly(peer_bitfields, piece_availability):
    # Create a list to track which pieces have been assigned to each peer
    peer_piece_count = {peer: 0 for peer in peer_bitfields}  # Initialize count of pieces each peer has
    
    # List to track which pieces need to be assigned
    pieces_needed = list(range(num_pieces))  # All piece indexes
    
    # Track available peers for each piece
    piece_peers = {i: [] for i in range(num_pieces)}
    for peer, bitfield in peer_bitfields.items():
        for i, has_piece in enumerate(bitfield):
            if has_piece:
                piece_peers[i].append(peer)
    
    # List to store the selected peers for each piece
    selected_peers_for_pieces = [None] * num_pieces
    
    for piece_index in pieces_needed:
        # Get the list of peers that have this piece
        available_peers = piece_peers[piece_index]
        
        # Sort peers by how many pieces they already have (select the peer with the least pieces)
        available_peers.sort(key=lambda peer: peer_piece_count[peer])
        
        # Select the peer with the least number of pieces already assigned
        selected_peer = available_peers[0]
        
        # Assign the selected peer to this piece
        selected_peers_for_pieces[piece_index] = selected_peer
        
        # Update the peer's piece count
        peer_piece_count[selected_peer] += 1

        print(f"Piece {piece_index + 1} is assigned to {selected_peer}.")
    
    return selected_peers_for_pieces

# Calculate piece availability
piece_availability = calculate_piece_availability(peer_bitfields)

# Select peers evenly
selected_peers_for_pieces = select_peers_evenly(peer_bitfields, piece_availability)

# Print the final assignments of peers to pieces
print("\nFinal selection of peers for each piece:")
for piece_index, peer in enumerate(selected_peers_for_pieces):
    print(f"Piece {piece_index + 1} is assigned to {peer}.")