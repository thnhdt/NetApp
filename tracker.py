# Initiate a server process
# add node
# send list node to client
import socket
from threading import Thread
import bencodepy
import json
import threading
import time
import sys

peer_dict = {}
lock = threading.Lock()

def new_connection(conn, addr):
    print(f"New connection from {addr}")
    while True:
        data = conn.recv(1024).decode('utf-8');
        if not data:
            time.sleep(1)  # Wait for 100ms before the next iteration
            continue
        message = json.loads(data)
        print(f"Received message from {addr}: {message}")
        handle_message(conn, message)
        print(message)

def handle_message(conn, message):
    lock.acquire()
    try:
        if message['action'] == 'publish':
            handle_publish(conn, message)
        elif message['action'] == 'get_peers':
            handle_get_peers(conn, message)
        elif message['action'] == 'exit':
            handle_exit(message)
        else:
            response = {"status": "error", "message": "Unknown action"}
            conn.send(json.dumps(response).encode())
    finally:
        lock.release()

def handle_publish(conn, message):
    peers_ip = message['peers_ip']
    peers_port = message['peers_port']
    peers_hostname = message['peers_hostname']
    file_name = message['file_name']
    file_size = message['file_size']
    file_hash = message['file_hash']
    piece_size = message['piece_size']
    num_order_in_file = message['num_order_in_file']

    # Store the published file information in peer_dict
    if file_hash not in peer_dict:
        peer_dict[file_hash] = {
            "file_name": file_name,
            "file_size": file_size,
            "piece_size": piece_size,
            "peers": {}
        }

    # Add the peer information
    peer_id = f"{peers_ip}:{peers_port}"
    peer_dict[file_hash]["peers"][peer_id] = {
        "hostname": peers_hostname,
        "ip": peers_ip,
        "port": peers_port,
        "num_order_in_file": num_order_in_file
    }

    print(f"Updated peer_dict for file {file_name}: {peer_dict[file_hash]}")

    # Send a response back to the client
    response = {"status": "success", "message": "File published successfully"}
    conn.send(json.dumps(response).encode())

def handle_get_peers(conn, message):
    file_hash = message['file_hash']
    if file_hash in peer_dict:
        response = {'peers': peer_dict[file_hash]['peers']}
    else:
        response = {'peers': {}}
    conn.send(json.dumps(response).encode())

def handle_exit(message):
    peer_id = message['peer_id']
    file_hash = message['file_hash']
    if file_hash in peer_dict and peer_id in peer_dict[file_hash]['peers']:
        del peer_dict[file_hash]['peers'][peer_id]
        print(f"Peer {peer_id} has exited. Updated peer_dict: {peer_dict}")


def get_host_default_interface_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP connection
    try:
       s.connect(('8.8.8.8', 1)) # This connects the socket to the remote address 8.8.8.8 (Google's public DNS server) on port 1.
       ip = s.getsockname()[0]
    except Exception:
       ip = '127.0.0.1'
    finally:
       s.close()
    return ip

#starting server
def start_server(host, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)
    print(f"Server listening on {host}:{port}")

    while True:
        client_socket, client_address = server_socket.accept()
        # Create a new thread for each client connection
        client_thread = threading.Thread(target=new_connection, args=(client_socket, client_address))
        client_thread.start()
        print(f"Active connections: {threading.active_count() - 1}")


#---SERVER COMMAND---
def server_command_shell():
    while True:
        cmd_input = input("Server command: ")
        cmd_parts = cmd_input.split()
        if cmd_parts:
            action = cmd_parts[0]
            if action == "discover" and len(cmd_parts) == 2:
                print("Implementing.")
                id = cmd_parts[1]
                thread = threading.Thread(target=discover_files, args=(id,))
                thread.start()
            elif action == "ping" and len(cmd_parts) == 2:
                id = cmd_parts[1]
                thread = threading.Thread(target=ping_host, args=(id,))
                thread.start()
            elif action == "exit":
                break
            else:
                print("Unknown command or incorrect usage.")

#discover
def discover_files(peers_hostname):
    files = clients_files(peers_hostname)
    print(f"Files on {peers_hostname}: {files}")

def clients_files(peers_hostname):
    peer_info = get_peer_ip_by_hostname(peer_dict, peers_hostname)
    print(peer_info)
    peer_ip = peer_info["ip"]
    if peer_ip:
        peer_port = peer_info["port"]
        peer_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        peer_sock.connect((peer_ip, peer_port))
        request = {'action': 'request_file_list'}
        #! conn_handler -> 'action': 'request_file_list'
        peer_sock.sendall(json.dumps(request).encode() + b'\n')
        response = json.loads(peer_sock.recv(4096).decode())
        peer_sock.close()
        if 'files' in response:
            return response['files']
        else:
            return "Error: No file list in response"
    else:
        return "Error: Client not connected"

    
#ping
def ping_host(peers_hostname):
    peer_info = get_peer_ip_by_hostname(peer_dict, peers_hostname)
    print(peer_info)
    peer_ip = peer_info["ip"]
    if peer_ip:
        peer_port = peer_info["port"]
        peer_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        peer_sock.connect((peer_ip, peer_port))
        request = {'action': 'ping'}
        peer_sock.sendall(json.dumps(request).encode() + b'\n')
        response = peer_sock.recv(4096).decode()
        peer_sock.close()
        if response:
            print(f"{peers_hostname} is online!")
    else:
        print(f"{peers_hostname} is not in network")

def get_peer_ip_by_hostname(peer_dict, hostname):
    for file_info in peer_dict.items():
        for peer_info in file_info['peers'].values():
            if peer_info['hostname'] == hostname:
                return peer_info
    return None

if __name__ == "__main__":
    #id = socket.getid()
    hostip = get_host_default_interface_ip()
    port = 65431
    print("Listening on: {}:{}".format(hostip,port))
    server_thread = threading.Thread(target=start_server, args=(hostip, port)) 
    server_thread.start()
    server_command_shell()
    # start_server(hostip, port)
    print("Shutting down server...")
    
    sys.exit(0)



