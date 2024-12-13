import json
import math
import socket
from prettytable import PrettyTable
from config import PEER_IP, PIECE_SIZE
from handlers.create_sample_file_handler import create_sample_file
from handlers.utils import check_local_files, create_table, load_file_chunks


def fetch(client_socket, file_name, peer_port):
    peers_hostname = socket.gethostname()

    if check_local_files(file_name):
        pieces = load_file_chunks(file_name)
        print(f"File {file_name} already exists locally with {len(pieces)} pieces:")
        print(create_table(pieces, False))
    else: print(f"File {file_name} didn't exist locally")

    print(f"Fetching status file: '{file_name}' from server...")

    command = {
        "action": "fetch",
        "peers_ip":PEER_IP,
        "peers_port":peer_port,
        "peers_hostname":peers_hostname,
        "file_name": file_name,
    }
    try:
        client_socket.sendall(json.dumps(command).encode() + b'\n')
        response = client_socket.recv(4096).decode()
        server_response = json.loads(response)

        if "file_size" in server_response:
            file_size = server_response["file_size"]
            num_chunks = math.floor(file_size / PIECE_SIZE)
            if check_local_files(file_name) == False:
                print(f"The file '{file_name}' does not exist locally. Creating the file now...")
                create_sample_file(file_name, num_chunks, missing_chunk_probability=1.0)
                print(f"'{file_name}' created with {num_chunks} chunks.")
            
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