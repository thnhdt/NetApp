import os
import random
from config import FILE_STATUS_PATH, PIECE_SIZE, STORAGE_PATH
from handlers.utils import update_file_status

# --- Helper Functions --- #
def store_file_chunk(file_name, chunk_index, data, fill_missing=False, is_last_chunk=False):
    """
    Lưu một chunk dữ liệu vào file. Nếu fill_missing là True, lấp đầy chunk bằng các byte null.
    Nếu là chunk cuối cùng (is_last_chunk=True), không thêm dấu xuống dòng.
    """
    file_path = os.path.join(STORAGE_PATH, file_name)

    # Tạo file mới nếu chưa tồn tại
    if not os.path.exists(file_path):
        with open(file_path, "wb") as f:
            f.write(b"")

    with open(file_path, "r+b") as f:
        f.seek(chunk_index * (PIECE_SIZE + 1))  # Di chuyển đến vị trí chính xác cho chunk này (tính cả dấu xuống dòng)
        if fill_missing:
            f.write(b"\x00" * PIECE_SIZE)
            if not is_last_chunk:
                f.write(b"\n")
        else:
            chunk_data = data.encode('latin1')
            padded_data = chunk_data.ljust(PIECE_SIZE, b'\x00')
            f.write(padded_data)
            if not is_last_chunk:
                f.write(b"\n")

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
        is_last_chunk = (chunk_index == num_chunks - 1)
        if random.random() > missing_chunk_probability:
            data = f"Data for chunk {chunk_index + 1} of {file_name}"  # Tạo dữ liệu cho chunk
            store_file_chunk(file_name, chunk_index, data, False, is_last_chunk)  # Lưu chunk vào file
            piece_status[chunk_index] = 1  # Đánh dấu chunk này đã được lưu trữ
        else:
            store_file_chunk(file_name, chunk_index, "", fill_missing=True, is_last_chunk=is_last_chunk)  # Lấp đầy chunk thiếu bằng byte null
    
    # Cập nhật lại trạng thái sau khi tạo file và lưu các chunk
    update_file_status(file_name, piece_status)
    print(f"Updated status for {file_name}: {piece_status}\nCreate {file_name} successfully!")

# --- Public Function --- #
def create_sample_file(file_name, num_chunks, missing_chunk_probability=0.3):
    """
    Tạo một file mẫu với số lượng chunk giả định và xác suất bị thiếu.
    """
    create_file_with_chunks(file_name, num_chunks, missing_chunk_probability)