import socket
from threading import Thread
import threading
import uuid
import torrent
import bencodepy
import time
import os
import argparse
import json
import sys
import base64
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

lock = threading.Lock()

class Peer:
    port: int
    ip: str
    id: str
    available_files: dict[str, str] # filename, file_dir
    clientSocket: socket.socket
    peer_list: dict[str, dict[str, str]] # [infohash, peer_id [ip, port, socket, status]] 
    serverSocket: socket.socket

    def __init__(self, ip, port_no, id, name):
        self.port = port_no
        self.ip = ip
        self.id = id
        self.downloadDir = PEERS_INCOMPLETE_DIR + name + "/"
        self.completeDir = PEERS_COMPLETE_DIR + name + "/"
        self.incomplete_files = {}
        self.available_files = {}
        self.clientSocket = None
        self.peer_list = {}

        if not os.path.isdir(self.downloadDir):
            os.mkdir(self.downloadDir)
            print("make dir")
        else:
            print("not make dir")

        if not os.path.isdir(self.completeDir):
            os.mkdir(self.completeDir)

    
    def _do_handshake (self, peer_id, peer_addr, info_hash): 
        print("do_handshake with", peer_addr, info_hash)

        if self.peer_list.get(info_hash): # TEMP
            if self.peer_list[info_hash].get(peer_id):
                print("Already handshake with", peer_addr, info_hash)
                return 
        # peer
        try:
            new_conn = socket.socket()
            new_conn.connect((peer_addr['ip'], peer_addr['port']))
            HANDSHAKE_MESSAGE = {
                'type': 'handshake',
                'info_hash': info_hash,
                'peer_id': self.id
            }
            if not self.peer_list.get(info_hash):
                self.peer_list[info_hash] = {peer_id: { 'socket': new_conn }}
            else:
                self.peer_list[info_hash][peer_id] = { 'socket': new_conn }
            # print(self.peer_list[info_hash][peer_id])
            new_conn.sendall(json.dumps(HANDSHAKE_MESSAGE).encode())
        except socket.error as e:
            logging.error(f"Socket error occurred: {e}")
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
        
        try:
        # Receiving data from the socket
            HANDSHAKE_RESPONSE = new_conn.recv(3000).decode()
            if not HANDSHAKE_RESPONSE:
                logging.warning("Connection closed by the peer.")
            response = json.loads(HANDSHAKE_RESPONSE)
            self.peer_list[info_hash][peer_id]['bitfield'] = response['bitfield'] # get bitfield from this peer
            logging.info("Data received successfully.")
        except socket.error as e:
            logging.error(f"Failed to receive data: {e}")
        except Exception as e:
            logging.error(f"An unexpected error occurred while receiving data: {e}")


    def add_peers (self, peers, info_hash):
        print("add_peers")
        for peer_id, peer_addr in peers.items():
            self._do_handshake(peer_id, peer_addr, info_hash)

    def _find_peers_have_piece (self, info_hash, piece_no):
        result = []
        for peer_id, peer_info in self.peer_list[info_hash].items():
            if peer_info['bitfield'][piece_no] == '1':
                result.append({**peer_info, 'peer_id': peer_id})
        return result 

    def request_piece (self, info_hash, peer_id, socket, piece_no):
        print("request_piece", socket)
        REQUEST_PIECE_MESSAGE = {
            'type': 'request_piece',
            'info_hash': info_hash,
            'piece_no': piece_no
        }
        try:
            socket.sendall(json.dumps(REQUEST_PIECE_MESSAGE).encode())
            print("send request piece")
        except socket.error as e:
            logging.error(e)

        # socket.settimeout(10)
        try:
            response = socket.recv(6000000).decode()
            data = json.loads(response)
            print("get request piece", data)

            if data['status']:
                byte_data = base64.b64decode(data['piece'])
                print("write piece no {} buf {}".format (piece_no, byte_data ))
                lock.acquire()
                write_result = self.incomplete_files[info_hash].write_piece_no(buf=byte_data, piece_no=piece_no)
                lock.release()
                if write_result == True:
                    HAVE_MESSAGE = {
                        'type': 'have',
                        'info_hash': info_hash,
                        'piece_no': piece_no,
                        'peer_id': self.id
                    }
                    for peer_id, peer_info in self.peer_list[info_hash].items():
                        peer_info['socket'].sendall(json.dumps(HAVE_MESSAGE).encode())
            else:
                logging.info("Peer id {} does not have piece {}".format(peer_id, piece_no))           
        except socket.error as e:
            logging.error(e)

    def _get_bitfield (self, info_hash):
        if self.available_files.get(info_hash):
            return self.available_files[info_hash].get_bitfield()
        else:
            return self.incomplete_files[info_hash].get_bitfield()
        

    def runClientThread (self):
        while True: 
            print('''You can 
                1. upload file.torrent
                2. download file.torrent
                3. create file.torrent
                ''')
            try:
                request = input(">")
            except EOFError as e:
                print(e)
                continue

            # Parse the tracker URL to get the hostname and port
            commands = request.split(" ");

            if(commands[0] == "download"):
                torrentFile = torrent.Torrent();
                torrentFile.load_file_from_path(commands[1])

                try:
                    trackerURL = torrentFile.get_tracker().decode('utf-8')
                except Exception as e:
                    print(e)
                    continue

                host, port = trackerURL.split(':')
                port = int(port)

                info_hash = torrentFile.info_hash; # get the file's info hash

                # create incomplete_file with files info in torrent file
                files = []
                for fileDict in torrentFile.files:
                    files.append(convert_bytes_to_string(fileDict))
                self.incomplete_files[info_hash] = incomplete_file.incompleteFile(self.downloadDir, files, create_status_file(info_hash), torrentFile.get_piece_hashes()) 

                # Create a socket connection to the tracker
                if not self.clientSocket:
                    self.clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.clientSocket.connect((host, port))
                    # Prepare the registration message
                message = {
                    'type': commands[0], 
                    'info_hash': info_hash,
                    'peer_id': self.id,
                    'ip': self.ip,
                    'port': self.port,
                    'event': 'started'  # Event type
                }
                print("Send msg to tracker", message)

                # Send the registration message
                self.clientSocket.sendall(json.dumps(message).encode('utf-8'))

                # Receive the response from the tracker
                response = self.clientSocket.recv(1024).decode("utf-8")
                response_data = json.loads(response)
                # Handle the response
                peer_list = response_data['peers']
                print("List of peers:", peer_list)
                # peer_list = {}
                self.add_peers(peer_list, info_hash)

                # Request all the missing pieces of files
                # this must be run in a different thread
                while True:
                    missing_pieces = self.incomplete_files[info_hash].get_missing_pieces()
                    print("Missing pieces", missing_pieces)
                    if(len(missing_pieces) > 0):
                        if self.peer_list.get(info_hash):
                            if len(self.peer_list[info_hash].items()) == 0:
                                time.sleep(5)  # Wait for 5s before the next iteration
                                peer_list =self.get_peer_list(info_hash=info_hash, host=host, port=port)
                                self.add_peers(peer_list, info_hash)
                                continue
                        else:
                            time.sleep(5)  # Wait for 5s before the next iteration
                            peer_list =self.get_peer_list(info_hash=info_hash, host=host, port=port)
                            self.add_peers(peer_list, info_hash)
                            continue
                        i = 0
                        # Get the piece no you want to download
                        while i < len(missing_pieces):
                            available_peers = self._find_peers_have_piece(info_hash, missing_pieces[i])
                            if len(available_peers) > 0:
                                newThread = Thread(target=self.request_piece, args=(info_hash, available_peers[0]['peer_id'], available_peers[0]['socket'], missing_pieces[i]))
                                newThread.start()
                                newThread.join()
                            else:
                                print("No peer with piece {}".format(missing_pieces[i]))
                                time.sleep(5)  # Wait for 5s before the next iteration
                                peer_list =self.get_peer_list(info_hash=info_hash, host=host, port=port)
                                self.add_peers(peer_list, info_hash)
                                continue
                            i += 1
                            time.sleep(1)
                    else: 
                        break
                print("Download completely!")
                        # Write block to piece
            elif(commands[0] == "get_peers"): # temp for testing
                message = {
                    'type': commands[0], 
                    'info_hash': info_hash,
                    'peer_id': self.id
                }

                self.clientSocket.sendall(json.dumps(message).encode('utf-8'))

                # Receive the response from the tracker
                response = self.clientSocket.recv(1024).decode("utf-8")
                response_data = json.loads(response)

                # Handle the response
                print("Tracker Response:", response_data)
            elif(commands[0] == "upload"): # temp for testing
        
                # commands [1] is the URL to the torrent file
                torrentFile = torrent.Torrent();
                torrentFile.load_file_from_path(commands[1])
                try:
                    trackerURL = torrentFile.get_tracker().decode('utf-8')
                except AttributeError as e:
                    print(e)
                    continue
                host, port = trackerURL.split(':')
                port = int(port)

                info_hash = torrentFile.info_hash; # get the file's info hash
                # extract info from torrent file
                files = []
                for fileDict in torrentFile.files:
                    files.append(convert_bytes_to_string(fileDict))
                self.available_files[info_hash] = complete_file.completeFile(self.completeDir, files)
                # create a status file with full of 1

                # register info to tracker
                if not self.clientSocket:
                    self.clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.clientSocket.connect((host, port))
                    # Prepare the registration message
                message = {
                    'type': commands[0], 
                    'info_hash': info_hash,
                    'peer_id': self.id,
                    'ip': self.ip,
                    'port': self.port,
                    'event': 'completed'  # Event type
                }
                print("Send msg to tracker", message)

                # Send the registration message
                self.clientSocket.sendall(json.dumps(message).encode('utf-8'))

                # Receive the response from the tracker
                response = self.clientSocket.recv(1024).decode("utf-8")
                response_data = json.loads(response)

                # Handle the response
                print("Upload response:", response_data)
                
                # Get the block no you want to download

                # Request to the peer which has that block

                # Write block to piece
            elif(commands[0] == "exit"): # temp for testing

                # Prepare the registration message
                if self.clientSocket:
                    peer_ip, peer_port = self.clientSocket.getsockname()
                    print(peer_ip, peer_port)
                    message = {
                        'type': commands[0], 
                        'peer_id': self.id,
                        'event': 'stopped'  # Event type
                    }
                    print("Send stop msg to tracker", message)

                    # Send the registration message
                    self.clientSocket.sendall(json.dumps(message).encode('utf-8'))

                    # Receive the response from the tracker
                    response = self.clientSocket.recv(1024).decode("utf-8")
                    response_data = json.loads(response)

                    # Handle the response

                    print("Exit response:", response_data)
                    self.clientSocket.close()
                os._exit(0)
                break

            else:
                print("Unknown request") 
                continue
        

    def get_peer_list (self, info_hash, host, port):
            if not self.clientSocket:
               self.clientSocket.connect((host, port)) # connect to tracker
            # Prepare the registration message
            message = {
                'type': "get_peers", 
                'peer_id': self.id,
                'info_hash': info_hash,
            }
            print("Send msg to tracker", message)

            # Send the registration message
            self.clientSocket.sendall(json.dumps(message).encode('utf-8'))

            # Receive the response from the tracker
            response = self.clientSocket.recv(1024).decode("utf-8")
            response_data = json.loads(response)
            # Handle the response
            peer_list = response_data['peers']
            print("List of peers:", peer_list)
            return peer_list

    

    def listen_to_peer(self, c: socket.socket, addr):
        """
        Listen to peer and give response when asked.
        """
        print("Listen to peer")
        while True:
            try:
                msg = json.loads(c.recv(2048).decode())
                if msg['type'] == 'request_piece':
                    info_hash = msg['info_hash']
                    piece_no = msg['piece_no']
                    # check if available files has that piece
                    piece = ""
                    if self.available_files.get(info_hash):
                        piece = self.available_files[info_hash].get_piece_no(piece_no)
                    # check if incomplete files has that piece
                    elif self.incomplete_files.get(info_hash):
                        piece = self.incomplete_files[info_hash].get_piece_no(piece_no)
                    if(piece != ""):
                        encoded_data = base64.b64encode(piece).decode('utf-8')

                    ret_msg = json.dumps({
                        "type": "response_piece",
                        "piece_no": piece_no,
                        "status": True if piece != "" else False,
                        "piece": encoded_data if piece != "" else ""
                    })
                    print("Send piece {}".format(piece_no))
                    c.send(ret_msg.encode())
                elif msg['type'] == 'handshake':
                    info_hash = msg['info_hash']
                    HANDSHAKE_RESPONSE_MESSAGE = {"type": "HANDSHAKE_RES",
                                                "bitfield": self._get_bitfield(info_hash),
                                                "peer_id": self.id}
                    c.sendall(json.dumps(HANDSHAKE_RESPONSE_MESSAGE).encode())
                elif msg['type'] == 'have':
                    info_hash = msg['info_hash']
                    peer_id = msg['peer_id']
                    piece_no = msg['piece_no']
                    print("Receive HAVE message", msg)
                    # HAVE_RESPONSE_MESSAGE = {"type": "HAVE_RES", "msg": "OK"}
                    if self.peer_list.get(info_hash) and self.peer_list[info_hash].get(peer_id):
                        newBitfield = self.peer_list[info_hash][peer_id]['bitfield'][:piece_no] + "1" + self.peer_list[info_hash][peer_id]['bitfield'][piece_no+1:]
                        self.peer_list[info_hash][peer_id]['bitfield'] = newBitfield
                    # c.sendall(json.dumps(HAVE_RESPONSE_MESSAGE).encode())
                    
            except EOFError:  # TODO: don't know what is happening here.
                pass

    def runServerThread (self):
        print('Server thread running at ip {} port {}'.format(self.ip, self.port))
        self.serverSocket = socket.socket()
        self.serverSocket.bind((self.ip, self.port))
        self.serverSocket.listen(5) # maximum 5 connections
        # conn_threads = []
        while True:
            conn, addr = self.serverSocket.accept()
            nconn = Thread(target=self.listen_to_peer, args=(conn, addr))
            nconn.start()
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
    parser = argparse.ArgumentParser(
                        prog='Client',
                        description='Connect to pre-declard server',
                        epilog='!!!It requires the server is running and listening!!!')
    parser.add_argument('--peer-port', type=int)
    parser.add_argument('--peer-name', type=str)
    args = parser.parse_args()
    PORT = args.peer_port
    NAME = args.peer_name
    peer_id = os.urandom(20).hex()  # Generates a random 20-byte ID
    peer = Peer(hostip, PORT, peer_id, NAME);
    sThread = Thread(target=peer.runServerThread, args=())
    cThread = Thread(target=peer.runClientThread, args=())
    sThread.start()
    cThread.start()
    sThread.join()
    cThread.join()