
import time
import socket
import select
import sys
import string
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
        self.board = [] # For the single game in soph test version

        # Tic-Tac-Toe specific attributes for stats
        self.game_stats = {}   # Stores player game statistics (wins, losses, streaks)
        self.stats_file = "soph_test_tictactoe_stats.json" # Separate stats file
        self._load_game_stats() # Load stats on server startup

        #start server
        self.server=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(SERVER)
        self.server.listen(5)
        self.all_sockets.append(self.server)
        #initialize past chat indices
        self.indices={}
        # sonnet
        # self.sonnet_f = open('AllSonnets.txt.idx', 'rb')
        # self.sonnet = pkl.load(self.sonnet_f)
        # self.sonnet_f.close()
        try:
            self.sonnet = indexer.PIndex("AllSonnets.txt")
        except Exception as e:
            print(f"ERROR: Failed to initialize PIndex: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1) # Exit explicitly if PIndex fails
    def new_client(self, sock):
        #add to all sockets and to new clients
        print('new client...')
        sock.setblocking(0)
        self.new_clients.append(sock)
        self.all_sockets.append(sock)

    def login(self, sock):
        #read the msg that should have login code plus username
        try:
            raw_msg = myrecv(sock) # Store raw message first
            if not raw_msg: # Client disconnected before sending login
                print(f"Client {sock.getpeername()} disconnected before sending login info.")
                # Ensure sock is removed from lists it might be in
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
                        #move socket from new clients list to logged clients
                        self.new_clients.remove(sock)
                        #add into the name to sock mapping
                        self.logged_name2sock[name] = sock
                        self.logged_sock2name[sock] = name
                        #load chat history of that user
                        if name not in self.indices.keys():
                            try:
                                self.indices[name]=pkl.load(open(name+'.idx','rb'))
                            except IOError: #chat index does not exist, then create one
                                self.indices[name] = indexer.Index(name)
                        print(name + ' logged in')
                        self.group.join(name)
                        # Initialize profile info if not present
                        if name not in self.user_profile_info:
                            self.user_profile_info[name] = {"pfp_url": None}
                        mysend(sock, json.dumps({"action":"login", "status":"ok"}))
                    else: #a client under this name has already logged in
                        mysend(sock, json.dumps({"action":"login", "status":"duplicate"}))
                        print(name + ' duplicate login attempt')
                else:
                    print ('wrong code received')
            else: #client died unexpectedly
                # This case might be redundant if raw_msg check catches disconnection
                self.logout(sock)
        except json.JSONDecodeError:
            peer_name_info = sock.getpeername() if sock.fileno() != -1 else "already closed socket"
            print(f"Login: Received malformed JSON from {peer_name_info}.")
            if sock.fileno() != -1: # Check if socket is still open
                if sock in self.new_clients: self.new_clients.remove(sock)
                if sock in self.all_sockets: self.all_sockets.remove(sock)
                sock.close()
            return # Prevent further processing for this socket
        except Exception as e: # Catch other potential errors during login
            peer_name_info = sock.getpeername() if sock.fileno() != -1 else "already closed socket"
            print(f"Error during login for {peer_name_info}: {e}")
            if sock.fileno() != -1:
                if sock in self.new_clients: self.new_clients.remove(sock)
                if sock in self.all_sockets: self.all_sockets.remove(sock)
                sock.close()
            return

    def logout(self, sock):
        #remove sock from all lists
        name = self.logged_sock2name[sock]
        pkl.dump(self.indices[name], open(name + '.idx','wb'))
        del self.indices[name]
        del self.logged_name2sock[name]
        del self.logged_sock2name[sock]
        self.all_sockets.remove(sock)
        self.group.leave(name)
        sock.close()

    # ----------------- Tic-Tac-Toe Stats Helper Methods (ported from main) -----------------
    def _load_game_stats(self):
        try:
            with open(self.stats_file, 'r') as f:
                self.game_stats = json.load(f)
            print(f"[Server SophTest] Tic-Tac-Toe stats loaded from {self.stats_file}.")
        except FileNotFoundError:
            print(f"[Server SophTest] Stats file '{self.stats_file}' not found. Initializing new stats.")
            self.game_stats = {}
        except json.JSONDecodeError:
            print(f"[Server SophTest] Error decoding JSON from '{self.stats_file}'. Initializing new stats.")
            self.game_stats = {}

    def _save_game_stats(self):
        try:
            with open(self.stats_file, 'w') as f:
                json.dump(self.game_stats, f, indent=4)
            print(f"[Server SophTest] Tic-Tac-Toe stats saved to {self.stats_file}.")
        except IOError as e:
            print(f"[Server SophTest] Error saving Tic-Tac-Toe stats to '{self.stats_file}': {e}")

    def _get_game_id(self, player1_name, player2_name):
        # Create a consistent game ID regardless of who initiated
        return "_vs_".join(sorted([player1_name, player2_name]))

    def _initialize_player_stats(self, player_name):
        if player_name not in self.game_stats:
            self.game_stats[player_name] = {"wins": 0, "losses": 0, "current_streak": 0, "max_streak": 0, "ties": 0}
            
    def _record_game_result(self, game_id_unused, winner_name, loser_name, is_tie=False):
        # game_id is not strictly needed for soph_test version if only one game at a time,
        # but we use its components (winner_name, loser_name)
        print(f"[Server SophTest] Recording game result: Winner: {winner_name}, Loser: {loser_name}, Tie: {is_tie}")
        
        # Determine players involved for stat initialization
        players_in_game = []
        if winner_name: players_in_game.append(winner_name)
        if loser_name: players_in_game.append(loser_name)
        if is_tie: # If tie, winner_name and loser_name might be None, get from ttt_pairs
            # This assumes ttt_pairs is populated correctly for the current game
            # This part is a bit fragile for 'tie' if ttt_pairs isn't perfectly in sync or if players are not in it.
            # A better approach would be to pass player names directly if possible.
            # For now, let's try to derive from ttt_pairs if it's a tie and names are missing.
            if not winner_name and not loser_name and hasattr(self, 'ttt_pairs') and self.ttt_pairs:
                # This is a simplification; ttt_pairs might not hold the current game if not cleared.
                # A more robust way would be to pass player1 and player2 names to _record_game_result.
                # For now, we'll rely on winner/loser names being passed.
                # If it's a tie, the calling function should pass the two player names.
                # Let's assume the calling function (move handler) will provide the names for a tie.
                pass


        for p_name in players_in_game:
             self._initialize_player_stats(p_name)

        announcement = ""
        if is_tie:
            # For a tie, we need both player names. The 'move' handler should provide them.
            # Let's assume winner_name and loser_name are the two players in a tie for now.
            # This needs the calling function to pass (player1, player2, is_tie=True)
            # For the current structure of soph_test, if it's a tie, from_name and to_name from 'move' are the players.
            player1_for_tie = winner_name # Placeholder, should be actual player1
            player2_for_tie = loser_name  # Placeholder, should be actual player2
            
            # This part needs the actual player names involved in the tie.
            # The 'move' handler will need to pass these.
            # For now, if winner_name and loser_name are passed as the two players in a tie:
            if winner_name and loser_name: # Assuming these are the two players in a tie
                 self._initialize_player_stats(winner_name)
                 self._initialize_player_stats(loser_name)
                 self.game_stats[winner_name]["ties"] = self.game_stats[winner_name].get("ties", 0) + 1
                 self.game_stats[loser_name]["ties"] = self.game_stats[loser_name].get("ties", 0) + 1
                 announcement = f"The Tic-Tac-Toe game between {winner_name} and {loser_name} was a tie!"
            else: # Fallback if player names for tie aren't clear
                announcement = "A Tic-Tac-Toe game ended in a tie!"

        else: # There is a winner
            if winner_name: # Ensure winner_name is not None
                self._initialize_player_stats(winner_name)
                self.game_stats[winner_name]["wins"] += 1
                self.game_stats[winner_name]["current_streak"] += 1
                if self.game_stats[winner_name]["current_streak"] > self.game_stats[winner_name]["max_streak"]:
                    self.game_stats[winner_name]["max_streak"] = self.game_stats[winner_name]["current_streak"]
                
                if loser_name:
                    self._initialize_player_stats(loser_name)
                    self.game_stats[loser_name]["losses"] += 1
                    self.game_stats[loser_name]["current_streak"] = 0
                
                announcement = f"{winner_name} has won a game of Tic-Tac-Toe! Current win streak: {self.game_stats[winner_name]['current_streak']}."
            else: # Should not happen if not a tie
                announcement = "A Tic-Tac-Toe game has ended."


        self._save_game_stats()
        
        if announcement:
            print(f"[Server SophTest] Broadcasting game result: {announcement}")
            for name, sock_to_send in self.logged_name2sock.items():
                system_msg_payload = {"action": "exchange", "from": "[GameServer]", "message": announcement}
                mysend(sock_to_send, json.dumps(system_msg_payload))
        
    def check_winners(self,board_arg): # Renamed argument to avoid confusion with self.board
        # It's generally better not to reassign self.board here if board_arg is the one to check
        # For this debugging, we'll assume self.board is the one being actively used and updated by 'move'
        # and that board_arg is indeed self.board when called from 'move'.
        # If self.board is the single source of truth, the 'board_arg' parameter is somewhat redundant here.
        # However, to stick to the original structure for debugging:
        self.board = board_arg

        print(f"DEBUG check_winners: Board state: {self.board}")

        # Check rows
        for r in range(3):
            if self.board[r][0] == self.board[r][1] and self.board[r][1] == self.board[r][2] and self.board[r][0] != 0:
                print(f"DEBUG: Winning row found: {self.board[r]} by symbol {self.board[r][0]}")
                return ["win", self.board[r][0]]
        # Check columns
        for c in range(3):
            if self.board[0][c] == self.board[1][c] and self.board[1][c] == self.board[2][c] and self.board[0][c] != 0:
                print(f"DEBUG: Winning column found: {[self.board[0][c], self.board[1][c], self.board[2][c]]} by symbol {self.board[0][c]}")
                return ["win", self.board[0][c]]
        # Check main diagonal
        if self.board[0][0] == self.board[1][1] and self.board[1][1] == self.board[2][2] and self.board[0][0] != 0:
            print(f"DEBUG: Winning main diagonal found: {[self.board[0][0], self.board[1][1], self.board[2][2]]} by symbol {self.board[0][0]}")
            return ["win", self.board[0][0]]
        # Check anti-diagonal
        if self.board[0][2] == self.board[1][1] and self.board[1][1] == self.board[2][0] and self.board[0][2] != 0:
            print(f"DEBUG: Winning anti-diagonal found: {[self.board[0][2], self.board[1][1], self.board[2][0]]} by symbol {self.board[0][2]}")
            return ["win", self.board[0][2]]
        
        # Check for Tie (no empty cells left and no winner yet)
        # This part was missing from the original check_winners
        is_full = True
        for r in range(3):
            for c in range(3):
                if self.board[r][c] == 0: # Assuming 0 is empty
                    is_full = False
                    break
            if not is_full:
                break
        
        if is_full:
            print(f"DEBUG: Board is full, declaring a tie. Board: {self.board}")
            return ["tie"] # Explicitly return a tie status

        return ["continue"]

        
        
        
#==============================================================================
# main command switchboard
#==============================================================================
    def handle_msg(self, from_sock):
        #read msg code
        try:
            # Get client identifier early, useful for logging even if recv fails
            client_identifier = self.logged_sock2name.get(from_sock)
            if not client_identifier:
                try:
                    # Use a placeholder if getpeername also fails (socket might be totally broken)
                    client_identifier = str(from_sock.getpeername())
                except socket.error:
                    client_identifier = f"Unknown/Pre-Login Socket ({from_sock.fileno()})"

            print(f"[Server Log] Attempting to receive message from {client_identifier}...")
            msg_content = myrecv(from_sock)
            print(f"[Server Log] Received from {client_identifier}: {len(msg_content) if msg_content is not None else 'None'} bytes")

            if not msg_content: # Client disconnected gracefully (myrecv returned '')
                print(f"[Server Log] Client {client_identifier} disconnected gracefully (received empty message). Logging out.")
                if from_sock in self.logged_sock2name: # Only logout if they were logged in
                     self.logout(from_sock)
                else: # If not logged_sock2name, it might be a new_client that disconnected weirdly
                    if from_sock in self.all_sockets: self.all_sockets.remove(from_sock)
                    if from_sock in self.new_clients: self.new_clients.remove(from_sock)
                    if from_sock.fileno() != -1: from_sock.close()
                return

            # Proceed only if msg_content is not empty
            try:
                msg = json.loads(msg_content) # Parse here
                print(f"[Server Log] Parsed JSON from {client_identifier}: action={msg.get('action', 'N/A')}")
            except json.JSONDecodeError:
                print(f"[Server Log] Handle_msg: Received malformed JSON from {client_identifier}. Content: '{msg_content[:100]}...'")
                # Optionally logout if malformed JSON is critical
                # self.logout(from_sock)
                return # Don't process further

            # --- Start of main message handling logic ---
            #==============================================================================
            # handle connect request
            #==============================================================================
            if msg["action"] == "connect":
                to_name = msg["target"]
                from_name = self.logged_sock2name[from_sock]
                if to_name == from_name:
                    msg_resp = json.dumps({"action":"connect", "status":"self"})
                elif self.group.is_member(to_name):
                    to_sock = self.logged_name2sock[to_name]
                    self.group.connect(from_name, to_name)
                    the_guys = self.group.list_me(from_name)
                    msg_resp = json.dumps({"action":"connect", "status":"success"})
                    for g in the_guys[1:]:
                        to_sock_peer = self.logged_name2sock[g]
                        mysend(to_sock_peer, json.dumps({"action":"connect", "status":"request", "from":from_name}))
                else:
                    msg_resp = json.dumps({"action":"connect", "status":"no-user"})
                mysend(from_sock, msg_resp)
            #==============================================================================
            # handle message exchange
            #==============================================================================
            elif msg["action"] == "exchange":
                from_name = self.logged_sock2name[from_sock]
                processed_msg = text_proc(msg["message"], from_name)
                if from_name in self.indices:
                    self.indices[from_name].add_msg_and_index(processed_msg)
                else:
                    print(f"[Server Warning] No index found for sender {from_name} during exchange.")

                print(f"[Server] Broadcasting message from {from_name} to all users.")
                for name, to_sock in self.logged_name2sock.items():
                    if name != from_name:
                        if name in self.indices:
                             self.indices[name].add_msg_and_index(processed_msg)
                        else:
                             print(f"[Server Warning] No index found for recipient {name} during exchange.")
                        mysend(to_sock, json.dumps({"action":"exchange", "from": msg["from"], "message": msg["message"]}))
            #==============================================================================
            # listing available peers
            #==============================================================================
            elif msg["action"] == "list":
                user_list_data = []
                for name in self.logged_name2sock.keys():
                    pfp_url = self.user_profile_info.get(name, {}).get("pfp_url")
                    user_list_data.append({"name": name, "pfp_url": pfp_url})
                mysend(from_sock, json.dumps({"action":"list", "results": user_list_data}))
            #==============================================================================
            # retrieve a sonnet
            #==============================================================================
            elif msg["action"] == "poem":
                poem_indx = int(msg["target"])
                from_name = self.logged_sock2name[from_sock]
                print(f"{from_name} asks for poem {poem_indx}")
                try:
                    poem = self.sonnet.get_poem(poem_indx)
                    poem_text = '\n'.join(poem)
                    print('Sending poem:\n', poem_text)
                    mysend(from_sock, json.dumps({"action":"poem", "results":poem_text}))
                except IndexError:
                     mysend(from_sock, json.dumps({"action":"poem", "results":"Poem index out of range."}))
                except Exception as e:
                     print(f"Error retrieving poem {poem_indx}: {e}")
                     mysend(from_sock, json.dumps({"action":"poem", "results":"Error retrieving poem."}))
            #==============================================================================
            # time
            #==============================================================================
            elif msg["action"] == "time":
                ctime = time.strftime("%I:%M%p", time.localtime())
                mysend(from_sock, json.dumps({"action":"time", "results":ctime}))
            #==============================================================================
            # handle private message request
            #==============================================================================
            elif msg["action"] == "private_message":
                target_username = msg.get("to")
                message_text = msg.get("message")
                if not target_username or not message_text:
                    status_payload = {"action": "private_message_status", "to": target_username or "N/A", "status": "error_bad_request", "detail": "Missing 'to' or 'message' field."}
                    mysend(from_sock, json.dumps(status_payload))
                else:
                    sender_username = self.logged_sock2name[from_sock]
                    if target_username == sender_username:
                        status_payload = {"action": "private_message_status", "to": target_username, "status": "error_self_message", "detail": "Cannot send private message to yourself."}
                        mysend(from_sock, json.dumps(status_payload))
                    elif target_username in self.logged_name2sock:
                        target_sock = self.logged_name2sock[target_username]
                        payload_for_recipient = {"action": "incoming_private_message", "from": f"[PM from {sender_username}]", "message": message_text}
                        mysend(target_sock, json.dumps(payload_for_recipient))
                        status_payload_to_sender = {"action": "private_message_status", "to": target_username, "status": "sent", "detail": f"PM sent to {target_username}."}
                        mysend(from_sock, json.dumps(status_payload_to_sender))
                    else:
                        status_payload = {"action": "private_message_status", "to": target_username, "status": "error_user_offline", "detail": f"User {target_username} is not online."}
                        mysend(from_sock, json.dumps(status_payload))
            #==============================================================================
            # search
            #==============================================================================
            elif msg["action"] == "search":
                term = msg["target"]
                from_name = self.logged_sock2name[from_sock]
                print(f'Search request from {from_name} for "{term}"')
                if from_name in self.indices:
                    search_rslt_list = [x[-1] for x in self.indices[from_name].search(term)]
                    search_rslt = '\n'.join(search_rslt_list)
                    print(f'Server side search result: {search_rslt}')
                    mysend(from_sock, json.dumps({"action":"search", "results":search_rslt}))
                else:
                    print(f"[Server Warning] No index found for {from_name} during search.")
                    mysend(from_sock, json.dumps({"action":"search", "results":"Search index not available."}))
            #==============================================================================
            # set profile picture
            #==============================================================================
            elif msg["action"] == "set_profile_pic":
                from_name = self.logged_sock2name[from_sock]
                pfp_url = msg.get("url")
                if pfp_url is not None:
                    if from_name in self.user_profile_info:
                        self.user_profile_info[from_name]["pfp_url"] = pfp_url
                        status_payload = {"action": "set_profile_pic_status", "status": "ok", "detail": "Profile picture updated."}
                    else:
                        self.user_profile_info[from_name] = {"pfp_url": pfp_url}
                        status_payload = {"action": "set_profile_pic_status", "status": "ok", "detail": "Profile picture set."}
                    print(f"User {from_name} set PFP URL to: {pfp_url}")
                else:
                    status_payload = {"action": "set_profile_pic_status", "status": "error_bad_request", "detail": "Missing 'url' field."}
                mysend(from_sock, json.dumps(status_payload))
            #==============================================================================
            # start ttt
            #==============================================================================   
            elif msg["action"] == "start_ttt":
                self.board = [[0, 0, 0],
                            [0, 0, 0],
                            [0, 0, 0]]
                from_name = self.logged_sock2name[from_sock]
                to_name = msg["target"]
                if to_name == from_name:
                    mysend(from_sock, json.dumps({"action":"open_ttt", "status":"self"}))
                else:
                    print("Currently logged in:", list(self.logged_name2sock.keys()))
                    print("Looking for:", to_name)
                    if not hasattr(self, 'ttt_pairs'):
                        self.ttt_pairs = {}
                    self.ttt_pairs[from_name] = to_name
                    self.ttt_pairs[to_name] = from_name
                    to_sock = self.logged_name2sock[to_name]
                    mysend(from_sock, json.dumps({"action":"open_ttt", "status":"ok", "from":from_name, "symbol":"X"}))
                    mysend(to_sock, json.dumps({"action":"open_ttt", "status":"ok", "from":from_name, "symbol":"O"}))
            #==============================================================================
            # handle moves
            #==============================================================================  
            elif msg["action"]=="move":
                
                from_name = self.logged_sock2name[from_sock]
                to_name = self.ttt_pairs[from_name]
                to_sock = self.logged_name2sock[to_name]
                row=int(msg["row"])
                column=int(msg["column"])
                print(f"#================================================server got the move {row}{column}")
                if row not in range(3) or column not in range(3):
                    print("Invalid move received: row/column out of range")
                    return
                
                # DEBUG: Print what the server is receiving as the symbol
                symbol_from_client = msg.get("from")
                print(f"DEBUG: Server received move from client. Symbol in msg['from']: {symbol_from_client}")

                self.board[row][column]=symbol_from_client # Use the received symbol
                result=self.check_winners(self.board) # check_winners now returns ["win", symbol], ["tie"], or ["continue"]
                print(f"DEBUG: check_winners result: {result}")
                
                if result[0] == "win":
                    winner_symbol = result[1] # This is the symbol that won, e.g., "X" or "O"
                    # Determine winner_name based on the symbol. This assumes self.ttt_pairs and client symbols are consistent.
                    # This part is a bit tricky with the current ttt_pairs structure if symbols aren't directly mapped to names server-side.
                    # For now, we'll assume from_name is the winner if their symbol (symbol_from_client) matches winner_symbol.
                    # This might need refinement if symbol assignment isn't strictly tied to from_name making the move.
                    actual_winner_name = from_name if symbol_from_client == winner_symbol else to_name

                    print(f"DEBUG: Game won by {actual_winner_name} with symbol {winner_symbol}")
                    end_payload = {
                        "action": "end",
                        "status": "win",
                        "winner": actual_winner_name, # Name of the winner
                        "winning_symbol": winner_symbol, # Symbol that won
                        "board": self.board # Send final board state
                    }
                    mysend(to_sock, json.dumps(end_payload))
                    mysend(from_sock, json.dumps(end_payload))
                    self._record_game_result(None, actual_winner_name, to_name if actual_winner_name == from_name else from_name, is_tie=False)
                elif result[0] == "tie":
                    print(f"DEBUG: Game is a tie. Board: {self.board}")
                    end_payload = {
                        "action": "end",
                        "status": "tie",
                        "winner": None, # No winner in a tie
                        "board": self.board # Send final board state
                    }
                    mysend(to_sock, json.dumps(end_payload))
                    mysend(from_sock, json.dumps(end_payload))
                    # For a tie, both from_name and to_name are involved.
                    self._record_game_result(None, from_name, to_name, is_tie=True)
                else: # "continue"
                    mysend(to_sock, json.dumps({"action":"update", "status":"your turn", "from":from_name, "turn": to_name, "row":msg["row"], "column":msg["column"]}))
                    mysend(from_sock, json.dumps({"action":"update", "status":"opponent turn", "from":from_name, "turn": to_name, "row":msg["row"], "column":msg["column"]}))
                
            #==============================================================================
            # disconnect request
            #==============================================================================
            elif msg["action"] == "disconnect":
                from_name = self.logged_sock2name[from_sock]
                the_guys = self.group.list_me(from_name)
                self.group.disconnect(from_name)
                the_guys.remove(from_name)
                if len(the_guys) == 1:
                    g = the_guys.pop()
                    to_sock = self.logged_name2sock[g]
                    mysend(to_sock, json.dumps({"action":"disconnect"}))
            #==============================================================================
            # Unknown action
            #==============================================================================
            else:
                print(f"[Server Warning] Unknown action received from {client_identifier}: {msg.get('action')}")
                # Optionally send an error back to the client
                # mysend(from_sock, json.dumps({"action":"error", "detail": f"Unknown action: {msg.get('action')}"}))

        except ConnectionResetError:
            # Get client identifier again, as it might not have been set before the error
            client_identifier_on_error = self.logged_sock2name.get(from_sock)
            if not client_identifier_on_error:
                 try:
                     client_identifier_on_error = str(from_sock.getpeername())
                 except socket.error:
                     client_identifier_on_error = f"Unknown/Closed Socket ({from_sock.fileno()})"

            print(f"[Server Log] Client {client_identifier_on_error} forcibly closed connection (ConnectionResetError). Logging out.")
            if from_sock in self.logged_sock2name:
                self.logout(from_sock)
            else: # Handle cases where the error happens before full login or for unknown sockets
                if from_sock in self.all_sockets: self.all_sockets.remove(from_sock)
                if from_sock in self.new_clients: self.new_clients.remove(from_sock)
                if from_sock.fileno() != -1:
                    try:
                        from_sock.close()
                        print(f"[Server Log] Closed socket for {client_identifier_on_error} after ConnectionResetError.")
                    except socket.error as close_err:
                         print(f"[Server Log] Error closing socket for {client_identifier_on_error} after ConnectionResetError: {close_err}")
            return # Stop processing for this socket

        except (socket.error, BrokenPipeError) as e: # Catch other potential socket errors
            client_identifier_on_error = self.logged_sock2name.get(from_sock)
            if not client_identifier_on_error:
                 try:
                     client_identifier_on_error = str(from_sock.getpeername())
                 except socket.error:
                     client_identifier_on_error = f"Unknown/Closed Socket ({from_sock.fileno()})"

            print(f"[Server Log] Socket error for client {client_identifier_on_error}: {e}. Logging out.")
            if from_sock in self.logged_sock2name:
                self.logout(from_sock)
            else:
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
# main loop, loops *forever*
#==============================================================================
    def run(self):
        print ('[Server Log] Starting server...')
        loop_count = 0
        while(1):
           loop_count += 1
           print(f'[Server Log] ----- Loop {loop_count} Start -----')
           print(f'[Server Log] Sockets to check: {len(self.all_sockets)}')
           read,write,error=select.select(self.all_sockets,[],[], 1.0) # Add timeout
           print(f'[Server Log] select() returned {len(read)} readable sockets.')

           print('[Server Log] Checking logged clients..')
           logged_clients_to_process = [logc for logc in list(self.logged_name2sock.values()) if logc in read]
           print(f'[Server Log] Found {len(logged_clients_to_process)} logged clients with data.')
           for logc in logged_clients_to_process:
               print(f'[Server Log] Handling message from logged client: {self.logged_sock2name.get(logc, "Unknown")}')
               self.handle_msg(logc)

           print('[Server Log] Checking new clients..')
           new_clients_to_process = [newc for newc in self.new_clients[:] if newc in read]
           print(f'[Server Log] Found {len(new_clients_to_process)} new clients with data.')
           for newc in new_clients_to_process:
               print(f'[Server Log] Attempting login for new client: {newc.getpeername() if newc.fileno() != -1 else "Closed Socket"}')
               self.login(newc)

           print('[Server Log] Checking for new connections..')
           if self.server in read :
               print('[Server Log] Server socket is readable - accepting new connection...')
               #new client request
               try:
                   sock, address = self.server.accept()
                   print(f'[Server Log] Accepted connection from {address}')
                   self.new_client(sock)
               except Exception as e:
                   print(f'[Server Log] ERROR accepting connection: {e}')
           print(f'[Server Log] ----- Loop {loop_count} End -----')

def main():
    server=Server()
    server.run()

main()
