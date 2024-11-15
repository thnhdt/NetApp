import json
import socket

def get_peers(client_socket, file_name):
    command = {
        "action": "get_peers",
        "file_name": file_name
    }
    
    try:
        client_socket.sendall(json.dumps(command).encode() + b'\n')
        response = client_socket.recv(4096).decode()
        server_response = json.loads(response)
        
        if 'peers' in server_response:
            peers = server_response['peers']
            if peers:
                print("Peers Hostnames:")
                for peer_info in peers.values():
                    print(peer_info['hostname'])
            else:
                print("No peers found for this file.")
        else:
            print("No peers found for this file.")
    
    except (socket.error, json.JSONDecodeError) as e:
        print(f"Error while getting peers: {e}")
