from math import ceil
import os 
import logging
import json
import hashlib

class incompleteFile():
    piece_size = 1 # 256 KB a piece
    piece_status: str # array of 0 1 indicates the status of the file, load from json file 
    piece_hashes = []
    files = [] # {length: x, path: []}
    size = 0
    filePaths = []
    pieceBoundaries = [0]
    def __init__(self, path: str, files, statusFileName:str, piece_hashes):
        self.filePath = path # download directory
        
        self.statusFilePath = path + statusFileName
        self.piece_hashes = piece_hashes # the hashes of the pieces
        self.files = files
        if not os.path.exists(path): # check if the file path exist or not
                os.makedirs(path)
        for file in files:
            self.size += file['length']
            piece_no = ceil(file['length'] / self.piece_size)
            self.pieceBoundaries.append(self.pieceBoundaries[-1] + piece_no)
            self.filePaths.append(self.filePath + file['path'][-1].decode())
            if not os.path.exists(self.filePaths[-1]): # check if the file path exist or not
                with open(self.filePaths[-1], 'w') as file:
                    pass  # Creates an empty file
        self.pieceBoundaries.pop(0) # delete the first dummy 0
        self.n_pieces = ceil(self.size / self.piece_size)
        print("Size of the complete file ", self.size)
        self.piece_status = self.load_status_file()
        print("File status ", self.piece_status)
        # Check if the directory exist, if not create it
      

    def get_piece_no(self, piece_no):
        if(self.piece_status[piece_no] == "1"):
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
        else:
            return ""
    
    def load_status_file(self):
        if not os.path.exists(self.statusFilePath):
        # If the file does not exist, create it and write some initial content
            with open(self.statusFilePath, 'w') as file:
                initial_data = {"status": "0" * self.n_pieces}
                json.dump(initial_data, file)
        # If the file exists, read and display the content
        with open(self.statusFilePath, 'r') as file:
            data = json.load(file)
        return data['status']        
    
    def write_piece_no(self, piece_no, buf):
        # use thread lock to preventing race condition
        # check buf with piece_hash
        # update status file
        if(self.check_piece_integrity(piece_no, buf)):
            

            new_status = self.piece_status[:piece_no] + "1" + self.piece_status[piece_no+1:]
            self.piece_status = new_status
            with open(self.statusFilePath, "w") as file:
                data = {"status": new_status}
                json.dump(data, file)

            fileIdx = self._find_file_of_piece(piece_no)
            with open(self.filePaths[fileIdx], "r+b") as file:
                if(fileIdx > 0):
                    offset = self.piece_size*(piece_no-self.pieceBoundaries[fileIdx-1])
                else:
                    offset = self.piece_size*(piece_no)
                file.seek(offset)
                file.write(buf)
            print("buf", buf)
            print("Write price no {} into file {} with offset {}".format(piece_no, fileIdx, offset) )
            return True
        else: 
            print("Write price no {} failed".format(piece_no))
            return False

    def _find_file_of_piece(self, piece_no):
        ans = 0
        for i in range(len(self.pieceBoundaries)):
            if(piece_no < self.pieceBoundaries[i]):
                ans = i
                break
        return ans
    

    def check_piece_integrity (self, piece_no, buf):
        newHash = hashlib.sha1(buf).digest()
        if(newHash == self.piece_hashes[piece_no]):
            print("Piece hash is the same")
            return True
        else:
            print("Piece hash is different")
            return False
    def get_bitfield (self):
        return self.piece_status


    def get_missing_pieces (self):
        missing_pieces = []
        for i in range(len(self.piece_status)):
            if(self.piece_status[i] == "0"):
                missing_pieces.append(i)
        # print("Missing pieces", missing_pieces)
        return missing_pieces

    @staticmethod
    def get_size(path):
        return os.path.getsize(path)
    
if __name__ == "__main__":
    file = incompleteFile("./peer_incomplete_file/", "iFile.txt", "iFileStatus.json", 10000000)

