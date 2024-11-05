# node.py
import socket
import threading

def connect_to_tracker(file_name):
    tracker_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tracker_socket.connect(('localhost', 5555))
    
    # Request the file from the tracker
    tracker_socket.send(f"FILE_REQUEST:{file_name}".encode('utf-8'))
    peer_data = tracker_socket.recv(1024).decode('utf-8')
    tracker_socket.close()

    if peer_data == "NO_PEERS":
        print(f"[TRACKER] No peers have the file: {file_name}")
        return []
    else:
        print(f"[TRACKER] Peers with file {file_name}: {peer_data}")
        return eval(peer_data)  # Returns a list of peers' IPs

def download_from_peer(peer_ip, file_name):
    peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    peer_socket.connect((peer_ip, 6666))  # Assuming peer listens on port 6666
    peer_socket.send(f"DOWNLOAD:{file_name}".encode('utf-8'))
    
    with open(file_name, 'wb') as f:
        while True:
            data = peer_socket.recv(1024)
            if not data:
                break
            f.write(data)
    
    print(f"[PEER] Downloaded {file_name} from {peer_ip}")
    peer_socket.close()

def handle_peer(conn, addr, file_name):
    print(f"[PEER CONNECTION] {addr} connected for file {file_name}.")
    request = conn.recv(1024).decode('utf-8')
    if request.startswith("DOWNLOAD"):
        with open(file_name, 'rb') as f:
            chunk = f.read(1024)
            while chunk:
                conn.send(chunk)
                chunk = f.read(1024)
    conn.close()

def start_node(file_name, my_ip):
    peer_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    peer_server.bind((my_ip, 6666))
    peer_server.listen()
    
    # Register with the tracker
    tracker_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tracker_socket.connect(('localhost', 5555))
    tracker_socket.send(f"REGISTER:{file_name}:{my_ip}".encode('utf-8'))
    tracker_socket.recv(1024)  # Wait for response
    tracker_socket.close()
    
    print(f"[NODE] Registered {file_name} with tracker.")
    
    def serve_peers():
        while True:
            conn, addr = peer_server.accept()
            threading.Thread(target=handle_peer, args=(conn, addr, file_name)).start()
    
    thread = threading.Thread(target=serve_peers)
    thread.start()

def main():
    file_name = "example_file.txt"  # The file you're sharing
    my_ip = 'localhost'  # Replace with your actual IP
    start_node(file_name, my_ip)

    # Download a file from peers
    peers = connect_to_tracker(file_name)
    if peers:
        for peer_ip in peers:
            download_from_peer(peer_ip, file_name)

if __name__ == "__main__":
    main()
