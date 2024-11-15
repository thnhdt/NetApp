peer_dict1 = {
    "abc123hash": {
        "file_name": "example_file.txt",
        "file_size": 2048,  # Size in bytes
        "piece_size": 512,   # Size of each piece in bytes
        "peers": {
            "192.168.1.2:65433": {
                "hostname": "peer1.local",
                "ip": "192.168.1.2",
                "port": 65433,
                "num_order_in_file": [0, 1, 2]
            },
            "192.168.1.3:65434": {
                "hostname": "peer2.local",
                "ip": "192.168.1.3",
                "port": 65434,
                "num_order_in_file": [0, 1]
            }
        }
    },
    "def456hash": {
        "file_name": "another_file.mp4",
        "file_size": 1048576,  # Size in bytes
        "piece_size": 1024,     # Size of each piece in bytes
        "peers": {
            "192.168.1.4:65435": {
                "hostname": "peer3.local",
                "ip": "",
                "port": 65435,
                "num_order_in_file": [0, 1, 2, 3, 4]
            }
        }
    }
}

def ping_host(peers_hostname):
    peer_info, file_hash = get_peer_ip_by_hostname(peer_dict1, peers_hostname)
    # print(peer_info)
    peer_ip = peer_info["ip"]
    if peer_ip:
        peer_port = peer_info["port"]
        print(f"{peer_ip} and {peer_port}")
    else:
        print(f"{peers_hostname} is not in network")


def get_peer_ip_by_hostname(peer_dict, hostname):
    for file_hash, file_info in peer_dict.items():
        for peer_info in file_info['peers'].values():
            if peer_info['hostname'] == hostname:
                return peer_info, file_hash
    return None, None

if __name__ == "__main__":
    # goto, file_hash = get_peer_ip_by_hostname(peer_dict1, "peer3.local")
    # print(goto, file_hash)
    ping_host("peer3.local")
