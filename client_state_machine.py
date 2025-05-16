from chat_utils import *
import json

class ClientSM:
    def __init__(self, s):
        self.state = S_OFFLINE
        self.peer = ''
        self.me = ''
        self.out_msg = ''
        self.s = s

    def set_state(self, state):
        self.state = state

    def get_state(self):
        return self.state

    def set_myname(self, name):
        self.me = name

    def get_myname(self):
        return self.me

    def connect_to(self, peer):
        msg = json.dumps({"action":"connect", "target":peer})
        mysend(self.s, msg)
        response = json.loads(myrecv(self.s))
        if response["status"] == "success":
            self.peer = peer
            self.out_msg += 'You are connected with '+ self.peer + '\n'
            return (True)
        elif response["status"] == "busy":
            self.out_msg += 'User is busy. Please try again later\n'
        elif response["status"] == "self":
            self.out_msg += 'Cannot talk to yourself (sick)\n'
        else:
            self.out_msg += 'User is not online, try again later\n'
        return(False)

    def disconnect(self):
        msg = json.dumps({"action":"disconnect"})
        mysend(self.s, msg)
        self.out_msg += 'You are disconnected from ' + self.peer + '\n'
        self.peer = ''
        

    def proc(self, my_msg, peer_msg):
        """
        Processes incoming messages from the server and local user commands.
        Updates the client's state and prepares output messages for the GUI.
        """
        self.out_msg = '' # Reset output message buffer.

        processed_my_msg_as_command = False # Flag to track if my_msg was a command.
        
        # Process messages received from the server (peer_msg).
        if len(peer_msg) > 0:
                peer_msg = json.loads(peer_msg) # Parse JSON message from server.
                if peer_msg["action"] == "open_ttt": # Server initiated Tic-Tac-Toe game.
                    self.symbol = peer_msg["symbol"]
                    self.out_msg += f"Received Tic Tac Toe request from {peer_msg['from']}.\n"
                    self.out_msg += f"OPEN_TTT: {peer_msg.get("from")}\n " # Signal GUI to open TTT window.
                    self.out_msg += "opponent turn "+ self.symbol # Initial turn status.
                elif peer_msg["action"]=="update" and peer_msg["status"]=="your turn": # Opponent made a move, now it's my turn.
                    self.out_msg += "myturn "+ peer_msg["from"]+" "+ peer_msg["row"] +" "+ peer_msg["column"] # Signal GUI about opponent's move.
                    # Note: Original comment about return was here, removed as it's not returning.
                elif peer_msg["action"] == "end": # Tic-Tac-Toe game ended.
                    status = peer_msg.get("status")
                    winner_name = peer_msg.get("winner")
                    final_board = peer_msg.get("board", [["","",""],["","",""],["","",""]])
                    if status == "win":
                        self.out_msg = f"GAME_OVER_UPDATE:{json.dumps({'winner': winner_name, 'status': 'win', 'board': final_board})}"
                    elif status == "tie":
                        self.out_msg = f"GAME_OVER_UPDATE:{json.dumps({'winner': None, 'status': 'tie', 'board': final_board})}"
                    # No return here, allow my_msg processing if any (though unlikely during game end notification)
                
        if len(my_msg) > 0:
            # These commands are available if logged in or chatting
            if self.state == S_LOGGEDIN or self.state == S_CHATTING:
                move_lst= my_msg.split()
                if move_lst[0]=="move" and len(move_lst) >= 5: # User made a Tic-Tac-Toe move.
                    row= move_lst[1]
                    column= move_lst[2]
                    # move_lst[3] is the literal string "from", move_lst[4] is the symbol ("X" or "O").
                    actual_symbol = move_lst[4]
                    
                    # Server expects the player's symbol in the "from" field for a "move" action.
                    mysend(self.s, json.dumps({"action": "move", "row": row, "column": column, "from": actual_symbol}))
                    response = json.loads(myrecv(self.s)) # Expect a response from the server after the move.
                    if response["status"] == "opponent turn":
                        self.out_msg += "\n oppo nent turn "+ response.get("turn")
                    elif response["status"] == "your turn": # This case might occur if server logic changes.
                        self.out_msg += "\n your turn "+ response.get("turn")
                    elif response["status"] == "win": # Game ended with a win.
                        winner_name = response.get("winner", "Unknown")
                        final_board = response.get("board", [["","",""],["","",""],["","",""]])
                        self.out_msg += f"\nGAME_OVER_UPDATE:{json.dumps({'winner': winner_name, 'status': 'win', 'board': final_board})}"
                    elif response["status"] == "tie": # Game ended with a tie.
                        final_board = response.get("board", [["","",""],["","",""],["","",""]])
                        self.out_msg += f"\nGAME_OVER_UPDATE:{json.dumps({'winner': None, 'status': 'tie', 'board': final_board})}"
                    
                    else: # Unexpected response status.
                        pass # Or handle unexpected status.
                    # Note: Original commented-out state change was here.
                        
                elif my_msg == 'q': # Quit command.
                    self.out_msg += 'See you next time!\n'
                    self.state = S_OFFLINE
                    processed_my_msg_as_command = True
                elif my_msg == 'time': # Time command.
                    mysend(self.s, json.dumps({"action":"time"}))
                    time_in = json.loads(myrecv(self.s))["results"]
                    self.out_msg += f"Current Time: {time_in}\n"
                    processed_my_msg_as_command = True
                elif my_msg == 'who': # Who command (list online users).
                    mysend(self.s, json.dumps({"action":"list"}))
                    response_json_str = myrecv(self.s)
                    if response_json_str:
                        try:
                            response_data = json.loads(response_json_str)
                            user_list_structured = response_data["results"]
                            # Prefix with "USER_LIST_STRUCT:" for GUI to handle popup.
                            self.out_msg = "USER_LIST_STRUCT:" + json.dumps(user_list_structured)
                        except (json.JSONDecodeError, KeyError) as e:
                            self.out_msg = "SYSTEM: Error parsing user list from server.\n"
                    else:
                        self.out_msg = "SYSTEM: No response from server for user list.\n"
                    processed_my_msg_as_command = True
                    
                # Tic-Tac-Toe start command.
                elif my_msg.startswith("ttt"):
                    target_player = my_msg[3:].strip()
                    if target_player:
                        mysend(self.s, json.dumps({"action": "start_ttt", "target": target_player}))
                        response = json.loads(myrecv(self.s))
                        if response.get("status") == "ok":
                            self.out_msg += f"Tic Tac Toe request sent to {target_player}.\n"
                            if response["action"] == "open_ttt": # Server confirms game start.
                                self.symbol= response.get("symbol", "X") # Get assigned symbol.
                                self.out_msg += f"Request approved. Game on!\n"
                                self.out_msg += f"OPEN_TTT: {response.get("from")} " # Signal GUI.
                                self.out_msg += self.symbol
                        else: # Server could not start TTT.
                            self.out_msg += f"Could not start TTT with {target_player}: {response.get('reason', 'Unknown error')}\n"
                    else:
                        self.out_msg += "Invalid TTT command format. Use: ttt <username>\n"
                    processed_my_msg_as_command = True
                    
                  
                elif my_msg.startswith("/setpfp "):
                    try:
                        parts = my_msg.split(" ", 1)
                        if len(parts) == 2:
                            pfp_url = parts[1].strip()
                            if pfp_url:
                                mysend(self.s, json.dumps({"action": "set_profile_pic", "url": pfp_url}))
                                response_json = myrecv(self.s)
                                if response_json:
                                    response = json.loads(response_json)
                                    if response.get("action") == "set_profile_pic_status":
                                        self.out_msg += f"[PFP Status: {response.get('detail', response.get('status', 'Unknown status'))}]\n"
                                    else:
                                        self.out_msg += "[PFP Status: Received unexpected server response type]\n"
                                else:
                                    self.out_msg += "[PFP Status: No response from server]\n"
                            else:
                                self.out_msg += "[PFP Error: URL cannot be empty.]\n"
                        else:
                            self.out_msg += "[PFP Error: Invalid /setpfp command format. Use /setpfp <URL>]\n"
                    except Exception as e:
                        self.out_msg += f"[PFP Error: {str(e)}]\n"
                    processed_my_msg_as_command = True
                    
                elif my_msg[0] == '?': # Search
                    term = my_msg[1:].strip()
                    mysend(self.s, json.dumps({"action":"search", "target":term}))
                    search_rslt = json.loads(myrecv(self.s))["results"].strip()
                    if (len(search_rslt)) > 0:
                        self.out_msg += search_rslt + '\n\n'
                    else:
                        self.out_msg += '\'' + term + '\'' + ' not found\n\n'
                    processed_my_msg_as_command = True
                    
                elif my_msg.startswith('p '): # Poem
                    parts = my_msg.split()
                    poem_idx_str = ""
                    if len(parts) == 2 and parts[0] == 'p' and parts[1].isdigit():
                        poem_idx_str = parts[1]
                        mysend(self.s, json.dumps({"action":"poem", "target":poem_idx_str}))
                        poem = json.loads(myrecv(self.s))["results"]
                        if (len(poem) > 0):
                            self.out_msg += f"Sonnet {poem_idx_str}:\n{poem}\n"
                        else:
                            self.out_msg += f"Sonnet {poem_idx_str} not found\n\n"
                    else:
                         self.out_msg += "Invalid poem command. Use 'p <number>'.\n"
                    processed_my_msg_as_command = True
                # The 'c' (connect) command is handled in the S_LOGGEDIN state block below.

        # State-specific handling for messages and commands.
        if self.state == S_LOGGEDIN:
            # Handle commands specific to the S_LOGGEDIN state (e.g., 'connect').
            if len(my_msg) > 0 and not processed_my_msg_as_command:
                if my_msg[0] == 'c': # Connect to another user.
                    peer = my_msg[1:].strip()
                    if self.connect_to(peer):
                        self.state = S_CHATTING # Transition to chatting state.
                        self.out_msg += 'Connect to ' + peer + '. Chat away!\n\n'
                        self.out_msg += '-----------------------------------\n'
                    else:
                        self.out_msg += 'Connection unsuccessful\n'
                    processed_my_msg_as_command = True
                # Original commented-out 'else' block for unknown S_LOGGEDIN commands removed.

            # Handle incoming server messages when in S_LOGGEDIN state.
            if len(peer_msg) > 0: # This assumes peer_msg was already parsed if it existed.
                # peer_msg = json.loads(myrecv(self.s)) # This line is problematic, peer_msg is already parsed or empty.
                                                        # If peer_msg was empty, this would block.
                                                        # If peer_msg was not empty, it's already a dict.
                                                        # This logic needs to rely on the peer_msg dict from the top of proc.
                if peer_msg["action"] == "connect": # Server confirms a connection initiated by another user.
                    self.peer = peer_msg["from"]
                    self.out_msg += 'Request from ' + self.peer + '\n'
                    self.out_msg += 'You are connected with ' + self.peer
                    self.out_msg += '. Chat away!\n\n'
                    self.out_msg += '------------------------------------\n'
                    self.state = S_CHATTING
                elif peer_msg["action"] == "exchange":
                    self.out_msg += peer_msg["from"] + peer_msg["message"]
                    
    
                    
                    

        elif self.state == S_CHATTING:
            if len(my_msg) > 0 and not processed_my_msg_as_command: # If not a universal command
                if my_msg.startswith('@'): # PM
                    try:
                        parts = my_msg[1:].split(" ", 1)
                        if len(parts) == 2:
                            target_user, pm_text = parts[0], parts[1]
                            mysend(self.s, json.dumps({"action": "private_message", "to": target_user, "message": pm_text}))
                            response_json = myrecv(self.s)
                            if response_json:
                                response = json.loads(response_json)
                                if response.get("action") == "private_message_status":
                                    self.out_msg += f"[PM to {response.get('to', target_user)}: {response.get('detail', response.get('status', 'Unknown'))}]\n"
                                else:
                                    self.out_msg += "[PM Status: Unexpected server response]\n"
                            else:
                                self.out_msg += "[PM Status: No response from server]\n"
                        else:
                            self.out_msg += "[Error: Invalid PM format. Use @user message]\n"
                    except Exception as e:
                        self.out_msg += f"[Error processing PM: {str(e)}]\n"
                elif my_msg == 'bye':
                    self.disconnect()
                    self.state = S_LOGGEDIN # Go back to S_LOGGEDIN after 'bye'
                    self.peer = '' # Clear peer
                else: # Regular broadcast message
                    mysend(self.s, json.dumps({"action":"exchange", "from":"[" + self.me + "]", "message":my_msg}))
                    self.out_msg += f"[{self.me}] {my_msg}\n" # Local echo

            if len(peer_msg) > 0:
                if peer_msg["action"] == "connect":
                    self.out_msg += "(" + peer_msg["from"] + " reconnected/joined?)\n"
                elif peer_msg["action"] == "disconnect":
                    self.out_msg += "(" + peer_msg.get("from", self.peer) + " left the chat)\n"
                    self.state = S_LOGGEDIN
                    self.peer = ''
                elif peer_msg["action"] == "incoming_private_message":
                    self.out_msg += peer_msg["from"] + " " + peer_msg["message"]
                elif peer_msg["action"] == "exchange": # Make sure S_CHATTING handles incoming exchanges
                    self.out_msg += peer_msg["from"] + peer_msg["message"]
                    print("regular message sent to gui")


        elif self.state == S_OFFLINE:
             if len(my_msg) > 0 :
                self.out_msg += "You are not connected. Please 'connect' first.\n"
        # S_CONNECTED state might need handling if my_msg can occur there
        # else: # Catchall for unhandled states or my_msg in unexpected states
        #    if len(my_msg) > 0:
        #        self.out_msg += "Cannot process message in current state.\n"


        # Fallback for invalid state that wasn't S_OFFLINE, S_LOGGEDIN, or S_CHATTING
        if not (self.state == S_LOGGEDIN or self.state == S_CHATTING or self.state == S_OFFLINE or self.state == S_CONNECTED):
            self.out_msg += 'How did you wind up here??\n'
            print_state(self.state)

        return self.out_msg
