import socket
from chat_utils import *
import client_state_machine as csm
from GUI import *

class Client:
    """
    Manages the client-side operations of the chat application,
    including connection, GUI, and message handling.
    """
    def __init__(self, args):
        """
        Initializes the Client.
        Args:
            args: Command-line arguments, typically containing server IP.
        """
        self.args = args
        self.socket = None
        self.sm = None
        self.gui = None

    def quit(self):
        """Shuts down the socket connection and closes it."""
        if self.socket:
            try:
                self.socket.shutdown(socket.SHUT_RDWR)
            except OSError: # Handle cases where socket might already be closed or not connected
                pass
            self.socket.close()

    def init_chat(self):
        """Initializes the chat client, sets up the socket, state machine, and GUI."""
        # print("[Client] Initializing chat...") # Debug print removed
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM )
        # Determine server address: use provided IP or default from chat_utils.
        svr = SERVER if self.args.d == None else (self.args.d, CHAT_PORT)
        # print(f"[Client] Connecting to server: {svr}") # Debug print removed
        self.socket.connect(svr)
        # print("[Client] Connected to server.") # Debug print removed
        self.sm = csm.ClientSM(self.socket) # Initialize client state machine.
        # print("[Client] Client State Machine initialized.") # Debug print removed
        self.gui = GUI(self.send, self.recv, self.sm, self.socket) # Initialize GUI.
        # print("[Client] GUI initialized.") # Debug print removed

    def send(self, msg):
        """Sends a message through the client's socket."""
        mysend(self.socket, msg)

    def recv(self):
        """Receives a message from the client's socket."""
        return myrecv(self.socket)

    def run_chat(self):
        """Starts the chat application execution flow."""
        # print("[Client] Starting run_chat...") # Debug print removed
        self.init_chat()
        # print("[Client] init_chat completed. Calling gui.run()...") # Debug print removed
        self.gui.run() # Start the GUI event loop.
        # print("[Client] gui.run() completed. GUI is off.") # Debug print removed
        self.quit() # Clean up and quit when GUI closes.
        # print("[Client] Client quit.") # Debug print removed
