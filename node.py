import socket
import sys
import time
import threading
from handlers.user_input_handler import process_input
from config import PEER_IP, PEER_PORT_MIN, PEER_PORT_MAX
from handlers.terminate_handler import get_terminate_flag, set_terminate_flag
from handlers.connect_handler import connect_to_server, disconnect_from_server, start_peer_server

def is_port_in_use(port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind((PEER_IP, port))
        s.close()
        return False
    except socket.error:
        return True

def get_available_port(start_port):
    port = start_port
    while port <= PEER_PORT_MAX:
        if not is_port_in_use(port):
            return port
        port += 1
    raise Exception("No available ports in the range!")

if __name__ == "__main__":
    client_socket = None
    available_peer_port = PEER_PORT_MIN

    try:
        HOST_IP = sys.argv[1] if len(sys.argv) > 1 else '192.168.150.1' 
        HOST_PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 12345
        client_socket = connect_to_server(HOST_IP, HOST_PORT)
        
        available_peer_port = get_available_port(available_peer_port)

        server_thread = threading.Thread(target=start_peer_server, args=(PEER_IP, available_peer_port))
        server_thread.start()
        time.sleep(1)

        print("Please type your command (publish <file_name> | fetch <file_name> | download <file_name> | create <file_name> <num_chunks> | get_peers | exit)\n")
        while not get_terminate_flag():
            cmd = input("Command: ")
            process_input(cmd, client_socket, peer_port=available_peer_port)

    except KeyboardInterrupt:
        set_terminate_flag(True)
        if client_socket:
            disconnect_from_server(client_socket, peer_port=available_peer_port)
        print('\nPeer stopped by user.')
    except Exception as e:
        set_terminate_flag(True)
        if client_socket:
            disconnect_from_server(client_socket, peer_port=available_peer_port)
        print(f"An error occurred: {e}")
        print("Connection closed automatically.")
    finally:
        print("Peer stopped and resources cleaned up.")