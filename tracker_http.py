from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse
import bencodepy  # You'll need to install bencodepy for bencoding the response
import random
import socket

class TrackerHandler(BaseHTTPRequestHandler):
    # This will store the active torrents and peer information
    torrents = {}

    def do_GET(self):
        # Parse the query parameters from the URL
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)

        # Required parameters
        info_hash = params.get('info_hash', [None])[0]
        peer_id = params.get('peer_id', [None])[0]
        port = params.get('port', [None])[0]

        if not info_hash or not peer_id or not port:
            self.send_error(400, "Missing required parameters")
            return

        # Optional parameters
        uploaded = int(params.get('uploaded', [0])[0])
        downloaded = int(params.get('downloaded', [0])[0])
        left = int(params.get('left', [0])[0])
        event = params.get('event', [None])[0]

        # Add peer to the torrent's peer list
        peer_info = {
            'peer_id': peer_id,
            'ip': self.client_address[0],
            'port': int(port),
            'uploaded': uploaded,
            'downloaded': downloaded,
            'left': left,
        }

        if info_hash not in self.torrents:
            self.torrents[info_hash] = {'peers': []}

        # Handle different events
        if event == 'started':
            self.torrents[info_hash]['peers'].append(peer_info)
        elif event == 'stopped':
            self.torrents[info_hash]['peers'] = [
                peer for peer in self.torrents[info_hash]['peers']
                if peer['peer_id'] != peer_id
            ]
        elif event == 'completed': # the peer send this event must be in the dict before
            # The peer has completed downloading
            pass

        # Generate the response with a list of peers
        peers = self.torrents[info_hash]['peers']
        response = {
            'interval': 1800,  # Set the announce interval in seconds
            'complete': len([p for p in peers if p['left'] == 0]),
            'incomplete': len([p for p in peers if p['left'] > 0]),
            'peers': [
                {
                    'peer id': p['peer_id'],
                    'ip': p['ip'],
                    'port': p['port'],
                } for p in random.sample(peers, min(len(peers), 50))
            ]
        }

        # Send the bencoded response
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(bencodepy.encode(response))


def get_host_default_interface_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP connection
    try:
       s.connect(('8.8.8.8', 1)) # This connects the socket to the remote address 8.8.8.8 (Google's public DNS server) on port 1.
       ip = s.getsockname()[0]
    except Exception:
       ip = '127.0.0.1'
    finally:
       s.close()
    return ip


# Start the HTTP server
def run_tracker(server_class=HTTPServer, handler_class=TrackerHandler, port=8000):
    ip = get_host_default_interface_ip()
    server_address = (ip, port)
    httpd = server_class(server_address, handler_class)
    print(f'Starting tracker at {ip} on port {port}...')
    httpd.serve_forever()

if __name__ == '__main__':
    run_tracker()