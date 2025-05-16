
import time
import socket
import select
import sys
import indexer
import json
import pickle as pkl
from chat_utils import *
import chat_group as grp

class Server:
    def __init__(self):
        self.new_clients = [] #list of new sockets of which the user id is not known
        self.logged_name2sock = {} #dictionary mapping username to socket
        self.logged_sock2name = {} # dict mapping socket to user name
        self.all_sockets = []
        self.group = grp.Group()
        self.user_profile_info = {} # To store PFP URLs and other info
        self.board = [] # Stores the current Tic-Tac-Toe game board.

        # Tic-Tac-Toe specific attributes for stats
        self.game_stats = {}   # Stores player game statistics (wins, losses, streaks)
        self.stats_file = "tictactoe_stats.json" # File to store Tic-Tac-Toe game statistics.
        self._load_game_stats() # Load stats on server startup

        #start server
        self.server=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(SERVER)
        self.server.listen(5)
        self.all_sockets.append(self.server)
        #initialize past chat indices
        self.indices={}
        # sonnet
        try:
            self.sonnet = indexer.PIndex("AllSonnets.txt")
        except Exception as e:
            print(f"ERROR: Failed to initialize PIndex: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1) # Exit explicitly if PIndex fails
    def new_client(self, sock):
        # Registers a new client socket.
        print('new client...')
        sock.setblocking(0)
        self.new_clients.append(sock)
        self.all_sockets.append(sock)

    def login(self, sock):
        # Processes a login attempt from a new client.
        try:
            raw_msg = myrecv(sock) # Receive the login message.
            if not raw_msg: # Client disconnected before sending login information.
                print(f"Client {sock.getpeername()} disconnected before sending login info.")
                # Clean up socket if client disconnected before login.
                if sock in self.all_sockets:
                    self.all_sockets.remove(sock)
                if sock in self.new_clients:
                    self.new_clients.remove(sock)
                sock.close()
                return

            msg = json.loads(raw_msg)
            print("login:", msg)
            if len(msg) > 0:

                if msg["action"] == "login":
                    name = msg["name"]
                    
                    if self.group.is_member(name) != True:
                        # If username is not taken, log in the user.
                        self.new_clients.remove(sock)
                        # Map username to socket and vice-versa.
                        self.logged_name2sock[name] = sock
                        self.logged_sock2name[sock] = name
                        # Load or create chat history index for the user.
                        if name not in self.indices.keys():
                            try:
                                # Attempt to load existing chat history.
                                self.indices[name]=pkl.load(open(name+'.idx','rb'))
                            except IOError: # If chat history index doesn't exist, create a new one.
                                self.indices[name] = indexer.Index(name)
                        print(name + ' logged in')
                        self.group.join(name)
                        # Initialize user profile information if it's their first login.
                        if name not in self.user_profile_info:
                            self.user_profile_info[name] = {"pfp_url": None}
                        mysend(sock, json.dumps({"action":"login", "status":"ok"}))
                    else: # Handle duplicate login attempt.
                        mysend(sock, json.dumps({"action":"login", "status":"duplicate"}))
                        print(name + ' duplicate login attempt')
                else:
                    print ('wrong code received') # Incorrect action received from client.
            else: # Handle unexpected client disconnection during login.
                # This might be redundant if the initial `not raw_msg` check catches disconnection.
                self.logout(sock)
        except json.JSONDecodeError:
            peer_name_info = sock.getpeername() if sock.fileno() != -1 else "already closed socket"
            print(f"Login: Received malformed JSON from {peer_name_info}.")
            if sock.fileno() != -1: # Check if socket is still open before attempting to close.
                if sock in self.new_clients: self.new_clients.remove(sock)
                if sock in self.all_sockets: self.all_sockets.remove(sock)
                sock.close()
            return # Stop further processing for this socket.
        except Exception as e: # Catch other potential errors during login.
            peer_name_info = sock.getpeername() if sock.fileno() != -1 else "already closed socket"
            print(f"Error during login for {peer_name_info}: {e}")
            if sock.fileno() != -1:
                if sock in self.new_clients: self.new_clients.remove(sock)
                if sock in self.all_sockets: self.all_sockets.remove(sock)
                sock.close()
            return

    def logout(self, sock):
        # Handles user logout.
        name = self.logged_sock2name[sock]
        pkl.dump(self.indices[name], open(name + '.idx','wb'))
        del self.indices[name]
        del self.logged_name2sock[name]
        del self.logged_sock2name[sock]
        self.all_sockets.remove(sock)
        self.group.leave(name)
        sock.close()

    # --- Tic-Tac-Toe Statistics Helper Methods ---
    def _load_game_stats(self):
        # Loads Tic-Tac-Toe game statistics from a JSON file.
        try:
            with open(self.stats_file, 'r') as f:
                self.game_stats = json.load(f)
            print(f"[GameServer] Tic-Tac-Toe stats loaded from {self.stats_file}.")
        except FileNotFoundError:
            print(f"[GameServer] Stats file '{self.stats_file}' not found. Initializing new stats.")
            self.game_stats = {} # Initialize with empty stats if file not found.
        except json.JSONDecodeError:
            print(f"[GameServer] Error decoding JSON from '{self.stats_file}'. Initializing new stats.")
            self.game_stats = {} # Initialize with empty stats if JSON is malformed.

    def _save_game_stats(self):
        # Saves Tic-Tac-Toe game statistics to a JSON file.
        try:
            with open(self.stats_file, 'w') as f:
                json.dump(self.game_stats, f, indent=4)
            print(f"[GameServer] Tic-Tac-Toe stats saved to {self.stats_file}.")
        except IOError as e:
            print(f"[GameServer] Error saving Tic-Tac-Toe stats to '{self.stats_file}': {e}")

    def _get_game_id(self, player1_name, player2_name):
        # Generates a unique and consistent ID for a game session between two players.
        return "_vs_".join(sorted([player1_name, player2_name]))

    def _initialize_player_stats(self, player_name):
        # Initializes the statistics for a player if they don't already exist.
        if player_name not in self.game_stats:
            self.game_stats[player_name] = {"wins": 0, "losses": 0, "current_streak": 0, "max_streak": 0, "ties": 0}
            
    def _record_game_result(self, winner_name, loser_name, is_tie=False):
        # Records the result of a Tic-Tac-Toe game and updates player statistics.
        print(f"[GameServer] Recording game result: Winner: {winner_name}, Loser: {loser_name}, Tie: {is_tie}")
        
        # Initialize stats for players if they don't exist.
        players_in_game = []
        if winner_name: players_in_game.append(winner_name)
        if loser_name: players_in_game.append(loser_name)
        
        # If it's a tie, ensure both players (passed as winner_name and loser_name by the caller)
        # are included for stat updates if not already.
        if is_tie:
            if winner_name and winner_name not in players_in_game: # winner_name is player1 in a tie
                 players_in_game.append(winner_name)
            if loser_name and loser_name not in players_in_game: # loser_name is player2 in a tie
                 players_in_game.append(loser_name)

        for p_name in players_in_game:
             self._initialize_player_stats(p_name)

        announcement = ""
        if is_tie:
            # For a tie, both player names are needed for the announcement.
            # The caller (handle_msg for 'move') should pass the two players involved as winner_name and loser_name.
            if winner_name and loser_name: # Assuming these are the two players in a tie
                 self.game_stats[winner_name]["ties"] = self.game_stats[winner_name].get("ties", 0) + 1
                 self.game_stats[loser_name]["ties"] = self.game_stats[loser_name].get("ties", 0) + 1
                 announcement = f"The Tic-Tac-Toe game between {winner_name} and {loser_name} was a tie!"
            else: # Fallback if player names for tie aren't clear (should not happen if called correctly)
                announcement = "A Tic-Tac-Toe game ended in a tie!"

        else: # There is a winner
            if winner_name: # Ensure winner_name is not None
                self._initialize_player_stats(winner_name) # Ensure stats are initialized
                self.game_stats[winner_name]["wins"] += 1
                self.game_stats[winner_name]["current_streak"] += 1
                if self.game_stats[winner_name]["current_streak"] > self.game_stats[winner_name]["max_streak"]:
                    self.game_stats[winner_name]["max_streak"] = self.game_stats[winner_name]["current_streak"]
                
                if loser_name:
                    self._initialize_player_stats(loser_name) # Ensure stats are initialized
                    self.game_stats[loser_name]["losses"] += 1
                    self.game_stats[loser_name]["current_streak"] = 0 # Reset loser's streak
                
                announcement = f"{winner_name} has won a game of Tic-Tac-Toe! Current win streak: {self.game_stats[winner_name]['current_streak']}."
            else: # This case should ideally not be reached if it's not a tie and there's no winner.
                announcement = "A Tic-Tac-Toe game has ended."


        self._save_game_stats()
        
        if announcement:
            print(f"[GameServer] Broadcasting game result: {announcement}")
            for name, sock_to_send in self.logged_name2sock.items():
                system_msg_payload = {"action": "exchange", "from": "[GameServer]", "message": announcement}
                mysend(sock_to_send, json.dumps(system_msg_payload))
        
    def check_winners(self):
        # Checks the Tic-Tac-Toe board for a win, tie, or if the game should continue.
        # This method directly uses `self.board`.

        # Check rows for a win.
        for r in range(3):
            if self.board[r][0] == self.board[r][1] and self.board[r][1] == self.board[r][2] and self.board[r][0] != 0:
                return ["win", self.board[r][0]]
        # Check columns for a win.
        for c in range(3):
            if self.board[0][c] == self.board[1][c] and self.board[1][c] == self.board[2][c] and self.board[0][c] != 0:
                return ["win", self.board[0][c]]
        # Check main diagonal (top-left to bottom-right) for a win.
        if self.board[0][0] == self.board[1][1] and self.board[1][1] == self.board[2][2] and self.board[0][0] != 0:
            return ["win", self.board[0][0]]
        # Check anti-diagonal (top-right to bottom-left) for a win.
        if self.board[0][2] == self.board[1][1] and self.board[1][1] == self.board[2][0] and self.board[0][2] != 0:
            return ["win", self.board[0][2]]
        
        # Check for a tie (board full, no winner).
        is_full = True
        for r in range(3):
            for c in range(3):
                if self.board[r][c] == 0: # 0 represents an empty cell.
                    is_full = False
                    break
            if not is_full: # Optimization: if an empty cell is found, no need to check further rows.
                break
        
        if is_full:
            return ["tie"] # Board is full, and no winner was found, so it's a tie.

        return ["continue"] # No winner and board is not full, so game continues.

        
        
        
#==============================================================================
# Main command switchboard for handling client messages.
#==============================================================================
    def handle_msg(self, from_sock):
        # Reads and processes a message from a client socket.
        try:
            # Get client identifier for logging purposes.
            client_identifier = self.logged_sock2name.get(from_sock)
            if not client_identifier:
                try:
                    # Fallback to socket peer name if user is not yet logged in.
                    client_identifier = str(from_sock.getpeername())
                except socket.error:
                    # Further fallback if socket details are unavailable (e.g., socket closed).
                    client_identifier = f"Unknown/Pre-Login Socket ({from_sock.fileno()})"

            print(f"[Server Log] Attempting to receive message from {client_identifier}...")
            msg_content = myrecv(from_sock) # Receive message from the client.
            print(f"[Server Log] Received from {client_identifier}: {len(msg_content) if msg_content is not None else 'None'} bytes")

            if not msg_content: # Client disconnected gracefully.
                print(f"[Server Log] Client {client_identifier} disconnected gracefully (received empty message). Logging out.")
                if from_sock in self.logged_sock2name: # Logout user if they were logged in.
                     self.logout(from_sock)
                else: # Clean up if it was a new client that disconnected before full login.
                    if from_sock in self.all_sockets: self.all_sockets.remove(from_sock)
                    if from_sock in self.new_clients: self.new_clients.remove(from_sock)
                    if from_sock.fileno() != -1: from_sock.close() # Ensure socket is closed.
                return

            # Attempt to parse the message as JSON.
            try:
                msg = json.loads(msg_content)
                print(f"[Server Log] Parsed JSON from {client_identifier}: action={msg.get('action', 'N/A')}")
            except json.JSONDecodeError:
                print(f"[Server Log] Handle_msg: Received malformed JSON from {client_identifier}. Content: '{msg_content[:100]}...'")
                # Do not process further if JSON is malformed.
                return

            # --- Main message handling logic based on 'action' ---
            
            # Handle 'connect' request: Establishes a chat connection between two users.
            if msg["action"] == "connect":
                to_name = msg["target"]
                from_name = self.logged_sock2name[from_sock]
                if to_name == from_name: # User trying to connect to themselves.
                    msg_resp = json.dumps({"action":"connect", "status":"self"})
                elif self.group.is_member(to_name): # Target user is online.
                    to_sock = self.logged_name2sock[to_name]
                    self.group.connect(from_name, to_name) # Update group state.
                    the_guys = self.group.list_me(from_name)
                    msg_resp = json.dumps({"action":"connect", "status":"success"})
                    # Notify other members of the group about the new connection.
                    for g in the_guys[1:]:
                        to_sock_peer = self.logged_name2sock[g]
                        mysend(to_sock_peer, json.dumps({"action":"connect", "status":"request", "from":from_name}))
                else: # Target user is not online.
                    msg_resp = json.dumps({"action":"connect", "status":"no-user"})
                mysend(from_sock, msg_resp)
            
            # Handle 'exchange' request: Broadcasts a message to other connected users.
            elif msg["action"] == "exchange":
                from_name = self.logged_sock2name[from_sock]
                # Process message text (e.g., add timestamp).
                processed_msg = text_proc(msg["message"], from_name)
                # Add message to sender's chat history index.
                if from_name in self.indices:
                    self.indices[from_name].add_msg_and_index(processed_msg)
                else:
                    print(f"[Server Warning] No index found for sender {from_name} during exchange.")

                print(f"[Server] Broadcasting message from {from_name} to all users.")
                # Send message to all other logged-in users.
                for name, to_sock in self.logged_name2sock.items():
                    if name != from_name: # Don't send message back to the sender.
                        # Add message to recipient's chat history index.
                        if name in self.indices:
                             self.indices[name].add_msg_and_index(processed_msg)
                        else:
                             print(f"[Server Warning] No index found for recipient {name} during exchange.")
                        mysend(to_sock, json.dumps({"action":"exchange", "from": msg["from"], "message": msg["message"]}))
            
            # Handle 'list' request: Sends a list of online users to the requester.
            elif msg["action"] == "list":
                user_list_data = []
                for name in self.logged_name2sock.keys():
                    pfp_url = self.user_profile_info.get(name, {}).get("pfp_url")
                    user_list_data.append({"name": name, "pfp_url": pfp_url})
                mysend(from_sock, json.dumps({"action":"list", "results": user_list_data}))
            
            # Handle 'poem' request: Retrieves and sends a specific sonnet.
            elif msg["action"] == "poem":
                poem_indx = int(msg["target"])
                from_name = self.logged_sock2name[from_sock]
                print(f"{from_name} asks for poem {poem_indx}")
                try:
                    poem = self.sonnet.get_poem(poem_indx)
                    poem_text = '\n'.join(poem)
                    print('Sending poem:\n', poem_text)
                    mysend(from_sock, json.dumps({"action":"poem", "results":poem_text}))
                except IndexError: # Requested poem index is out of range.
                     mysend(from_sock, json.dumps({"action":"poem", "results":"Poem index out of range."}))
                except Exception as e: # Other errors during poem retrieval.
                     print(f"Error retrieving poem {poem_indx}: {e}")
                     mysend(from_sock, json.dumps({"action":"poem", "results":"Error retrieving poem."}))
            
            # Handle 'time' request: Sends the current server time.
            elif msg["action"] == "time":
                ctime = time.strftime("%I:%M%p", time.localtime())
                mysend(from_sock, json.dumps({"action":"time", "results":ctime}))
            
            # Handle 'private_message' request: Sends a message to a specific user.
            elif msg["action"] == "private_message":
                target_username = msg.get("to")
                message_text = msg.get("message")
                if not target_username or not message_text: # Validate request.
                    status_payload = {"action": "private_message_status", "to": target_username or "N/A", "status": "error_bad_request", "detail": "Missing 'to' or 'message' field."}
                    mysend(from_sock, json.dumps(status_payload))
                else:
                    sender_username = self.logged_sock2name[from_sock]
                    if target_username == sender_username: # User trying to PM themselves.
                        status_payload = {"action": "private_message_status", "to": target_username, "status": "error_self_message", "detail": "Cannot send private message to yourself."}
                        mysend(from_sock, json.dumps(status_payload))
                    elif target_username in self.logged_name2sock: # Target user is online.
                        target_sock = self.logged_name2sock[target_username]
                        payload_for_recipient = {"action": "incoming_private_message", "from": f"[PM from {sender_username}]", "message": message_text}
                        mysend(target_sock, json.dumps(payload_for_recipient))
                        # Confirm PM sent to the sender.
                        status_payload_to_sender = {"action": "private_message_status", "to": target_username, "status": "sent", "detail": f"PM sent to {target_username}."}
                        mysend(from_sock, json.dumps(status_payload_to_sender))
                    else: # Target user is offline.
                        status_payload = {"action": "private_message_status", "to": target_username, "status": "error_user_offline", "detail": f"User {target_username} is not online."}
                        mysend(from_sock, json.dumps(status_payload))
            
            # Handle 'search' request: Searches user's chat history for a term.
            elif msg["action"] == "search":
                term = msg["target"]
                from_name = self.logged_sock2name[from_sock]
                print(f'Search request from {from_name} for "{term}"')
                if from_name in self.indices: # Check if user has a chat history index.
                    search_rslt_list = [x[-1] for x in self.indices[from_name].search(term)]
                    search_rslt = '\n'.join(search_rslt_list)
                    print(f'Server side search result: {search_rslt}')
                    mysend(from_sock, json.dumps({"action":"search", "results":search_rslt}))
                else: # User has no chat history index.
                    print(f"[Server Warning] No index found for {from_name} during search.")
                    mysend(from_sock, json.dumps({"action":"search", "results":"Search index not available."}))
            
            # Handle 'set_profile_pic' request: Updates user's profile picture URL.
            elif msg["action"] == "set_profile_pic":
                from_name = self.logged_sock2name[from_sock]
                pfp_url = msg.get("url")
                if pfp_url is not None: # Validate URL presence.
                    if from_name in self.user_profile_info:
                        self.user_profile_info[from_name]["pfp_url"] = pfp_url
                        status_payload = {"action": "set_profile_pic_status", "status": "ok", "detail": "Profile picture updated."}
                    else: # Should not happen if user is logged in, but handle defensively.
                        self.user_profile_info[from_name] = {"pfp_url": pfp_url}
                        status_payload = {"action": "set_profile_pic_status", "status": "ok", "detail": "Profile picture set."}
                    print(f"User {from_name} set PFP URL to: {pfp_url}")
                else: # URL missing in request.
                    status_payload = {"action": "set_profile_pic_status", "status": "error_bad_request", "detail": "Missing 'url' field."}
                mysend(from_sock, json.dumps(status_payload))
            
            # Handle 'start_ttt' request: Initiates a Tic-Tac-Toe game.
            elif msg["action"] == "start_ttt":
                self.board = [[0, 0, 0], [0, 0, 0], [0, 0, 0]] # Reset/Initialize board.
                from_name = self.logged_sock2name[from_sock]
                to_name = msg["target"]
                if to_name == from_name: # User trying to play against themselves.
                    mysend(from_sock, json.dumps({"action":"open_ttt", "status":"self"}))
                else: # Valid opponent.
                    print("Currently logged in:", list(self.logged_name2sock.keys()))
                    print("Looking for:", to_name)
                    if not hasattr(self, 'ttt_pairs'): # Initialize ttt_pairs if it doesn't exist.
                        self.ttt_pairs = {}
                    self.ttt_pairs[from_name] = to_name # Store player pair.
                    self.ttt_pairs[to_name] = from_name
                    to_sock = self.logged_name2sock[to_name]
                    # Notify both players to open the TTT game window, assigning symbols.
                    mysend(from_sock, json.dumps({"action":"open_ttt", "status":"ok", "from":from_name, "symbol":"X"}))
                    mysend(to_sock, json.dumps({"action":"open_ttt", "status":"ok", "from":from_name, "symbol":"O"}))
            
            # Handle 'move' request: Processes a Tic-Tac-Toe game move.
            elif msg["action"]=="move":
                from_name = self.logged_sock2name[from_sock]
                to_name = self.ttt_pairs[from_name]
                to_sock = self.logged_name2sock[to_name]
                row=int(msg["row"])
                column=int(msg["column"])
                # print(f"Server received move: {row},{column} from {from_name}") # Optional: less verbose log
                if row not in range(3) or column not in range(3): # Validate move coordinates.
                    print("Invalid move received: row/column out of range")
                    return
                
                symbol_from_client = msg.get("from") # Symbol ('X' or 'O') sent by the client.
                # print(f"Symbol in msg['from']: {symbol_from_client}") # Optional: less verbose log

                self.board[row][column]=symbol_from_client # Update board state.
                result=self.check_winners() # Check for win/tie/continue.
                # print(f"check_winners result: {result}") # Optional: less verbose log
                
                if result[0] == "win": # Game won.
                    winner_symbol = result[1]
                    # Determine winner's name based on the winning symbol.
                    actual_winner_name = from_name if symbol_from_client == winner_symbol else to_name
                    # print(f"Game won by {actual_winner_name} with symbol {winner_symbol}") # Optional: less verbose log
                    end_payload = {
                        "action": "end", "status": "win",
                        "winner": actual_winner_name, "winning_symbol": winner_symbol,
                        "board": self.board
                    }
                    mysend(to_sock, json.dumps(end_payload))
                    mysend(from_sock, json.dumps(end_payload))
                    self._record_game_result(actual_winner_name,
                                             to_name if actual_winner_name == from_name else from_name,
                                             is_tie=False)
                elif result[0] == "tie": # Game is a tie.
                    # print(f"Game is a tie. Board: {self.board}") # Optional: less verbose log
                    end_payload = {
                        "action": "end", "status": "tie",
                        "winner": None, "board": self.board
                    }
                    mysend(to_sock, json.dumps(end_payload))
                    mysend(from_sock, json.dumps(end_payload))
                    self._record_game_result(from_name, to_name, is_tie=True)
                else: # Game continues.
                    mysend(to_sock, json.dumps({"action":"update", "status":"your turn", "from":from_name, "turn": to_name, "row":msg["row"], "column":msg["column"]}))
                    mysend(from_sock, json.dumps({"action":"update", "status":"opponent turn", "from":from_name, "turn": to_name, "row":msg["row"], "column":msg["column"]}))
                
            # Handle 'disconnect' request: Disconnects a user from their current chat group.
            elif msg["action"] == "disconnect":
                from_name = self.logged_sock2name[from_sock]
                the_guys = self.group.list_me(from_name)
                self.group.disconnect(from_name) # Update group state.
                the_guys.remove(from_name)
                if len(the_guys) == 1: # If one person remains in the group, notify them.
                    g = the_guys.pop()
                    to_sock = self.logged_name2sock[g]
                    mysend(to_sock, json.dumps({"action":"disconnect"}))
            
            # Handle unknown actions.
            else:
                print(f"[Server Warning] Unknown action received from {client_identifier}: {msg.get('action')}")

        except ConnectionResetError: # Client connection was forcibly closed.
            client_identifier_on_error = self.logged_sock2name.get(from_sock)
            if not client_identifier_on_error:
                 try:
                     client_identifier_on_error = str(from_sock.getpeername())
                 except socket.error:
                     client_identifier_on_error = f"Unknown/Closed Socket ({from_sock.fileno()})"

            print(f"[Server Log] Client {client_identifier_on_error} forcibly closed connection (ConnectionResetError). Logging out.")
            if from_sock in self.logged_sock2name:
                self.logout(from_sock)
            else: # Clean up if error occurred for a non-fully-logged-in client.
                if from_sock in self.all_sockets: self.all_sockets.remove(from_sock)
                if from_sock in self.new_clients: self.new_clients.remove(from_sock)
                if from_sock.fileno() != -1:
                    try:
                        from_sock.close()
                        print(f"[Server Log] Closed socket for {client_identifier_on_error} after ConnectionResetError.")
                    except socket.error as close_err:
                         print(f"[Server Log] Error closing socket for {client_identifier_on_error} after ConnectionResetError: {close_err}")
            return # Stop processing for this socket.

        except (socket.error, BrokenPipeError) as e: # Other socket-related errors.
            client_identifier_on_error = self.logged_sock2name.get(from_sock)
            if not client_identifier_on_error:
                 try:
                     client_identifier_on_error = str(from_sock.getpeername())
                 except socket.error:
                     client_identifier_on_error = f"Unknown/Closed Socket ({from_sock.fileno()})"

            print(f"[Server Log] Socket error for client {client_identifier_on_error}: {e}. Logging out.")
            if from_sock in self.logged_sock2name:
                self.logout(from_sock)
            else: # Clean up if error occurred for a non-fully-logged-in client.
                if from_sock in self.all_sockets: self.all_sockets.remove(from_sock)
                if from_sock in self.new_clients: self.new_clients.remove(from_sock)
                if from_sock.fileno() != -1:
                    try:
                        from_sock.close()
                        print(f"[Server Log] Closed socket for {client_identifier_on_error} after {type(e).__name__}.")
                    except socket.error as close_err:
                         print(f"[Server Log] Error closing socket for {client_identifier_on_error} after {type(e).__name__}: {close_err}")
            return

#==============================================================================
# Main server loop.
#==============================================================================
    def run(self):
        print ('[Server Log] Starting server...')
        loop_count = 0
        while(1): # Loop indefinitely to handle client connections and messages.
           loop_count += 1
           print(f'[Server Log] ----- Loop {loop_count} Start -----')
           print(f'[Server Log] Sockets to check: {len(self.all_sockets)}')
           # Use select to monitor sockets for readability with a timeout.
           read,write,error=select.select(self.all_sockets,[],[], 1.0)
           print(f'[Server Log] select() returned {len(read)} readable sockets.')

           # Process messages from already logged-in clients.
           print('[Server Log] Checking logged clients..')
           logged_clients_to_process = [logc for logc in list(self.logged_name2sock.values()) if logc in read]
           print(f'[Server Log] Found {len(logged_clients_to_process)} logged clients with data.')
           for logc in logged_clients_to_process:
               print(f'[Server Log] Handling message from logged client: {self.logged_sock2name.get(logc, "Unknown")}')
               self.handle_msg(logc)

           # Process login attempts from new clients.
           print('[Server Log] Checking new clients..')
           new_clients_to_process = [newc for newc in self.new_clients[:] if newc in read] # Iterate over a copy for safe removal.
           print(f'[Server Log] Found {len(new_clients_to_process)} new clients with data.')
           for newc in new_clients_to_process:
               print(f'[Server Log] Attempting login for new client: {newc.getpeername() if newc.fileno() != -1 else "Closed Socket"}')
               self.login(newc)

           # Accept new client connections.
           print('[Server Log] Checking for new connections..')
           if self.server in read :
               print('[Server Log] Server socket is readable - accepting new connection...')
               try:
                   sock, address = self.server.accept()
                   print(f'[Server Log] Accepted connection from {address}')
                   self.new_client(sock) # Register the new client.
               except Exception as e:
                   print(f'[Server Log] ERROR accepting connection: {e}')
           print(f'[Server Log] ----- Loop {loop_count} End -----')

def main():
    server=Server()
    server.run()

main()
