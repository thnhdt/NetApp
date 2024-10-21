# Initiate a server process
# add node
# send list node to client
import socket
from threading import Thread
import bencodepy
import json
import time
peer_dict = {}

def new_connection(conn, addr):
    # print(addr)
    # print(conn)

    while True:
        data = conn.recv(1024).decode('utf-8');
        if not data:
            time.sleep(1)  # Wait for 100ms before the next iteration
            continue
        message = json.loads(data)
        if(message['action'] == 'download' or message['action'] == 'upload'): # register to tracker
            info_hash = message['info_hash']
            peer_id = message['peer_id']
            peer_ip = message['ip']
            peer_port = message['port'];

            if(info_hash in peer_dict): # check if this file is already in peer_dict or not
                peer_dict[info_hash]["peers"][peer_id] = {
                    "ip": peer_ip,
                    "port": peer_port,
                }
            else:
                peer_dict[info_hash] = {"peers": {}}
                peer_dict[info_hash]["peers"][peer_id] = {
                    "ip": peer_ip,
                    "port": peer_port,
                }

            print("peer dict", peer_dict)
            if info_hash in peer_dict:
                peers = peer_dict[info_hash]
                response = peers
            else:
                response = {'peers': {}}
            conn.send(json.dumps(response).encode()) # sends peer list
        elif (message['action'] == 'get_peers'): 
                # Example: get_peers <info_hash>
                # info_hash = parts[1]
                info_hash = message['info_hash']
                if info_hash in peer_dict:
                    peers = peer_dict[info_hash]
                    response = peers
                else:
                    response = {'peers': {}}
                conn.send(json.dumps(response).encode())
        else:
            response = "What do you say?"
            conn.send(json.dumps(response).encode('utf-8'))

    

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

def get_peers_for_file(info_hash): # get list of peers that requesting (having a specific file)
    if info_hash in peer_dict:
        return peer_dict[info_hash]["peers"]
    else:
        return {}  # No peers available for the given info_hash

def server_program(host, port):
    serversocket = socket.socket()
    serversocket.bind((host, port))
    serversocket.listen(10)
    while True:
        conn, addr = serversocket.accept()
        nconn = Thread(target=new_connection, args=(conn, addr))
        nconn.start()

if __name__ == "__main__":
    #hostname = socket.gethostname()
    hostip = get_host_default_interface_ip()
    port = 22236
    print("Listening on: {}:{}".format(hostip,port))
    server_program(hostip, port)