import os
import json
import math
import hashlib
from prettytable import PrettyTable
from config import FILE_STATUS_PATH, STORAGE_PATH, PIECE_SIZE

# Utility Functions
def load_file_status():
    if os.path.exists(FILE_STATUS_PATH):
        with open(FILE_STATUS_PATH, "r") as file:
            return json.load(file)
    return {}

def save_file_status(file_status):
    with open(FILE_STATUS_PATH, "w") as file:
        json.dump(file_status, file, indent=4)

def update_file_status(file_name, piece_status):
    file_status = load_file_status()
    if file_name not in file_status:
        file_status[file_name] = {
            "piece_status": piece_status,
            "total_pieces": len(piece_status),
        }
    else:
        file_status[file_name]["piece_status"] = piece_status
    save_file_status(file_status)

def check_local_files(file_name):
    file_status = load_file_status()
    return file_name in file_status

def check_local_piece_files(file_name):
    file_status = load_file_status()
    if file_name in file_status:
        return file_status[file_name]["piece_status"]
    return False

# Table Display
# def create_table(pieces, select=True):
#     table = PrettyTable()
#     table.field_names = ["Piece Number", "Piece Status"]
#     for i, piece in enumerate(pieces):
#         piece_status = piece.strip() if piece else "(empty) - Cannot select" if select else "(empty)"
#         table.add_row([i + 1, piece_status])
#     return table
def create_table(pieces, select=True):
    table = PrettyTable()
    table.field_names = ["Piece Number", "Piece Content"]
    for i, piece in enumerate(pieces):
        piece_status = piece.strip().replace('\n', '').replace('\r', '') if piece else "(empty) - Cannot select" if select else "(empty)"
        table.add_row([i + 1, piece_status])
        print(str(piece_status))
    return table
# File Hashing
def generate_info_hash(file_path, hash_algorithm='sha1'):
    if hash_algorithm == 'sha1':
        hash_func = hashlib.sha1()
    elif hash_algorithm == 'sha256':
        hash_func = hashlib.sha256()
    else:
        raise ValueError("Unsupported hash algorithm. Use 'sha1' or 'sha256'.")
    with open(file_path, 'rb') as file:
        while chunk := file.read(4096):
            hash_func.update(chunk)
    return hash_func.hexdigest()

# File Chunk Management
def store_file_chunk(file_name, chunk_index, data, fill_missing=False):
    file_path = os.path.join(STORAGE_PATH, file_name)
    if not os.path.exists(file_path):
        with open(file_path, "wb") as f:
            f.write(b"")
    with open(file_path, "r+b") as f:
        f.seek(chunk_index * (PIECE_SIZE + 1))
        if fill_missing:
            f.write((b"\x00" * PIECE_SIZE) + b"\n")
        else:
            f.write(data.encode('latin1') + b"\n")

def load_file_chunks(file_name):
    chunk_data = []
    file_path = os.path.join(STORAGE_PATH, file_name)
    if not os.path.exists(file_path):
        return []
    with open(file_path, "rb") as f:
        total_size = os.path.getsize(file_path)
        total_chunks = math.ceil(total_size / (PIECE_SIZE + 1))
        for chunk_index in range(total_chunks):
            f.seek(chunk_index * (PIECE_SIZE + 1))
            data = f.read(PIECE_SIZE)
            chunk_data.append(data.decode('latin1').rstrip('\x00'))
    return chunk_data

def load_file_chunk(file_name, chunk_index):
    file_path = os.path.join(STORAGE_PATH, file_name)
    if not os.path.exists(file_path):
        return None
    
    with open(file_path, "rb") as f:
        f.seek(chunk_index * (PIECE_SIZE + 1))
        data = f.read(PIECE_SIZE)
        return data.decode('latin1').rstrip('\x00')