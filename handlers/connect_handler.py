import json
import socket
from handlers.terminate_handler import get_terminate_flag
from config import PEER_IP
from handlers.utils import check_local_files, check_local_piece_files, load_file_chunk

def connect_to_server(host_ip, host_port):
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((host_ip, host_port))
        print(f"Connected to server {host_ip}:{host_port}")
        return client_socket
    except socket.error as e:
        print(f"Error connecting to server: {e}")
        return None

def disconnect_from_server(client_socket, peer_port):
    if client_socket:
        command = {
            "action": "exit",
            "peers_ip": PEER_IP,
            "peers_port": peer_port,
            "peers_hostname": socket.gethostname(),
        }
        try:
            client_socket.sendall(json.dumps(command).encode() + b'\n')
            client_socket.close()
            print("Disconnected from server.")
        except socket.error as e:
            print(f"Error disconnecting from server: {e}")

def connect_to_peer(peer_ip, peer_port):
    try:
        peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        peer_socket.connect((peer_ip, peer_port))
        
        peer_hostname = socket.gethostbyaddr(peer_ip)[0]
        print(f"Connected to peer ({peer_ip}:{peer_port})")
        
        return peer_socket
    except socket.error as e:
        print(f"Error connecting to peer: {e}")
        return None
    except socket.herror:
        print(f"Connected to peer {peer_ip}:{peer_port}")
        return peer_socket

def disconnect_from_peer(peer_socket):
    if peer_socket:
        try:
            peer_ip, peer_port = peer_socket.getpeername()
            print(f"Disconnected from peer ({peer_ip}:{peer_port})")  
            peer_socket.close()
        except socket.error as e:
            print(f"Error disconnecting from peer: {e}")

def start_peer_server(peer_ip, peer_port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as peer_socket:
        peer_socket.bind((peer_ip, peer_port))
        peer_socket.listen(5)
        print(f"Peer server started successfully! Listening on {peer_ip}:{peer_port}")
        while not get_terminate_flag():
            try:
                peer_socket.settimeout(1)
                client_socket, client_address = peer_socket.accept()
                print(f"Connected to {client_address}")

                with client_socket:
                    data = client_socket.recv(4096)
                    if data:
                        try:
                            request_data = json.loads(data.decode('utf-8'))
                            handleReq(client_socket, request_data)
                        except json.JSONDecodeError:
                            response = {"status": "error", "message": "Invalid JSON format."}
                            client_socket.sendall(json.dumps(response).encode() + b'\n')

            except socket.timeout:
                continue

def handleReq(client_socket, request_data):
    if request_data.get("action") == "download_chunk":
        file_name = request_data.get("file_name")
        chunk_indices = request_data.get("chunk_indices")

        if not file_name or not chunk_indices:
            response = {"status": "error", "message": "Invalid request. File name or chunk indices missing."}
            client_socket.sendall(json.dumps(response).encode() + b'\n')
            return

        if not check_local_files(file_name):
            response = {"status": "error", "message": f"File '{file_name}' not found on the server."}
            client_socket.sendall(json.dumps(response).encode() + b'\n')
            return

        local_piece_status = check_local_piece_files(file_name)
        if not local_piece_status:
            response = {"status": "error", "message": f"Chunks for file '{file_name}' are not available."}
            client_socket.sendall(json.dumps(response).encode() + b'\n')
            return

        for chunk_index in chunk_indices:
            try:
                chunk_data_status = local_piece_status[chunk_index] if 0 <= chunk_index < len(local_piece_status) else None
                if chunk_data_status != 1:
                    response = {
                        "status": "error",
                        "message": f"Chunk {chunk_index} of '{file_name}' is missing."
                    }
                    client_socket.sendall(json.dumps(response).encode() + b'\n')
                    continue
                chunk_data=load_file_chunk(file_name, chunk_index)
                response = {
                    "status": "success",
                    "chunk_index": chunk_index,
                    "data": chunk_data
                }
                print(response)
                client_socket.sendall(json.dumps(response).encode() + b'\n')

            except (OSError, ValueError) as e:
                response = {
                    "status": "error",
                    "message": f"Error reading chunk {chunk_index} from '{file_name}': {str(e)}"
                }
                client_socket.sendall(json.dumps(response).encode() + b'\n')


    else:
        response = {"status": "error", "message": "Unsupported action."}
        client_socket.sendall(json.dumps(response).encode() + b'\n')