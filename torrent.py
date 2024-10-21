import os
import hashlib
import bencodepy
PIECE_LENGTH = 1
def getInfoHash (info):
    bencoded_info = bencodepy.encode(info)
    # Compute the SHA-1 hash of the bencoded info
    info_hash = hashlib.sha1(bencoded_info).hexdigest()
    return info_hash

class Torrent ():
    def __init__(self):
        self.total_length: int = 0
        self.piece_length: int = 0
        self.piece_hashes = [] # TEMP because it only handles single-file torrent
        self.info_hash: str = ''
        self.peer_id: str = ''
        self.announce = ''
        # self.file_names = []
        self.files = [] # part of info
        self.name = '' # part of info (torrent file name)
        self.number_of_pieces: int = 0

    def get_tracker(self):
        return self.announce
    
    def load_file_from_path(self, path):
        try:
            # Open the torrent file in binary read mode
            with open(path, 'rb') as f:
                # Read the contents of the file
                bencoded_data = f.read()

            # Decode the bencoded data
            torrent_data = bencodepy.decode(bencoded_data)
            self.announce = torrent_data.get(b'announce', b'')
            
            info = torrent_data.get(b'info', {})
            # print(info)
            self.piece_length = info.get(b'piece length', 0)
           
            pieces_byte = info.get(b'pieces')
            self.piece_hashes = [pieces_byte[i:i + 20] for i in range(0, len(pieces_byte), 20)]  # Split pieces into chunks of 20 bytes
            self.name = info.get(b'name', '')

            # For multi-file torrents
            self.files = info.get(b'files', []) 
            self.total_length = sum(file[b'length'] for file in info.get(b'files', []))

            self.number_of_pieces = len(self.piece_hashes)
            # Calculate the info hash
            self.info_hash = getInfoHash(info)
            # Logging result
            # print("announce", self.announce)
            # print("piece_length", self.piece_length)
            # print("piece_hashes", self.piece_hashes)
            # print("info_hash", self.info_hash)
            # print("no_of_pieces", self.number_of_pieces)
            # print("files", self.files)
            # print("name", self.name)
            # print("total_length", self.total_length)
            return torrent_data
    
        except FileNotFoundError:
            print(f"Error: The file '{path}' was not found.")
        except Exception as e:
            print(f"An error occurred while loading the torrent file: {e}")

    def get_piece_hashes (self):
        return self.piece_hashes
        
    def create_multi_file_torrent(self, shared_file_path, torrent_file_path, tracker_url, output_torrent, piece_length=PIECE_LENGTH):
        for root, _, filenames in os.walk(shared_file_path):
            for filename in filenames:
                file_path = os.path.join(root, filename)
                file_size = os.path.getsize(file_path)
                self.total_length += file_size

                # Calculate the relative file path (relative to the directory being shared)
                relative_path = os.path.relpath(file_path, shared_file_path).split(os.sep)

                # Add the file's information to the "files" list
                self.files.append({
                    'length': file_size,
                    'path': relative_path
                })

                # Read the file in chunks and generate the SHA-1 hashes for the pieces
                with open(file_path, 'rb') as f:
                    while True:
                        chunk = f.read(piece_length)
                        if not chunk:
                            break
                        # Create a SHA-1 hash for each piece
                        self.piece_hashes.append(hashlib.sha1(chunk).digest())
        info = {
            'name': os.path.basename(shared_file_path),  # The root directory name
            'piece length': piece_length,               # The length of each piece
            'pieces': b''.join(self.piece_hashes),                 # Concatenate all the SHA-1 hashes
            'files': self.files                              # List of all files and their paths
        }
        
        self.info_hash = getInfoHash(info) # get info_hash
        self.announce = tracker_url # save tracker URL

        # Create the full torrent metadata
        torrent_data = {
            'announce': self.announce,  # The tracker URL
            'info': info              # The info dictionary
        }

        # Encode the data in bencode format and write it to the output file
        encoded_data = bencodepy.encode(torrent_data)
        with open(
        torrent_file_path + output_torrent, 'wb') as torrent_file:
            torrent_file.write(encoded_data)

        print(f'Torrent file created: {output_torrent}')


if __name__ == '__main__':
    # Input parameters
    shared_file_path = 'S:/Programming/Network/MyBitTorrent/shared_file'  # Replace with the path to your file
    torren_file_path = 'S:/Programming/Network/MyBitTorrent/torrent/'
    tracker_url = '192.168.0.2:22236'  # Replace with the tracker URL
    output_torrent = 'test.torrent'  # Output .torrent file path
    torrent = Torrent();
    torrent.create_multi_file_torrent(shared_file_path=shared_file_path,
                                      torrent_file_path = torren_file_path,
                                      tracker_url=tracker_url, output_torrent=output_torrent)
    existedTorrent = Torrent();
    existedTorrent.load_file_from_path("S:/Programming/Network/MyBitTorrent/torrent/test.torrent")
