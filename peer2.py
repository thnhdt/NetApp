import socket
from threading import Thread
import uuid
import argparse

def new_connection(addr, conn):
    print("New connection {} {}".format(addr, conn))

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


def clientThread (id, serverip, serverport, peerid, peerport):
    print("Client {} {} {} {} {}".format(id, serverip, serverport, peerid, peerport))
    clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    clientsocket.connect((serverip, serverport));


def serverThread (host, port):
    print('Server thread running at ip {} port {}'.format(host, port))
    serversocket = socket.socket()
    serversocket.bind((host, port))
    serversocket.listen(10)
    while True:
        addr, conn = serversocket.accept()
        nconn = Thread(target=new_connection, args=(addr, conn))
        nconn.start()
        nconn.join();

if __name__ == "__main__":
    hostip = get_host_default_interface_ip();
    PORT = 11112;
    sThread = Thread(target=serverThread, args=(hostip,PORT))
    parser = argparse.ArgumentParser(
                        prog='Client',
                        description='Connect to pre-declard server',
                        epilog='!!!It requires the server is running and listening!!!')
    parser.add_argument('--server-ip')
    parser.add_argument('--server-port', type=int)
    args = parser.parse_args()
    tracker_ip = args.server_ip
    tracker_port = args.server_port
    # print(tracker_ip, tracker_port)
    cThread = Thread(target=clientThread, args=(uuid.uuid4(),tracker_ip, tracker_port, hostip, PORT))
    sThread.start()
    cThread.start()
    sThread.join()
    cThread.join()