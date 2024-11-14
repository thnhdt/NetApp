import os
from dotenv import load_dotenv

load_dotenv()
STORAGE_PATH = "storage"
FILE_STATUS_PATH = "file_status.json"
HOST_IP = os.getenv('HOST_IP', '127.0.0.1')
HOST_PORT = int(os.getenv('HOST_PORT', '65431'))
PEER_IP = os.getenv('PEER_IP', '127.0.0.1')
PEER_PORT = int(os.getenv('PEER_PORT', '65432'))
# PIECE_SIZE = int(os.getenv('PIECE_SIZE', '512')) 
PIECE_SIZE = 524288