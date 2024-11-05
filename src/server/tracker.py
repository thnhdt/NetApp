# tracker.py
import socket
import threading

# Data to track the files and peers
# file_pieces is a dictionary that holds file names and which peers have them
file_pieces = {}

def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected.")
    try:
        while True:
            data = conn.recv(1024).decode('utf-8')
            if data == "DISCONNECT":
                break
            else:
                # Expected format: FILE_REQUEST:file_name
                command, file_name = data.split(':')
                if command == "FILE_REQUEST":
                    if file_name in file_pieces:
                        conn.send(str(file_pieces[file_name]).encode('utf-8'))
                    else:
                        conn.send("NO_PEERS".encode('utf-8'))
                elif command == "REGISTER":
                    # Format: REGISTER:file_name:peer_ip
                    _, file_name, peer_ip = data.split(':')
                    if file_name not in file_pieces:
                        file_pieces[file_name] = []
                    file_pieces[file_name].append(peer_ip)
                    conn.send("REGISTERED".encode('utf-8'))
    except:
        pass
    conn.close()

def start_tracker():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('localhost', 5555))
    server.listen()
    print("[TRACKER] Tracker is listening on port 5555...")
    
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")

if __name__ == "__main__":
    start_tracker()
