# FOR TESTING PURPOSE
import libtorrent as lt

def read_torrent_file(path):
    with open(path, 'rb') as file:
        contents = file.read()  # Read the file content as bytes
        torrent_info = lt.bdecode(contents)  # Decode the torrent content
        return torrent_info

# Example usage
torrent_data = read_torrent_file('example.txt.torrent')
print(torrent_data)