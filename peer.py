import socket
from threading import Thread
import uuid
import torrent
import bencodepy
import os
import argparse
import json

def new_connection(addr, conn):
    print("New connection {} {}".format(addr, conn))

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


def clientThread (peer_id, tracker_url, info_hash):
    print("client thread",peer_id, tracker_url, info_hash)
    try:
        # Parse the tracker URL to get the hostname and port
        host, port = tracker_url.split(':')
        port = int(port)

        # Create a socket connection to the tracker
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as clientsocket:
            clientsocket.connect((host, port))
            # Prepare the registration message
            peer_ip, peer_port = clientsocket.getsockname()
            print(peer_ip, peer_port)
            while True: 

                request = input();
                if(request == "announce"):
                    message = {
                        'action': 'announce',  # '0' for 'connect'
                        'info_hash': info_hash,
                        'peer_id': peer_id,
                        'ip': peer_ip,
                        'port': peer_port,
                        'num_want': 200,
                        'event': 'started'  # Event type
                    }
                    print("Client id:{} trackerURL {} info hash {} ip {} port {}".format(peer_id, tracker_url, info_hash, peer_ip, peer_port))

                    # Send the registration message
                    clientsocket.sendall(json.dumps(message).encode('utf-8'))

                    # Receive the response from the tracker
                    response = clientsocket.recv(1024).decode("utf-8")
                    response_data = json.loads(response)

                    # Handle the response
                    print("Tracker Response:", response_data)
                else:
                    print("Unknown request") 
                    continue

    except Exception as e:
        print(f"Error connecting to tracker: {e}")


def serverThread (host, port):
    print('Server thread running at ip {} port {}'.format(host, port))
    serversocket = socket.socket()
    serversocket.bind((host, port))
    serversocket.listen(5) # maximum 5 connections
    while True:
        addr, conn = serversocket.accept()
        nconn = Thread(target=new_connection, args=(addr, conn))
        nconn.start()
        nconn.join();

if __name__ == "__main__":
    hostip = get_host_default_interface_ip();
    PORT = 11111;
    sThread = Thread(target=serverThread, args=(hostip,PORT))
    # parser = argparse.ArgumentParser(
    #                     prog='Client',
    #                     description='Connect to pre-declard server',
    #                     epilog='!!!It requires the server is running and listening!!!')
    # parser.add_argument('--server-ip')
    # parser.add_argument('--server-port', type=int)
    # args = parser.parse_args()
    # tracker_ip = args.server_ip
    # tracker_port = args.server_port
    # print(tracker_ip, tracker_port)
    existedTorrent = torrent.Torrent();
    torrentPath = "test.torrent"
    existedTorrent.load_file_from_path(torrentPath)
    peer_id = os.urandom(20).hex()  # Generates a random 20-byte ID
    cThread = Thread(target=clientThread, args=(peer_id, 
                                                existedTorrent.announce.decode('utf-8'), 
                                                existedTorrent.info_hash
                                                ))
    sThread.start()
    cThread.start()
    sThread.join()
    cThread.join()