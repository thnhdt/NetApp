import os
import shlex
import socket
from config import PEER_IP, PEER_PORT, PIECE_SIZE, STORAGE_PATH
from handlers.utils import create_table, generate_info_hash, load_file_chunks

def handle_publish_piece(client_socket, file_name, pieces, file_size, file_hash):
    print(f"File {file_name} has {len(pieces)} pieces:")
    print(create_table(pieces))

    user_input_num_piece = input(f"Please select piece numbers to publish (e.g., 1 3 5): ")
    num_order_in_file = shlex.split(user_input_num_piece)

    selected_chunks = []
    for i in num_order_in_file:
        try:
            index = int(i) - 1
            if pieces[index]:
                selected_chunks.append(index)
                print(f"Selected Piece {i}: {pieces[index].strip()}")
            else:
                print(f"Piece {i} is empty and cannot be selected.")
        except (ValueError, IndexError):
            print(f"Invalid piece number: {i}")

    if file_hash:
        publish_piece_file(client_socket, file_name, file_size, file_hash, selected_chunks)
    else:
        print("No valid pieces selected.")

def publish_piece_file(client_socket, file_name, file_size, file_hash, selected_chunks):
    peers_hostname = socket.gethostname()
    command = {
        "action": "publish",
        "peers_ip":PEER_IP,
        "peers_port":PEER_PORT,
        "peers_hostname":peers_hostname,
        "file_name": file_name,
        "file_size": file_size,
        "file_hash": file_hash,
        "piece_size": PIECE_SIZE,
        "num_order_in_file": selected_chunks,
    }
    print(f"Send to server: {command}")
    print("Publish selected pieces successfully!")
    # try:
    #     client_socket.sendall(json.dumps(command).encode() + b'\n')
    #     response = client_socket.recv(4096).decode()
    #     print("Server response:", response)
    # except socket.error as e:
    #     print(f"Error while publishing file pieces: {e}")
    
def publish(client_socket, file_name):
    file_path = os.path.join(STORAGE_PATH, file_name)
    if not os.path.exists(file_path):
        print(f"File '{file_name}' does not exist in storage.")
        return

    pieces = load_file_chunks(file_name)
    file_size = len(pieces) * PIECE_SIZE
    file_hash = generate_info_hash(file_path, hash_algorithm='sha1')

    if not pieces:
        print(f"No pieces found for file '{file_name}'.")
        return

    handle_publish_piece(client_socket, file_name, pieces, file_size, file_hash)