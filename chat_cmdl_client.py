
from chat_client_class import *

def main():
    """
    Command-line interface for the chat client.
    Parses server IP address argument and starts the chat client.
    """
    import argparse
    parser = argparse.ArgumentParser(description='chat client argument')
    parser.add_argument('-d', type=str, default=None, help='server IP addr')
    args = parser.parse_args()

    client = Client(args)
    client.run_chat()

main()
