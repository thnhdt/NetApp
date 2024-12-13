from handlers.fetch_handler import fetch
from handlers.publish_handler import publish
from handlers.download_handler import download
from handlers.terminate_handler import set_terminate_flag
from handlers.connect_handler import disconnect_from_server
from handlers.create_sample_file_handler import create_sample_file
from handlers.get_peers import get_peers

def process_input(cmd, client_socket, peer_port):
    params = cmd.split()

    if len(params) == 0:
        print("Please type your command (publish <file_name> | fetch <file_name> | download <file_name> | create <file_name> <num_chunks> | get_peers <file_name> | exit)\n")
        return

    try:
        if params[0] == 'exit':
            set_terminate_flag(True)
            if client_socket:
                disconnect_from_server(client_socket, peer_port=peer_port)
            print("Stopping the server...")

        elif params[0] == 'create':
            if len(params) == 1:
                print('Argument file_name is required')
                return
            elif len(params) == 2:
                print('Argument num_chunks is required')
                return
            create_sample_file(params[1], int(params[2]))

        elif params[0] == 'publish':
            if len(params) == 1:
                print('Argument file_name is required')
                return
            publish(client_socket, params[1], peer_port)

        elif params[0] == 'fetch':
            if len(params) == 1:
                print('Argument file_name is required')
                return
            fetch(client_socket, params[1], peer_port)

        elif params[0] == 'download':
            if len(params) == 1:
                print('Argument file_name is required')
                return
            download(client_socket, params[1], peer_port)

        elif params[0] == 'get_peers':
            if len(params) == 1:
                print('Argument file_name is required')
                return
            get_peers(client_socket, params[1])

        else:
            print('Invalid command (publish <file_name> | fetch <file_name> | download <file_name> | create <file_name> <num_chunks> | get_peers <file_name> | exit)')

    except IndexError:
        print('Invalid command (publish <file_name> | fetch <file_name> | download <file_name> | create <file_name> <num_chunks> | get_peers <file_name> | exit)')