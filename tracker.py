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
terminate_flag = False

def get_terminate_flag():
    return terminate_flag

def set_terminate_flag(value: bool):
    global terminate_flag
    terminate_flag = value

def new_connection(conn, addr):
    print(f"New connection from {addr}")
    while not get_terminate_flag():
        data = conn.recv(1024).decode('utf-8');
        if not data:
            time.sleep(1)
            continue
        message = json.loads(data)
        handle_message(conn, message)

def handle_message(conn, message):
    lock.acquire()
    try:
        if message['action'] == 'publish':
            handle_publish(conn, message)
        elif message['action'] == 'get_peers':
            handle_get_peers(conn, message)
        elif message['action'] == 'fetch':
            handle_fetch(conn, message)
        elif message['action'] == 'exit':
            handle_exit(conn, message)
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

    if file_hash not in peer_dict:
        peer_dict[file_hash] = {
            "file_name": file_name,
            "file_size": file_size,
            "piece_size": piece_size,
            "peers": {}
        }

    peer_id = f"{peers_ip}:{peers_port}"
    peer_dict[file_hash]["peers"][peer_id] = {
        "hostname": peers_hostname,
        "ip": peers_ip,
        "port": peers_port,
        "num_order_in_file": num_order_in_file
    }

    print(f"Updated peer_dict for file {file_name}: {peer_dict[file_hash]}")
    response = {"status": "success", "message": "File published successfully"}
    conn.send(json.dumps(response).encode())

def handle_fetch(conn, message):
    file_hash = find_by_file_name(message['file_name'])
    if file_hash:
        peers_info = peer_dict[file_hash]['peers']
        res_peers_info = [
            {
                'num_order_in_file': peer['num_order_in_file'],
                'peers_hostname': peer['hostname'],
                'peers_ip': peer['ip'],
                'peers_port': peer['port'],
                'file_hash': file_hash,
                'file_size': peer_dict[file_hash]['file_size'],
                'piece_size': peer_dict[file_hash]['piece_size']
            }
            for peer in peers_info.values()
        ]
        response = {
            "status": "success",
            "file_size": peer_dict[file_hash]['file_size'],
            "peers_info": res_peers_info
        }
    else:
        response = {"status": "error", "message": "File not found"}
        conn.send(json.dumps(response).encode())

def find_by_file_name(file_name):
    for file_hash, details in peer_dict.items():
        if details['file_name'] == file_name:
            return file_hash
    return None

def handle_get_peers(conn, message):
    file_hash = find_by_file_name(message['file_name'])
    if file_hash in peer_dict:
        response = {'peers': peer_dict[file_hash]['peers']}
    else:
        response = {}
    conn.send(json.dumps(response).encode())

def handle_exit(conn, message):
    ip = message['peers_ip']
    port = message['peers_port']
    if ip is None or port is None:
        print("Invalid exit message: missing IP or port.")
        return
    peer_removed = False
    for file_hash in peer_dict:
        peers_to_remove = []
        for peer_id, details in peer_dict[file_hash]['peers'].items():
            if details['ip'] == ip and details['port'] == port:
                peers_to_remove.append(peer_id)
        for peer_id in peers_to_remove:
            del peer_dict[file_hash]['peers'][peer_id]
            peer_removed = True
            print(f"Peer {ip}:{port} has exited. Updated peer_dict for file {file_hash}: {peer_dict[file_hash]}")
    if not peer_removed:
        print(f"No matching peer found for {ip}:{port} in peer_dict.")



def get_host_default_interface_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
       s.connect(('8.8.8.8', 1))
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

    while not get_terminate_flag():
        try:
            server_socket.settimeout(1.0)
            client_socket, client_address = server_socket.accept()
            client_thread = threading.Thread(target=new_connection, args=(client_socket, client_address))
            client_thread.start()
        except socket.timeout:
            continue
        except Exception as e:
            print(f"Error accepting connection: {e}")
            break
    server_socket.close()
    print("Server has been shut down.")


#---SERVER COMMAND---
def server_CLI():
    while True:
        cmd_input = input("Server command: (discover <peer_hostname>, ping <peer_hostname>, peer_dict, exit)\n")
        cmd_parts = cmd_input.split()
        if cmd_parts:
            action = cmd_parts[0]
            if action == "discover" and len(cmd_parts) == 2:
                id = cmd_parts[1]
                thread = threading.Thread(target=discover_files, args=(id,))
                thread.start()
            elif action == "ping" and len(cmd_parts) == 2:
                id = cmd_parts[1]
                thread = threading.Thread(target=ping, args=(id,))
                thread.start()
            elif action == "exit":
                break
            elif action == "peer_dict":
                print(peer_dict)
            else:
                print("Unknown command or incorrect usage.")

#discover
def discover_files(peers_hostname):
    files = clients_files(peers_hostname)
    print(f"Files on {peers_hostname}: {files}")

def clients_files(peers_hostname):
    files = []
    for file_hash, file_info in peer_dict.items():
        peers = file_info["peers"]
        for peer_key, peer_info in peers.items():
            if peer_info["hostname"] == peers_hostname:
                files.append(file_info['file_name'])
    return files

#ping
def ping(peers_hostname):
    peer_ip, peer_port = ip_port_by_hostname(peer_dict, peers_hostname)
    if peer_ip and peer_port != None:
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

def ip_port_by_hostname(peer_dict, hostname):
    for file_hash, file_info in peer_dict.items():
        peers = file_info["peers"]
        for peer_key, peer_info in peers.items():
            if peer_info["hostname"] == hostname:
                return peer_info["ip"], peer_info["port"]
    return None

if __name__ == "__main__":
    #id = socket.getid()
    hostip = get_host_default_interface_ip()
    port = 65431
    print("Listening on: {}:{}".format(hostip,port))
    server_thread = threading.Thread(target=start_server, args=(hostip, port)) 
    server_thread.start()
    try:
        server_CLI()
    except KeyboardInterrupt:
        print("Shutting down server...")
        set_terminate_flag(True)
        server_thread.join()
    finally:
        print("All threads have been terminated. Exiting...")



