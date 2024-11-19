import json

def mock_server_response():
    response = {
        "file_size": 5120,
        "peers_info": [
            {
                "peers_ip": "127.0.0.1",
                "peers_port": 65433,
                "num_order_in_file": [0, 1, 2, 3, 4, 6, 8]
            },
        ]
    }
    return json.dumps(response)