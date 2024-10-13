# FOR TESTING PURPOSE

import os

class FileDownloader:
    def __init__(self, file_path, file_size, piece_size, block_size):
        self.file_path = file_path
        self.file_size = file_size
        self.piece_size = piece_size
        self.block_size = block_size
        self.total_pieces = (file_size + piece_size - 1) // piece_size
        self.blocks_per_piece = (piece_size + block_size - 1) // block_size

        # Create a file of the appropriate size
        with open(self.file_path, 'wb') as f:
            f.truncate(file_size)

        # Tracking which blocks have been downloaded (False means not downloaded)
        self.downloaded_blocks = [
            [False] * self.blocks_per_piece for _ in range(self.total_pieces)
        ]

    def write_block(self, piece_index, block_index, block_data):
        """Write a block to its correct position in the file."""
        if self.downloaded_blocks[piece_index][block_index]:
            print(f"Block {block_index} of piece {piece_index} already downloaded.")
            return

        # Calculate the position in the file where this block should be written
        piece_start = piece_index * self.piece_size
        block_start = piece_start + block_index * self.block_size

        # Write the block data to the file
        with open(self.file_path, 'r+b') as f:
            f.seek(block_start)
            f.write(block_data)

        # Mark this block as downloaded
        self.downloaded_blocks[piece_index][block_index] = True
        print(f"Downloaded block {block_index} of piece {piece_index}.")

    def is_piece_complete(self, piece_index):
        """Check if all blocks of a piece have been downloaded."""
        return all(self.downloaded_blocks[piece_index])

    def is_download_complete(self):
        """Check if the entire file has been downloaded."""
        return all(all(piece) for piece in self.downloaded_blocks)

# Example usage
if __name__ == '__main__':
    file_path = 'downloaded_file.txt'
    file_size = 4  # 4B for example
    piece_size = 2  # 2B per piece
    block_size = 1  # 1B per block

    downloader = FileDownloader(file_path, file_size, piece_size, block_size)

    # Simulate receiving blocks out of order
    downloader.write_block(0, 0, b'A' * 1)  # Block 0 of Piece 0
    downloader.write_block(1, 1, b'B' * 1)  # Block 1 of Piece 1
    downloader.write_block(0, 1, b'C' * 1)  # Block 1 of Piece 0
    downloader.write_block(1, 0, b'D' * 1)  # Block 0 of Piece 1

    # Check download status
    print("Piece 0 complete:", downloader.is_piece_complete(0))
    print("Piece 1 complete:", downloader.is_piece_complete(1))
    print("Download complete:", downloader.is_download_complete())