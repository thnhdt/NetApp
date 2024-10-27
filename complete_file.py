from math import ceil
import os 

class completeFile():
    piece_size = 1 # 256 KB a piece
    filePaths = []
    files = [] # {length: x, path: []}
    size = 0
    pieceBoundaries = [0]
    filePaths = []

    def __init__(self, path: str, files):
        self.path = path
        self.files = files

        for file in files:
            self.size += file['length']
            piece_no = ceil(file['length'] / self.piece_size)
            self.pieceBoundaries.append(self.pieceBoundaries[-1] + piece_no)
            self.filePaths.append(self.path + file['path'][-1].decode()) # peer's stored directory + file_name
        print("Size of file ", self.size)
        self.n_pieces = ceil(self.size / self.piece_size)
        self.pieceBoundaries.pop(0) # delete the first dummy 0

    def get_piece_no(self, piece_no):
        fileIdx = self._find_file_of_piece(piece_no)
        with open(self.filePaths[fileIdx], "rb") as file:
            if(fileIdx > 0):
                offset = self.piece_size*(piece_no-self.pieceBoundaries[fileIdx-1])
            else:
                offset = self.piece_size*(piece_no)
            file.seek(offset)
            data = file.read(self.piece_size)
        # self.read_fp.seek(offset, 0)
        # piece = self.read_fp.read(self.piece_size)
        return data
    def get_bitfield (self):
        return "1" * self.n_pieces
    
    def _find_file_of_piece(self, piece_no):
        ans = 0
        for i in range(len(self.pieceBoundaries)):
            if(piece_no < self.pieceBoundaries[i]):
                ans = i
                break
        return ans

    @staticmethod
    def get_size(path):
        return os.path.getsize(path)
    
# if __name__ == "__main__":
#     file = completeFile("./peerfile/file.txt", "file.txt")

