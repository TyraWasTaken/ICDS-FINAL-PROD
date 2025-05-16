import socket
import sys
from chat_utils import *
import client_state_machine as csm
from GUI import *

class Client:
    def __init__(self, args):
        self.args = args

    def quit(self):
        self.socket.shutdown(socket.SHUT_RDWR)
        self.socket.close()

    def init_chat(self):
        print("[Client] Initializing chat...")
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM )
        svr = SERVER if self.args.d == None else (self.args.d, CHAT_PORT)
        print(f"[Client] Connecting to server: {svr}")
        self.socket.connect(svr)
        print("[Client] Connected to server.")
        self.sm = csm.ClientSM(self.socket)
        print("[Client] Client State Machine initialized.")
        self.gui = GUI(self.send, self.recv, self.sm, self.socket)
        print("[Client] GUI initialized.")

    def shutdown_chat(self):
        return

    def send(self, msg):
        mysend(self.socket, msg)

    def recv(self):
        return myrecv(self.socket)

    def run_chat(self):
        print("[Client] Starting run_chat...")
        self.init_chat()
        print("[Client] init_chat completed. Calling gui.run()...")
        self.gui.run()
        print("[Client] gui.run() completed. GUI is off.")
        self.quit()
        print("[Client] Client quit.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Socket Client')
    parser.add_argument('-d', type=str, default=None, help="server IP addr")
    args = parser.parse_args()

    print("[ClientApp] Starting client application...")
    client = Client(args)
    try:
        client.run_chat()
    except Exception as e:
        print(f"[ClientApp] An error occurred: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("[ClientApp] Client application finished.")
