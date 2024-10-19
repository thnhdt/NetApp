import socket
from threading import Thread
import uuid
import torrent
import bencodepy
import os
import argparse
import json
import complete_file
import incomplete_file
import logging
from collections import OrderedDict
PEERS_INCOMPLETE_DIR = "./peer-incomplete-file"
PEERS_COMPLETE_DIR = "./peer-complete-file"

def create_status_file (filename):
    name, _ = os.path.splitext(filename)
    # Create a new filename with .json extension
    json_filename = name + 'Status.json'
    return json_filename

def convert_bytes_to_string(ordered_dict, encoding='utf-8'):
    # Create a new OrderedDict with decoded string values
    converted_dict = OrderedDict()
    print("convert Dict", ordered_dict)
    for key, value in ordered_dict.items():
        # Decode the key and value if they are bytes
        if isinstance(key, bytes):
            key = key.decode(encoding)
        if isinstance(value, bytes):
            value = value.decode(encoding)
        # Add the decoded key and value to the new OrderedDict
        converted_dict[key] = value
    
    return converted_dict

class Peer:
    port: int
    ip: str
    id: str
    available_files: dict[str, str] # filename, file_dir
    clientSocket: socket.socket
    peer_list: dict[str, dict[str, str]] # [infohash, peer_id [ip, port, status]] 
    serverSocket: socket.socket

    def __init__(self, ip, port_no, id, name):
        print("init peer")
        self.port = port_no
        self.ip = ip
        self.id = id
        self.downloadDir = PEERS_INCOMPLETE_DIR + name + "/"
        self.completeDir = PEERS_COMPLETE_DIR + name + "/"
        self.incomplete_files = {}

        if not os.path.isdir(self.downloadDir):
            os.mkdir(self.downloadDir)
            print("make dir")
        else:
            print("not make dir")

        if not os.path.isdir(self.completeDir):
            os.mkdir(self.completeDir)

        self.available_files = {}
        for f in os.listdir(self.completeDir):
            print(f)
            self.available_files[f] = complete_file.completeFile(f, "")

        
        
    def runServerThread (self):
        self.serverSocket = socket.socket()
        self.serverSocket.bind((self.ip, self.port))

    def runClientThread (self):
        while True: 
            print('''You can 
                1. upload file
                2. download file
                ''')
            request = input(">");
            # Parse the tracker URL to get the hostname and port
            commands = request.split(" ");

            if(commands[0] == "download"):
                torrentFile = torrent.Torrent();
                torrentFile.load_file_from_path(commands[1])

                trackerURL = torrentFile.get_tracker().decode('utf-8')

                host, port = trackerURL.split(':')
                port = int(port)

                info_hash = torrentFile.info_hash; # get the file's info hash

                # create incomplete_file with files info in torrent file
                files = []
                for fileDict in torrentFile.files:
                    files.append(convert_bytes_to_string(fileDict))
                self.incomplete_files[info_hash] = incomplete_file.incompleteFile(self.downloadDir, files, create_status_file(info_hash), torrentFile.get_piece_hashes()) 

                # Create a socket connection to the tracker
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as clientsocket:
                    clientsocket.connect((host, port))
                    # Prepare the registration message
                    peer_ip, peer_port = clientsocket.getsockname()
                    print(peer_ip, peer_port)
                    message = {
                        'action': commands[0], 
                        'info_hash': info_hash,
                        'peer_id': self.id,
                        'ip': peer_ip,
                        'port': peer_port,
                        'event': 'started'  # Event type
                    }
                    print("Send msg to tracker", message)

                    # Send the registration message
                    clientsocket.sendall(json.dumps(message).encode('utf-8'))

                    # Receive the response from the tracker
                    response = clientsocket.recv(1024).decode("utf-8")
                    response_data = json.loads(response)
                    # Handle the response
                    self.peer_list = response_data['peers']
                    print("List of peers:", self.peer_list)

                # Request all the missing pieces of files
                # this must be run in a different thread
                while True:
                    missing_pieces = self.incomplete_files[info_hash].get_missing_pieces()
                    print("Missing pieces", missing_pieces)
                    if(len(missing_pieces) > 0):
                        i = 0
                        # Get the piece no you want to download
                        connections = []
                        for peer_id, peer_addr in self.peer_list:
                            while i < len(missing_pieces):
                                if(peer_id != self.id):
                                    connection = Thread(target=self.get_piece_from_peer, args=(info_hash, peer_addr['ip'], peer_addr['port'], missing_pieces[i]))
                                    # connections.append(connection)
                                    connection.join()
                            i += 1
                    else: 
                        break
                        # Request to the peer which has that block

                            # Write block to piece
            elif(commands[0] == "get_peers"): # temp for testing
                message = {
                    'action': commands[0], 
                    'info_hash': info_hash,
                }

                clientsocket.sendall(json.dumps(message).encode('utf-8'))

                # Receive the response from the tracker
                response = clientsocket.recv(1024).decode("utf-8")
                response_data = json.loads(response)

                # Handle the response
                print("Tracker Response:", response_data)
            elif(commands[0] == "upload"): # temp for testing
        
                # commands [1] is the URL to the torrent file
                torrentFile = torrent.Torrent();
                torrentFile.load_file_from_path(commands[1])

                trackerURL = torrentFile.get_tracker().decode('utf-8')

                host, port = trackerURL.split(':')
                port = int(port)

                info_hash = torrentFile.info_hash; # get the file's info hash
                # extract info from torrent file
                files = []
                for fileDict in torrentFile.files:
                    files.append(convert_bytes_to_string(fileDict))
                self.available_files[info_hash] = complete_file.completeFile(PEERS_COMPLETE_DIR, files)
                # create a status file with full of 1

                # register info to tracker
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as clientsocket:
                    clientsocket.connect((host, port))
                    # Prepare the registration message
                    peer_ip, peer_port = clientsocket.getsockname()
                    print(peer_ip, peer_port)
                    message = {
                        'action': commands[0], 
                        'info_hash': info_hash,
                        'peer_id': self.id,
                        'ip': peer_ip,
                        'port': peer_port,
                        'event': 'started'  # Event type
                    }
                    print("Send msg to tracker", message)

                    # Send the registration message
                    clientsocket.sendall(json.dumps(message).encode('utf-8'))

                    # Receive the response from the tracker
                    response = clientsocket.recv(1024).decode("utf-8")
                    response_data = json.loads(response)

                    # Handle the response
                    print("Upload response:", response_data)
                    
                    # Get the block no you want to download

                    # Request to the peer which has that block

                    # Write block to piece
            else:
                print("Unknown request") 
                continue

    def get_piece_from_peer(self, info_hash, peer_ip, peer_port, piece_no):

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect((peer_ip, peer_port))
            logging.info(f"Connected to Peer {peer_ip}")
        except:
            print("could not connect to ", peer_ip)
        msg = json.dumps({
            "type": "request_piece",
            "data": {
                "info_hash": info_hash,
                "piece_no": piece_no
            }
        })
        sock.send(msg.encode())
        # c.settimeout(PEER_TIMEOUT)
        try:
            msg = json.loads(sock.recv(4096).decode())
            if msg['type'] == "response_piece":
                if msg['data']['status']:
                    self.incomplete_files[info_hash].write_piece_no(buf=msg['data']['piece'], piece_no=piece_no)
                else:
                    logging.info("Peer with ip {} does not have piece {}".format(peer_ip, piece_no))            

        except socket.timeout:
            print(f"peer {peer_ip} did not send the file")
        logging.info("Receive piece {} from peer with ip {}".format(piece_no, peer_ip))
        socket.close()



    def listen_to_peer(self, c: socket.socket, addr):
        """
        Listen to peer and give response when asked.
        """

        while True:
            try:
                msg = json.loads(c.recv(2048).decode())

                # if msg['type'] == 'request_file':
                #     req_file_name = msg['data']
                #     if req_file_name in self.available_files:
                #         file_details = pickle.dumps({
                #             "type": "available_file",
                #             "data": {
                #                 "filesize": str(self.available_files[req_file_name].size)
                #             }
                #         })

                #         c.send(file_details)
                

                # find that piece in either complete file and incomplete file
                if msg['type'] == 'request_piece':
                    info_hash = msg['data']['info_hash']
                    piece_no = msg['data']['piece_no']
                    # TODO: check if available files has that piece
                    # piece = self.available_files[file_name].get_chunk_no(chunk_no)

                    # TODO: check if incomplete files has that piece

                    ret_msg = json.dumps({
                        "type": "response_piece",
                        "data": {
                            "piece_no": piece_no,
                            "status": True,
                            "piece": data
                        }
                    })

                    c.send(ret_msg.encode())
            except EOFError:  # TODO: don't know what is happening here.
                pass


    def download_file ():
        print("Downlioad")



    def serverThread (self, host, port):
        print('Server thread running at ip {} port {}'.format(host, port))
        serversocket = socket.socket()
        serversocket.bind((host, port))
        serversocket.listen(5) # maximum 5 connections
        while True:
            conn, addr = serversocket.accept()
            nconn = Thread(target=self.listen_to_peer, args=(conn, addr))
            nconn.start()
            nconn.join();

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


if __name__ == "__main__":
    hostip = get_host_default_interface_ip();
    PORT = 11112;
    peer_id = os.urandom(20).hex()  # Generates a random 20-byte ID
    peer = Peer(hostip, PORT, "fake_id", "hihi");
    sThread = Thread(target=peer.runServerThread, args=())
    cThread = Thread(target=peer.runClientThread, args=())
    sThread.start()
    cThread.start()
    sThread.join()
    cThread.join()