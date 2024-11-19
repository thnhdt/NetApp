import time
import threading
from handlers.user_input_handler import process_input
from config import HOST_IP, HOST_PORT, PEER_IP, PEER_PORT
from handlers.terminate_handler import get_terminate_flag, set_terminate_flag
from handlers.connect_handler import connect_to_server, disconnect_from_server, start_peer_server

if __name__ == "__main__":
    client_socket = None

    try:
        client_socket = connect_to_server(HOST_IP, HOST_PORT)
        server_thread = threading.Thread(target=start_peer_server, args=(PEER_IP, PEER_PORT))
        server_thread.start()
        time.sleep(1)

        print("Please type your command (publish <file_name> | fetch <file_name> | download <file_name> | create <file_name> <num_chunks> | get_peers | exit)\n")
        while not get_terminate_flag():
            cmd = input("Command: ")
            process_input(cmd, client_socket)

    except KeyboardInterrupt:
        set_terminate_flag(True)
        if client_socket:
            disconnect_from_server(client_socket)
        print('\nPeer stopped by user.')
    except Exception as e:
        set_terminate_flag(True)
        if client_socket:
            disconnect_from_server(client_socket)
        print(f"An error occurred: {e}")
        print("Connection closed automatically.")
    finally:
        print("Peer stopped and resources cleaned up.")