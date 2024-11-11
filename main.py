import os
import json
import math
import shlex
import time
import socket
import hashlib
import threading
from queue import Queue
from dotenv import load_dotenv
from prettytable import PrettyTable
from helper import create_sample_file

terminate_flag = False

load_dotenv()
STORAGE_PATH = "storage"
FILE_STATUS_PATH = "file_status.json"
HOST_IP = os.getenv('HOST_IP', '127.0.0.1')
HOST_PORT = int(os.getenv('HOST_PORT', '65431'))
PEER_IP = os.getenv('PEER_IP', '127.0.0.1')
PEER_PORT = int(os.getenv('PEER_PORT', '65432'))
PIECE_SIZE = int(os.getenv('PIECE_SIZE', '512'))

# Tạo thư mục lưu trữ nếu chưa có
if not os.path.exists(STORAGE_PATH):
    os.makedirs(STORAGE_PATH)

# --- Connect Handler --- #
def connect_to_server(host_ip, host_port):
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((host_ip, host_port))
        print(f"Connected to server {host_ip}:{host_port}")
        return client_socket
    except socket.error as e:
        print(f"Error connecting to server: {e}")
        return None

def disconnect_from_server(client_socket):
    if client_socket:
        try:
            client_socket.close()
            print("Disconnected from server.")
        except socket.error as e:
            print(f"Error disconnecting from server: {e}")

def start_peer_server(peer_ip, peer_port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as peer_socket:
        peer_socket.bind((peer_ip, peer_port))
        peer_socket.listen(5)
        print(f"Peer 1 started successfully!\nListening on {peer_ip}:{peer_port}")
        print("Please type your command (publish file_name | fetch file_name | download file_name | create file_name num_chunks | exit)\n")

        while not terminate_flag:
            try:
                peer_socket.settimeout(1)
                client_socket, client_address = peer_socket.accept()
                print(f"Connected to {client_address}")
                # handle_request(client_socket)
            except socket.timeout:
                continue

# --- Helper --- #
def load_file_status():
    if os.path.exists(FILE_STATUS_PATH):
        with open(FILE_STATUS_PATH, "r") as file:
            return json.load(file)
    return {}

def save_file_status(file_status):
    with open(FILE_STATUS_PATH, "w") as file:
        json.dump(file_status, file, indent=4)

def check_local_files(file_name):
    file_status = load_file_status()
    return True if file_name in file_status else False

def check_local_piece_files(file_name):
    file_status = load_file_status()
    if file_name in file_status:
        return file_status[file_name]["piece_status"]
    return False

def create_table(pieces, select = True):
    table = PrettyTable()
    table.field_names = ["Piece Number", "Piece Status"]
    
    for i, piece in enumerate(pieces):
        piece_status = piece.strip() if piece else "(empty) - Cannot select" if select == True else "(empty)"
        table.add_row([i + 1, piece_status])

    return table

def generate_info_hash(file_path, hash_algorithm = 'sha1'):
    if hash_algorithm == 'sha1':
        hash_func = hashlib.sha1()
    elif hash_algorithm == 'sha256':
        hash_func = hashlib.sha256()
    else:
        raise ValueError("Unsupported hash algorithm. Use 'sha1' or 'sha256'.")

    with open(file_path, 'rb') as file:
        while chunk := file.read(4096):
            hash_func.update(chunk)

    return hash_func.hexdigest()

# --- Storage & File Update --- #
def update_file_status(file_name, piece_status):
    file_status = load_file_status()
    
    if file_name not in file_status:
        file_status[file_name] = {
            "piece_status": piece_status,
            "total_pieces": len(piece_status),
        }
    else:
        file_status[file_name]["piece_status"] = piece_status
    
    save_file_status(file_status)

def store_file_chunk(file_name, chunk_index, data, fill_missing=False):
    file_path = os.path.join(STORAGE_PATH, file_name)
    
    if not os.path.exists(file_path):
        with open(file_path, "wb") as f:
            f.write(b"")
    
    with open(file_path, "r+b") as f:
        f.seek(chunk_index * (PIECE_SIZE + 1))
        if fill_missing:
            f.write((b"\x00" * PIECE_SIZE) + b"\n")
        else:
            f.write(data.encode('latin1') + b"\n")

def load_file_chunks(file_name):
    chunk_data = []
    file_path = os.path.join(STORAGE_PATH, file_name)

    if not os.path.exists(file_path):
        return []

    with open(file_path, "rb") as f:
        total_size = os.path.getsize(file_path)
        total_chunks = math.ceil(total_size / (PIECE_SIZE + 1))

        for chunk_index in range(total_chunks):
            f.seek(chunk_index * (PIECE_SIZE + 1))
            data = f.read(PIECE_SIZE)
            chunk_data.append(data.decode('latin1').rstrip('\x00'))

    return chunk_data

# --- Helper Functions for Publish --- #
def handle_publish_piece(client_socket, file_name, pieces, file_size, file_hash, piece_size):
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
        publish_piece_file(client_socket, file_name, file_size, file_hash, piece_size, selected_chunks)
    else:
        print("No valid pieces selected.")

def publish_piece_file(client_socket, file_name, file_size, file_hash, piece_size, selected_chunks):
    peers_hostname = socket.gethostname()
    command = {
        "action": "publish",
        "peers_ip":PEER_IP,
        "peers_port":PEER_PORT,
        "peers_hostname":peers_hostname,
        "file_name": file_name,
        "file_size": file_size,
        "file_hash": file_hash,
        "piece_size": piece_size,
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

# --- Publish handler --- #
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

    handle_publish_piece(client_socket, file_name, pieces, file_size, file_hash, PIECE_SIZE)

# --- Fetch handler --- #
def fetch(client_socket, file_name):
    file_status = load_file_status()
        
    if check_local_files(file_name):
        pieces = load_file_chunks(file_name)
        print(f"File {file_name} already exists locally with {len(pieces)} pieces:")
        print(create_table(pieces, False))

    print(f"Fetching status file: '{file_name}' from server...")

    command = {
        "action": "fetch",
        "file_name": file_name,
    }
    try:
        client_socket.sendall(json.dumps(command).encode() + b'\n')
        response = client_socket.recv(4096).decode()
        server_response = json.loads(response)

        if "file_size" in server_response:
            file_size = server_response["file_size"]
            num_chunks = math.floor(file_size / PIECE_SIZE)
            print(f"File size: {file_size} bytes, Total chunks: {num_chunks}")
            
            if 'peers_info' in server_response:
                peers_info = server_response['peers_info']
                peer_table = PrettyTable()
                peer_table.field_names = ["Number", "Peer Hostname", "Peer IP", "Peer Port", "File Hash", "File Size", "Piece Size", "Piece Order"]

                for peer_info in peers_info:
                    peer_table.add_row([
                        peer_info['num_order_in_file'],
                        peer_info['peers_hostname'],
                        peer_info['peers_ip'],
                        peer_info['peers_port'],
                        peer_info['file_hash'],
                        peer_info['file_size'],
                        peer_info['piece_size'],
                        peer_info['num_order_in_file']
                    ])
                print(f"Hosts with the file {file_name}:\n{peer_table}")
            else:
                print("No peers have the file.")
        
        else:
            print("No file size returned from server.")

    except socket.error as e:
        print(f"Error while fetching file: {e}")

# --- UserInput handler --- #
def process_input(cmd, client_socket):
    global terminate_flag

    params = cmd.split()

    if len(params) == 0:
        print("Please type your command (publish file_name | fetch file_name | create file_name num_chunks | exit)\n")
        return

    try:
        if params[0] == 'exit':
            terminate_flag = True

            if client_socket:
                disconnect_from_server(client_socket)

            print("Stopping the server...")
        elif params[0] == 'create':
            if len(params) == 1:
                print('Argument file_name is required')
                return
            elif len(params) == 2:
                print('Argument num_chunks is required')
                return
            create_sample_file(params[1], int(params[2]))
        elif params[0] == 'publish':
            if len(params) == 1:
                print('Argument file_name is required')
                return
            publish(client_socket, params[1])
        elif params[0] == 'fetch':
            if len(params) == 1:
                print('Argument file_name is required')
                return
            fetch(client_socket, params[1])
        else:
            print('Invalid command (publish file_name | fetch file_name | download file_name | exit)')
    except IndexError:
        print('Invalid command (publish file_name | fetch file_name | download file_name | exit)')

if __name__ == "__main__":
    client_socket = None

    try:
        client_socket = connect_to_server(HOST_IP, HOST_PORT)

        server_thread = threading.Thread(target=start_peer_server, args=(PEER_IP, PEER_PORT))
        server_thread.start()
        time.sleep(1)

        while not terminate_flag:
            cmd = input("Command: ")
            process_input(cmd, client_socket)

    except KeyboardInterrupt:
        terminate_flag = True

        if client_socket:
            disconnect_from_server(client_socket)

        print('\nPeer stopped by user.')

    finally:
        print("Peer stopped and resources cleaned up.")