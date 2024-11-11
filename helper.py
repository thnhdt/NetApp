import os
import json
import random
from dotenv import load_dotenv

# Tải biến môi trường từ .env
load_dotenv()
FILE_STATUS_PATH = "file_status.json"
STORAGE_PATH = "storage"
PIECE_SIZE = int(os.getenv('PIECE_SIZE', '512'))

# --- Helper Functions --- #

def load_file_status():
    """
    Tải trạng thái file từ file_status.json nếu tồn tại.
    """
    if os.path.exists(FILE_STATUS_PATH):
        with open(FILE_STATUS_PATH, "r") as file:
            return json.load(file)
    return {}

def save_file_status(file_status):
    """
    Lưu trạng thái file vào file_status.json.
    """
    with open(FILE_STATUS_PATH, "w") as file:
        json.dump(file_status, file, indent=4)

def update_file_status(file_name, piece_status):
    """
    Cập nhật trạng thái của file vào file_status.json.
    """
    file_status = load_file_status()
    
    if file_name not in file_status:
        file_status[file_name] = {
            "piece_status": piece_status,
            "total_pieces": len(piece_status),
        }
    else:
        file_status[file_name]["piece_status"] = piece_status
    
    save_file_status(file_status)

def store_file_chunk(file_name, chunk_index, data, fill_missing=False):
    """
    Lưu một chunk dữ liệu vào file. Nếu fill_missing là True, sẽ lấp đầy chunk bằng các byte null khi thiếu.
    """
    file_path = os.path.join(STORAGE_PATH, file_name)

    # Tạo file mới nếu chưa tồn tại
    if not os.path.exists(file_path):
        with open(file_path, "wb") as f:
            f.write(b"")

    with open(file_path, "r+b") as f:
        f.seek(chunk_index * (PIECE_SIZE + 1))  # Chuyển đến đúng vị trí cho chunk này
        if fill_missing:
            # Lấp đầy chunk bằng byte null nếu bị thiếu
            f.write((b"\x00" * PIECE_SIZE) + b"\n")
        else:
            # Thêm ký tự xuống hàng sau dữ liệu của chunk
            f.write(data.encode('latin1') + b"\n")


def create_file_with_chunks(file_name, num_chunks, missing_chunk_probability):
    """
    Tạo file mới với số lượng chunk giả định, có khả năng thiếu một số chunks.
    Trạng thái sẽ được cập nhật vào file_status.json.
    
    :param file_name: Tên file cần tạo
    :param num_chunks: Số lượng chunks cần tạo cho file
    """
    piece_status = [0] * num_chunks  # Khởi tạo trạng thái các chunk là chưa lưu trữ (0)
    
    # Cập nhật trạng thái ban đầu của file
    update_file_status(file_name, piece_status)
    
    for chunk_index in range(num_chunks):
        if random.random() > missing_chunk_probability:
            data = f"Data for chunk {chunk_index + 1} of {file_name}"  # Tạo dữ liệu cho chunk
            store_file_chunk(file_name, chunk_index, data)  # Lưu chunk vào file
            piece_status[chunk_index] = 1  # Đánh dấu chunk này đã được lưu trữ
        else:
            store_file_chunk(file_name, chunk_index, "", fill_missing=True)  # Lấp đầy chunk thiếu bằng byte null
    
    # Cập nhật lại trạng thái sau khi tạo file và lưu các chunk
    update_file_status(file_name, piece_status)
    print(f"Updated status for {file_name}: {piece_status}\nCreate {file_name} successfully!")

# --- Public Function --- #
def create_sample_file(file_name, num_chunks, missing_chunk_probability = 0.3):
    """
    Tạo một file mẫu với số lượng chunk giả định và xác suất bị thiếu.
    """
    create_file_with_chunks(file_name, num_chunks, missing_chunk_probability)