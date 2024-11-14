import json
import math
import random
import socket
import threading
from queue import Queue
from handlers.test import mock_server_response
from handlers.utils import check_local_files, load_file_status, update_file_status
from config import PEER_IP, PEER_PORT, PIECE_SIZE
from concurrent.futures import ThreadPoolExecutor
from handlers.create_sample_file_handler import store_file_chunk
from handlers.connect_handler import connect_to_peer, disconnect_from_peer

def download(client_socket, file_name):
    if not check_local_files(file_name):
        print(f"The file '{file_name}' does not exist locally. Please fetch it first using the fetch function.")
        return

    command = {
        "action": "fetch",
        "peers_ip": PEER_IP,
        "peers_port": PEER_PORT,
        "peers_hostname": socket.gethostname(),
        "file_name": file_name,
    }

    # try:
    #     client_socket.sendall(json.dumps(command).encode() + b'\n')
    #     response = client_socket.recv(4096).decode()
    #     server_response = json.loads(response)
    # except (socket.error, json.JSONDecodeError) as e:
    #     print(f"Error while downloading file info: {e}")
    #     return
    try:
        # Thay thế đoạn gửi và nhận từ socket bằng mock response
        response = mock_server_response()
        server_response = json.loads(response)
    except json.JSONDecodeError as e:
        print(f"Error while decoding mock server response: {e}")
        return

    file_size = server_response["file_size"]
    num_chunks = math.ceil(file_size / PIECE_SIZE)
    pieces_to_download = list(range(num_chunks))

    while True:
        user_input = input(f"Available chunks: {len(pieces_to_download)}. Select chunks to download ('1 3 5' or 'all'): ").strip().lower()
        if user_input == "all":
            selected_chunks = pieces_to_download
            break
        else:
            try:
                selected_chunks = [int(chunk.strip()) - 1 for chunk in user_input.split()]
                
                if any(chunk < 0 or chunk >= len(pieces_to_download) for chunk in selected_chunks):
                    print(f"Invalid input. Please select numbers between 1 and {len(pieces_to_download)}.")
                    continue
                
                break
            except KeyboardInterrupt:
                break
            except ValueError:
                print("Invalid input. Please enter numbers separated by spaces or 'all' to download all chunks.")

    print(f"Starting download for {len(selected_chunks)} chunks...")
    download_chunks(file_name, selected_chunks, server_response['peers_info'], num_chunks)

def download_chunks(file_name, chunks, peers_info, num_of_pieces):
    piece_download_lock = threading.Lock()
    piece_has_been_downloaded = [0 for _ in range(num_of_pieces)]
    chunk_queue = Queue()

    for chunk_index in chunks:
        chunk_queue.put(chunk_index)

    chunk_peers_map = {}
    for chunk_index in chunks:
        peers_with_chunk = []
        for peer in peers_info:
            if chunk_index in peer.get("num_order_in_file", []):
                peers_with_chunk.append((peer['peers_ip'], peer['peers_port']))
        random.shuffle(peers_with_chunk)
        chunk_peers_map[chunk_index] = peers_with_chunk

    def download_chunk():
        while not chunk_queue.empty():
            chunk_index = chunk_queue.get()
            peers = chunk_peers_map.get(chunk_index, [])
            download_successful = False

            for _ in range(len(peers)):
                if not peers:
                    break 

                ip, port = peers.pop(0)
                peers.append((ip, port))

                with piece_download_lock:
                    if piece_has_been_downloaded[chunk_index]:
                        download_successful = True
                        break

                try:
                    success = connect_to_peer_and_download_file_chunk(ip, port, file_name, [chunk_index])
                    if success:
                        with piece_download_lock:
                            piece_has_been_downloaded[chunk_index] = 1
                            download_successful = True
                except Exception as e:
                    print(f"Error downloading chunk {chunk_index + 1} from {ip}:{port}: {e}")

            if not download_successful:
                print(f"Failed to download chunk {chunk_index + 1}. No more peers available.")

            chunk_queue.task_done()

    with ThreadPoolExecutor(max_workers=5) as executor:
        for _ in range(5):
            executor.submit(download_chunk)

    chunk_queue.join()
    current_status = load_file_status()
    if file_name in current_status:
        for chunk_index, has_been_downloaded in enumerate(piece_has_been_downloaded):
            if has_been_downloaded == 1:
                current_status[file_name]["piece_status"][chunk_index] = 1
        update_file_status(file_name, current_status[file_name]["piece_status"])
    print(f"Download completed. Piece status for file {file_name} updated: {current_status[file_name]['piece_status']}")

def connect_to_peer_and_download_file_chunk(ip, port, file_name, chunk_indices):
    peer_socket = connect_to_peer(ip, port)
    if peer_socket is None:
        return False

    try:
        request_data = {
            "action": "download_chunk",
            "file_name": file_name,
            "chunk_indices": chunk_indices
        }
        peer_socket.sendall(json.dumps(request_data).encode() + b'\n')

        for chunk_index in chunk_indices:
            response = peer_socket.recv(4096).decode()
            response_data = json.loads(response)

            if response_data.get("status") != "success":
                print(f"Failed to download chunk {chunk_index + 1} from {ip}:{port}: {response_data.get('message', 'Unknown error')}")
                continue

            chunk_data = response_data.get("data")
            if chunk_data:
                store_file_chunk(file_name, chunk_index, chunk_data)
                print(f"Successfully downloaded chunk {chunk_index + 1} from {ip}:{port}")
            else:
                print(f"Chunk data for chunk {chunk_index + 1} is empty from {ip}:{port}.")

    except (socket.error, json.JSONDecodeError) as e:
        print(f"Error while downloading chunks {chunk_indices} from {ip}:{port}: {e}")
    finally:
        disconnect_from_peer(peer_socket)
        return True