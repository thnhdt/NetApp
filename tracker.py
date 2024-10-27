# Initiate a server process
# add node
# send list node to client
import socket
from threading import Thread
import bencodepy
import json
import threading
import time
peer_dict = {}

lock = threading.Lock()

def new_connection(conn, addr):
    # print(addr)
    # print(conn)

    while True:
        data = conn.recv(1024).decode('utf-8');
        if not data:
            time.sleep(1)  # Wait for 100ms before the next iteration
            continue
        message = json.loads(data)
        if(message['type'] == 'download' or message['type'] == 'upload'): # register to tracker
            info_hash = message['info_hash']
            id = message['peer_id']
            peer_ip = message['ip']
            peer_port = message['port']
            event = message['event']
            lock.acquire()
            if(info_hash in peer_dict): # check if this file is already in peer_dict or not
                peer_dict[info_hash]["peers"][id] = {
                    "ip": peer_ip,
                    "port": peer_port,
                    "event": event
                }
            else:
                peer_dict[info_hash] = {"peers": {}}
                peer_dict[info_hash]["peers"][id] = {
                    "ip": peer_ip,
                    "port": peer_port,
                    "event": event
                }

            print("peer dict for {info_hash}", peer_dict)

            if info_hash in peer_dict:
                all_peers = peer_dict[info_hash]
                filtered_peers = {peer_id: peer_info for peer_id, peer_info in all_peers['peers'].items() if peer_id != id and peer_info['event'] != 'stopped'}
                response = {'peers': filtered_peers}
            else:
                response = {'peers': {}}
            lock.release()
            conn.send(json.dumps(response).encode()) # sends peer list
        elif (message['type'] == 'get_peers'):
            # Example: get_peers <info_hash>
            # info_hash = parts[1]
            id = message['peer_id']
            info_hash = message['info_hash']
            lock.acquire()
            if info_hash in peer_dict:
                all_peers = peer_dict[info_hash]
                filtered_peers = {peer_id: peer_info for peer_id, peer_info in all_peers['peers'].items() if peer_id != id and peer_info['event'] != 'stopped'}
                response = {'peers': filtered_peers}
            else:
                response = {'peers': {}}
            lock.release()
            conn.send(json.dumps(response).encode())
        elif (message['type'] == 'exit'): 
            # TODO: update status of peer
            print("receive exit request")
            peer_id = message['peer_id']
            response = "Client exit"
            lock.acquire()
            update_peer_dict(peer_id)
            lock.release()
            conn.send(json.dumps(response).encode())
        else:
            response = "What do you say?"
            conn.send(json.dumps(response).encode('utf-8'))



def update_peer_dict (stopped_peer_id) :
    new_peer_dict = {}
    global peer_dict
    for info_hash, all_peers in peer_dict.items():
        newPeers  = {peer_id: peer_info for peer_id, peer_info in all_peers['peers'].items() if peer_id != stopped_peer_id}
        new_peer_dict[info_hash] = {'peers': newPeers}
    peer_dict = new_peer_dict


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