#!/usr/bin/env python3
# -*- coding: utf-8 -*-


# import all the required  modules
import threading
import select
from tkinter import *
from tkinter import font
from tkinter import ttk
from chat_utils import *
import json
from tkinter import messagebox
import tkinter as tk
from tkinter import colorchooser
# import emoji # Emoji functionality removed
import random
try:
    import requests
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("Pillow (PIL) and/or requests library not found. Profile pictures will not be loaded.")

# --- AOL Themed Button ---
class AOLButton(Button):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.config(
            relief=RAISED,
            borderwidth=2,
            bg="#C0C0C0",  # Classic grey button
            fg="#000000",  # Black text
            activebackground="#A0A0A0", # Darker grey when pressed
            activeforeground="#000000",
            font=("Arial", 10, "bold"), # Common AOL-era font
            padx=8,
            pady=4
        )
        # AOL buttons didn't typically have hover, but we can add subtle ones if you like later

class AOLSmallButton(Button): # For smaller action buttons like emoji picker
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.config(
            relief=RAISED,
            borderwidth=1,
            bg="#C0C0C0",
            fg="#000000",
            activebackground="#A0A0A0",
            font=("Arial", 9),
            padx=5,
            pady=2
        )

# GUI class for the chat
class GUI:
    # constructor method
    def __init__(self, send, recv, sm, s):
        # chat window which is currently hidden
        self.Window = Tk()
        self.Window.withdraw()
        self.send = send
        self.recv = recv
        self.sm = sm
        self.socket = s
        self.my_msg = ""
        self.system_msg = ""
        # PM and User List Popup variables removed
        
        # --- AOL Theme Colors ---
        self.aol_main_blue = "#003399"    # Primary AOL blue
        self.aol_panel_bg = "#D1D1D1"     # Light grey for panels/frames
        self.aol_widget_bg = "#C0C0C0"    # Standard grey for widgets like buttons
        self.aol_chat_bg = "#FFFFFF"      # White for chat display area
        self.aol_text_on_blue = "#FFFFFF" # White text for dark blue backgrounds
        self.aol_text_on_grey = "#000000" # Black text for grey backgrounds
        self.aol_text_on_white = "#000000" # Black text for white backgrounds
        self.aol_accent_yellow = "#FFCC00" # AOL's signature yellow (sparingly)

        # Assigning to generic names for easier application
        self.bg_color = self.aol_main_blue       # Overall window background
        self.panel_color = self.aol_panel_bg     # Background for major content frames
        self.chat_area_bg_color = self.aol_chat_bg
        self.text_color = self.aol_text_on_blue # Default text color (e.g., for labels on main_blue)
        self.widget_text_color = self.aol_text_on_grey # For text on buttons, entries
        self.chat_text_color = self.aol_text_on_white

        # Configure styles
        self.style = ttk.Style()
        self.style.configure("TFrame", background=self.panel_color) # Default for ttk.Frames

    def login(self):
        # login window
        self.login = Toplevel()
        # set the title
        self.login.title("AOL Chat - Sign On")
        self.login.resizable(width = False, 
                             height = False)
        self.login.configure(width = 350,
                             height = 250,
                             bg = self.bg_color)
        
        # Center the window
        screen_width = self.login.winfo_screenwidth()
        screen_height = self.login.winfo_screenheight()
        x = (screen_width - 350) // 2
        y = (screen_height - 250) // 2
        self.login.geometry(f"350x250+{x}+{y}")

        # Central frame for login elements (mimics an inset panel)
        login_panel = Frame(self.login, bg=self.panel_color, relief=RAISED, borderwidth=2, padx=20, pady=20)
        login_panel.pack(expand=True, padx=15, pady=15)

        welcome_label = Label(login_panel,
                              text="Welcome!",
                              font=("Arial", 16, "bold"),
                              bg=self.panel_color,
                              fg=self.aol_text_on_grey)
        welcome_label.pack(pady=(0, 10))

        name_label = Label(login_panel,
                              text="Screen Name:",
                              font=("Arial", 10),
                              bg=self.panel_color,
                              fg=self.aol_text_on_grey)
        name_label.pack(pady=(5,0))

        self.entryName = Entry(login_panel,
                               font=("Arial", 12),
                               width=20,
                               relief=SUNKEN,
                               borderwidth=2)
        self.entryName.pack(pady=(0,10))
        self.entryName.focus()

        self.go_button = AOLButton(login_panel,
                                   text="Sign On",
                                   command=lambda: self.goAhead(self.entryName.get()))
        self.go_button.pack(pady=10)
        
        # Add a small AOL-like logo spot
        logo_spot_frame = Frame(self.login, bg=self.aol_accent_yellow, width=30, height=30, relief=SUNKEN, borderwidth=1)
        logo_spot_frame.place(x=10, y=10) # Top-left corner for a tiny "logo"
        logo_spot_frame.pack_propagate(False) # Prevent frame from resizing to image

        if PIL_AVAILABLE:
            try:
                img = Image.open("aol_logo.png")
                img = img.resize((28, 28), Image.Resampling.LANCZOS) # Resize to fit, leave 1px border
                self.aol_logo_photo = ImageTk.PhotoImage(img) # Keep a reference
                
                logo_label = Label(logo_spot_frame, image=self.aol_logo_photo, bg=self.aol_accent_yellow)
                logo_label.pack(expand=True, fill=BOTH)
            except FileNotFoundError:
                print("aol_logo.png not found. Displaying yellow box.")
                # Fallback to just the yellow box if image not found
            except Exception as e:
                print(f"Error loading AOL logo: {e}")
                # Fallback
        else:
            # If PIL is not available, Tkinter's PhotoImage might still work for PNGs
            # but resizing is harder. For simplicity, just show yellow box or simple text.
            # Or, you could try PhotoImage directly if you know it's a compatible PNG.
            # For now, just the yellow box if PIL is not there.
            print("PIL not available, AOL logo will not be displayed, showing yellow box.")


        self.Window.mainloop()
  
    def goAhead(self, name):
        if len(name) > 0:
            msg = json.dumps({"action":"login", "name": name})
            self.send(msg)
            response_json = self.recv()
            if response_json:
                response = json.loads(response_json)
                if response["status"] == 'ok':
                    self.login.destroy()
                    self.sm.set_state(S_CHATTING) # Change to S_CHATTING for immediate broadcast capability
                    self.sm.set_myname(name)
                    self.layout(name)
                    self.textCons.config(state=NORMAL)
                    initial_chat_text = menu.replace("===", "--").replace("•", "-") # AOL-ify menu
                    self.textCons.insert(END, initial_chat_text + "\n\n")      
                    self.textCons.config(state=DISABLED)
                    self.textCons.see(END)
                    # Start the proc thread AFTER layout is done
                    process = threading.Thread(target=self.proc)
                    process.daemon = True
                    process.start()
                else:
                    messagebox.showerror("Sign On Failed", f"Could not sign on: {response.get('status', 'Unknown error')}", parent=self.login)
            else:
                messagebox.showerror("Connection Error", "No response from server.", parent=self.login)
        else:
            messagebox.showwarning("Input Needed", "Please enter a Screen Name.", parent=self.login)
  
    # The main layout of the chat
    def layout(self,name):
        
        self.name = name
        # to show chat window
        self.Window.deiconify()
        self.Window.title(f"AOL Chat - ({self.name})")
        self.Window.resizable(width = True,
                              height = True)
        self.Window.configure(width = 1200,
                              height = 800,
                              bg = self.bg_color)
        
        # Center the window
        screen_width = self.Window.winfo_screenwidth()
        screen_height = self.Window.winfo_screenheight()
        x = (screen_width - 1200) // 2
        y = (screen_height - 800) // 2
        self.Window.geometry(f"1200x800+{x}+{y}")

        # Main content frame (panel-like)
        main_panel = Frame(self.Window, bg=self.panel_color, relief=RAISED, borderwidth=2)
        main_panel.pack(fill=BOTH, expand=True, padx=5, pady=5)
        
        # Top bar (could hold status or simple title)
        top_bar_frame = Frame(main_panel, bg=self.aol_widget_bg, relief=SUNKEN, borderwidth=1, height=30)
        top_bar_frame.pack(fill=X, padx=2, pady=2)
        Label(top_bar_frame, text=f"You are signed on as: {self.name}", font=("Arial", 9), bg=self.aol_widget_bg, fg=self.aol_text_on_grey).pack(side=LEFT, padx=5)

        # --- Left Panel for Commands ---
        command_panel = Frame(main_panel, bg=self.panel_color, relief=RIDGE, borderwidth=2, width=150)
        command_panel.pack(side=LEFT, fill=Y, padx=(2,1), pady=2)
        command_panel.pack_propagate(False) # Prevent shrinking

        Label(command_panel, text="Channels", font=("Arial", 10, "bold"), bg=self.panel_color, fg=self.aol_text_on_grey).pack(pady=5)
        
        # Reverted "People Here" button command
        AOLButton(command_panel, text="People Here", command=lambda: self.handle_command("who")).pack(fill=X, padx=5, pady=3)
        AOLButton(command_panel, text="Daily Sonnet", command=lambda: self.handle_command("poem")).pack(fill=X, padx=5, pady=3)
        AOLButton(command_panel, text="Get Specific Sonnet", command=self.show_poem_dialog).pack(fill=X, padx=5, pady=3)
        AOLButton(command_panel, text="Get Time", command=lambda: self.handle_command("time")).pack(fill=X, padx=5, pady=3)
        
        # Special button for search, needs a dialog
        search_btn = AOLButton(command_panel, text="Find...", command=self.show_search_dialog)
        search_btn.pack(fill=X, padx=5, pady=3)

        AOLButton(command_panel, text="Set PFP", command=self.show_set_pfp_dialog).pack(fill=X, padx=5, pady=3) # New Set PFP button
        
        AOLButton(command_panel, text="Leave Chat", command=lambda: self.handle_command("disconnect")).pack(fill=X, padx=5, pady=3)

        #Special button for tic tac toe
        tic_tac_toe_btn = AOLButton(command_panel, text="Tic Tac Toe", command=lambda: self.choose_player_dialog())
        tic_tac_toe_btn.pack(fill=X, padx=5, pady=3)
        
        # --- Right Panel for Chat ---
        chat_panel = Frame(main_panel, bg=self.panel_color, relief=RIDGE, borderwidth=2)
        chat_panel.pack(side=RIGHT, fill=BOTH, expand=True, padx=(1,2), pady=2)

        # Chat display area
        self.textCons = Text(chat_panel,
                             wrap=WORD,
                             bg=self.chat_area_bg_color, # White chat background
                             fg=self.chat_text_color,    # Black chat text
                             font=("Arial", 11),
                             relief=SUNKEN,
                             borderwidth=2,
                             padx=5,
                             pady=5)
        self.textCons.pack(fill=BOTH, expand=True, padx=5, pady=(5,0))

        # Scrollbar
        scrollbar = Scrollbar(self.textCons, relief=FLAT, troughcolor=self.aol_widget_bg) # Style scrollbar trough
        scrollbar.pack(side=RIGHT, fill=Y)
        self.textCons.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.textCons.yview)

        # Input area
        input_area_frame = Frame(chat_panel, bg=self.panel_color, relief=FLAT) # Flat, part of chat_panel
        input_area_frame.pack(fill=X, padx=5, pady=(1,5)) # Small padding

        # Emoji button removed
        # self.emoji_button = AOLSmallButton(input_area_frame, # Smaller button
        #                                 text=":-)", # Classic emoticon for emoji
        #                                 command=self.show_emoji_picker)
        # self.emoji_button.pack(side=LEFT, padx=(0,5))

        # Message entry
        self.entryMsg = Entry(input_area_frame,
                            font=("Arial", 11),
                            relief=SUNKEN,
                            borderwidth=2)
        self.entryMsg.pack(side=LEFT, fill=X, expand=True)
        self.entryMsg.bind("<Return>", lambda event: self.sendButton(self.entryMsg.get()))
          
        # Send button
        self.buttonMsg = AOLButton(input_area_frame,
                                    text="Send", # Was "Send Message"
                                    command=lambda: self.sendButton(self.entryMsg.get()))
        self.buttonMsg.pack(side=RIGHT, padx=(5,0))
          
        self.textCons.config(cursor = "arrow")
        self.textCons.config(state = DISABLED)
        self.entryMsg.focus()
  
    def handle_command(self, command):
        if command == "who":
            self.my_msg = "who"
        elif command == "time":
            self.my_msg = "time"
        elif command == "search":
            self.show_search_dialog() # This sets self.my_msg internally via dialog
        elif command == "poem":
            # When clicking "Daily Sonnet", get a random one between 1-154
            random_sonnet = random.randint(1, 154)
            self.my_msg = f"p {random_sonnet}"
        elif command == "disconnect":
            self.my_msg = "disconnect"
        elif command == "OPEN_TTT":
            self.my_msg = "OPEN_TTT"
        

    def show_search_dialog(self):
        # Style this like a small AOL dialog
        search_dialog = Toplevel(self.Window)
        search_dialog.title("Keyword Search")
        search_dialog.configure(bg=self.panel_color)
        search_dialog.geometry("300x150")
        search_dialog.resizable(False, False)
        search_dialog.transient(self.Window) # Keep on top of main window

        Label(search_dialog, text="Find text in chat:", font=("Arial", 10), bg=self.panel_color, fg=self.aol_text_on_grey).pack(pady=10)
        
        search_entry = Entry(search_dialog, font=("Arial", 10), width=30, relief=SUNKEN, borderwidth=1)
        search_entry.pack(pady=5)
        search_entry.focus()
        
        def perform_search():
            term = search_entry.get()
            if term:
                self.my_msg = f"? {term}" # State machine uses ? for search
                search_dialog.destroy()
            else:
                messagebox.showwarning("Input Needed", "Please enter a search term.", parent=search_dialog)
        
        AOLButton(search_dialog, text="Find", command=perform_search).pack(pady=10)

    def show_poem_dialog(self):
        poem_dialog = Toplevel(self.Window)
        poem_dialog.title("Get Specific Sonnet")
        poem_dialog.configure(bg=self.panel_color)
        poem_dialog.geometry("300x180") # Slightly taller for two buttons
        poem_dialog.resizable(False, False)
        poem_dialog.transient(self.Window)

        Label(poem_dialog, text="Enter Sonnet Number (1-154):", font=("Arial", 10), bg=self.panel_color, fg=self.aol_text_on_grey).pack(pady=10)
        
        poem_entry = Entry(poem_dialog, font=("Arial", 10), width=5, relief=SUNKEN, borderwidth=1)
        poem_entry.pack(pady=5)
        poem_entry.focus()
        
        def submit_specific_sonnet():
            num_str = poem_entry.get()
            if num_str.isdigit() and 1 <= int(num_str) <= 154:
                self.my_msg = f"p {num_str}"
                poem_dialog.destroy()
            else:
                messagebox.showerror("Invalid Number", "Please enter a number between 1 and 154.", parent=poem_dialog)
        
        AOLButton(poem_dialog, text="Get Sonnet", command=submit_specific_sonnet).pack(pady=10)

    def show_set_pfp_dialog(self):
        pfp_dialog = Toplevel(self.Window)
        pfp_dialog.title("Set Profile Picture")
        pfp_dialog.configure(bg=self.panel_color)
        pfp_dialog.geometry("350x180")
        pfp_dialog.resizable(False, False)
        pfp_dialog.transient(self.Window)

        Label(pfp_dialog, text="Enter Profile Picture URL:", font=("Arial", 10), bg=self.panel_color, fg=self.aol_text_on_grey).pack(pady=10)
        
        pfp_url_entry = Entry(pfp_dialog, font=("Arial", 10), width=40, relief=SUNKEN, borderwidth=1)
        pfp_url_entry.pack(pady=5)
        pfp_url_entry.focus()
        
        def submit_pfp_url():
            url = pfp_url_entry.get().strip()
            if url:
                self.my_msg = f"/setpfp {url}" # Command for ClientSM
                pfp_dialog.destroy()
            else:
                messagebox.showwarning("Input Needed", "Please enter a URL.", parent=pfp_dialog)
        
        AOLButton(pfp_dialog, text="Set Picture", command=submit_pfp_url).pack(pady=10)

    # Emoji methods removed
    # def show_emoji_picker(self): ...
    # def insert_emoji(self, emoji_char, window): ...
  
    # function to basically start the thread for sending messages
    
    def choose_player_dialog(self):
        choose_dialog = Toplevel(self.Window)
        choose_dialog.title("Choose your opponent")
        choose_dialog.configure(bg=self.panel_color)
        choose_dialog.geometry("400x250")
        choose_dialog.resizable(False, False)
        choose_dialog.transient(self.Window)
        Label(choose_dialog, text="Enter player name:", font=("Arial", 10), bg=self.panel_color, fg=self.aol_text_on_grey).pack(pady=10)
        player_entry = Entry(choose_dialog, font=("Arial", 10), width=10, relief=SUNKEN, borderwidth=1)
        player_entry.pack(pady=5)
        player_entry.focus()
        
        def submit_player_name():
            name = player_entry.get().strip()
            if name and name != self.name:
                self.my_msg = f"ttt{name}"
                choose_dialog.destroy()
        
        AOLButton(choose_dialog, text="Play", command=submit_player_name).pack(pady=10)
        
    #set up ttt window
    def open_ttt_window(self,symbol):
        self.symbol = symbol
        if self.symbol == "X":
            peer_symbol = "O"
        else:
            peer_symbol = "X"
        color_blue = "#4584b6"
        color_yellow = "#ffde57"
        color_gray = "#343434"
        color_light_gray = "#646464"
        self.board = [[None for _ in range(3)] for _ in range(3)]
        self.ttt_window = Toplevel(self.Window)
        self.ttt_window.title(f"Tic Tac Toe with {peer_symbol}")
        self.ttt_window.configure(bg=self.panel_color)
        
        # Set a decent size and center it
        default_width = 450
        default_height = 555
        screen_width = self.ttt_window.winfo_screenwidth()
        screen_height = self.ttt_window.winfo_screenheight()
        window_x = int((screen_width / 2) - (default_width / 2))
        window_y = int((screen_height / 2) - (default_height / 2))
        
        self.ttt_window.resizable(False, False)
        self.ttt_window.transient(self.Window)

        # Create frame for layout
        self.frame = Frame(self.ttt_window, bg=color_gray)
        self.frame.pack(padx=10, pady=10)
    
        # Status label
        curr_player="X"
        self.label = Label(self.frame, text=curr_player +"'s turn", font=("Consolas", 16), bg=color_gray, fg="white")
        self.label.grid(row=0, column=0, columnspan=3, sticky="we")

        
        for row in range(3):
            for column in range(3):
                
                self.board[row][column] = Button(self.frame, text="", font=("Consolas", 50, "bold"), background=color_gray, foreground=color_yellow, width=4, height=1,
                                command=lambda r=row, c=column: self.make_move(r, c))
                self.board[row][column].grid(row=row+1, column=column)
                
        #restart button for new game
        self.restart_button = Button(self.frame, text="restart", font=("Consolas", 20), background=color_gray,
                        foreground="white")
        self.restart_button.grid(row=4, column=0, columnspan=3, sticky="we")
        
    
    def make_move(self, row, column):
        if self.board[row][column]["text"] != "":
            return
        
        
        self.board[row][column]["text"] = self.symbol  # Game logic
        print(f"i marked this place {row}, {column}")
        self.my_msg="move "+ str(row)+" "+ str(column)+ " from "+self.symbol
        print(f"send {row} {column} to state machine")
        for row in range(3):
            for column in range(3):
                self.board[row][column].config(state=DISABLED)
        
        
        
        
    def sendButton(self, msg):
        # Always process the message regardless of content
        msg = msg.strip()
        if msg:
            # Check for /pm command before sending as broadcast
            if msg.startswith("/pm "):
                parts = msg.split(" ", 2)
                if len(parts) == 3:
                    target_user = parts[1]
                    pm_message = parts[2]
                    self.my_msg = f"@{target_user} {pm_message}" # Use internal format for ClientSM
                    # Local echo for PMs (optional, can be added later if needed)
                    # self.textCons.config(state=NORMAL)
                    # self.textCons.insert(END, f"PM to {target_user}: {pm_message}\n")
                    # self.textCons.config(state=DISABLED)
                    # self.textCons.see(END)
                else:
                    # Invalid /pm format, treat as regular message or show error?
                    # For now, treat as regular message
                    self.my_msg = msg 
            else:
                 # Regular broadcast message
                 self.my_msg = msg
                 
            self.entryMsg.delete(0, END)
            # No need to disable textCons here, proc loop handles it
            
            

    def proc(self):
        while True:
            read, write, error = select.select([self.socket], [], [], 0)
            peer_msg_json = "" # Incoming JSON message from network as a string
            
            # Capture the command this client is about to process via the state machine.
            command_this_client_sent = self.my_msg 

            if self.socket in read:
                peer_msg_json = self.recv() # Potentially a message from another user or server notification

            # Process either a command from this client (self.my_msg) or an incoming network message (peer_msg_json)
            if len(self.my_msg) > 0 or len(peer_msg_json) > 0:
                # self.sm.proc will handle the logic and return a string for display
                sm_output_string = self.sm.proc(self.my_msg, peer_msg_json)
                print(f"gui's output_string: {sm_output_string}")
                self.my_msg = "" # Clear the command/message from this client, as it's now processed

                if sm_output_string: # If the state machine generated something to display
                    self.textCons.config(state=NORMAL)
                    display_text_for_gui = ""

                    # Determine how to format the output based on the original command or message type
                    if sm_output_string.strip().startswith("GAME_OVER_UPDATE:"):
                        try:
                            data_json_str = sm_output_string.strip().replace("GAME_OVER_UPDATE:", "", 1)
                            data = json.loads(data_json_str)
                            winner = data.get("winner")
                            status = data.get("status")
                            final_board_state = data.get("board")

                            if hasattr(self, 'ttt_window') and self.ttt_window.winfo_exists():
                                if status == "win" and winner:
                                    self.label.config(text=f"{winner} wins!")
                                elif status == "tie":
                                    self.label.config(text="It's a Tie!")
                                else:
                                    self.label.config(text="Game Over!")

                                if final_board_state and hasattr(self, 'board'):
                                    for r_idx in range(3):
                                        for c_idx in range(3):
                                            if self.board[r_idx][c_idx]: # Check if button exists
                                                self.board[r_idx][c_idx].config(text=final_board_state[r_idx][c_idx], state=DISABLED)
                                # Disable all buttons just in case
                                for r_idx in range(3):
                                    for c_idx in range(3):
                                        if hasattr(self, 'board') and self.board[r_idx][c_idx]:
                                             self.board[r_idx][c_idx].config(state=DISABLED)
                            else:
                                # If ttt_window doesn't exist, maybe show in main chat
                                display_text_for_gui = f"\nSYSTEM: Game Over! Winner: {winner if winner else 'Tie'}\n\n"
                            
                            # No text to main chat if game window handled it
                            # display_text_for_gui = ""

                        except (json.JSONDecodeError, Exception) as e:
                            print(f"Error parsing GAME_OVER_UPDATE: {e}")
                            display_text_for_gui = "\nSYSTEM: Error processing game over message.\n\n"

                    elif "OPEN_TTT" in sm_output_string:
                        print(f"DEBUG GUI: OPEN_TTT received: {sm_output_string}")
                        try:
                            # The symbol ("X" or "O") should be the last part of the string sent by CSM
                            # CSM for initiator sends: "...OPEN_TTT: <opponent_name> <MY_SYMBOL>"
                            # CSM for invitee sends: "...OPEN_TTT: <challenger_name>\n opponent turn <MY_SYMBOL>"
                            
                            stripped_sm_output = sm_output_string.strip()
                            parts = stripped_sm_output.split() # Split by any whitespace
                            parsed_symbol = parts[-1] # Assume last word is the symbol

                            if parsed_symbol not in ["X", "O"]:
                                # If last word isn't X/O, check if it's like "... opponent turn X"
                                if len(parts) >= 3 and parts[-3].lower() == "opponent" and parts[-2].lower() == "turn" and parts[-1] in ["X", "O"]:
                                    parsed_symbol = parts[-1]
                                else:
                                    # Fallback if parsing is still tricky
                                    print(f"[GUI WARNING] Could not reliably parse symbol from OPEN_TTT: '{stripped_sm_output}'. Defaulting symbol.")
                                    # Try to get it from self.sm if it's set there (CSM sets its self.symbol)
                                    if hasattr(self.sm, 'symbol') and self.sm.symbol in ["X", "O"]:
                                        parsed_symbol = self.sm.symbol
                                        print(f"[GUI DEBUG] Using symbol '{parsed_symbol}' from ClientSM instance.")
                                    else:
                                        parsed_symbol = "X" # Absolute fallback
                                        print(f"[GUI DEBUG] Absolute fallback to symbol '{parsed_symbol}'.")

                            self.symbol = parsed_symbol
                            print(f"[GUI DEBUG] My assigned TTT symbol is: {self.symbol}")

                            if not hasattr(self, "ttt_window") or not self.ttt_window.winfo_exists():
                                self.open_ttt_window(self.symbol) # Pass the correctly parsed symbol
                            
                            # Set initial turn label - server will send first "update" to clarify actual first turn
                            if hasattr(self, 'label') and self.label.winfo_exists():
                                self.label.config(text="X's Turn (pending server)")

                            display_text_for_gui = "" # Clear this, as game window is opened
                            
                        except Exception as e:
                            print(f"Error parsing OPEN_TTT message: {e}. String was: '{sm_output_string}'")
                            display_text_for_gui = "\nSYSTEM: Error opening TTT window.\n\n"
                        
                    
                    elif "myturn" in sm_output_string and len(sm_output_string.split()) >= 4 : # Check length
                        print("gui know its my turn")
                        parts = sm_output_string.split() # e.g. "myturn opponent_name row col"
                        # Expected: parts[-4] could be "myturn", parts[-2] is row, parts[-1] is col
                        # parts[-3] is opponent_name who made the last move
                        row=int(parts[-2])
                        column=int(parts[-1])
                        opponent_symbol_played = "X" if self.symbol=="O" else "O" # Symbol of the opponent

                        if hasattr(self, 'board') and self.board[row][column]:
                            self.board[row][column]["text"]=opponent_symbol_played
                            print(f"mark opponent {opponent_symbol_played} move at {row},{column}")
                        
                        if hasattr(self, 'label'):
                            self.label["text"]=self.name+"'s turn (" + self.symbol + ")"
                        
                        # Enable only empty buttons
                        if hasattr(self, 'board'):
                            for r_idx in range(3):
                                for c_idx in range(3):
                                    if self.board[r_idx][c_idx]: # Check if button exists
                                        if self.board[r_idx][c_idx]["text"] == "":
                                            self.board[r_idx][c_idx].config(state=NORMAL)
                                        else:
                                            self.board[r_idx][c_idx].config(state=DISABLED)
                        
                        display_text_for_gui = "" # No need to echo this to main chat
                        print("my turn, now click")
                        
                                
                    elif "oppo nent turn" in sm_output_string and len(sm_output_string.split()) >= 3: # Check length
                        print("gui know its opponent turn")
                        if hasattr(self, 'board'):
                            for r_idx in range(3):
                                for c_idx in range(3):
                                    if self.board[r_idx][c_idx]: # Check if button exists
                                        self.board[r_idx][c_idx].config(state=DISABLED)
                        
                        turn_player_name = sm_output_string.split()[-1] # Name of player whose turn it is
                        opponent_symbol_for_display = "X" if self.symbol == "O" else "O"

                        if hasattr(self, 'label'):
                            self.label["text"]=turn_player_name+"'s turn ("+ opponent_symbol_for_display +")"
                        display_text_for_gui = "" # No need to echo this to main chat
                        print("you have clicked. Dont click, not my turn")
                        
                         
                        
                    elif command_this_client_sent == "who" and sm_output_string.startswith("USER_LIST_STRUCT:"):
                        try:
                            user_list_json_str = sm_output_string.replace("USER_LIST_STRUCT:", "", 1)
                            user_list_data = json.loads(user_list_json_str)
                            self.show_user_list_popup(user_list_data)
                            display_text_for_gui = "" # Popup handles display, no text for main chat window
                        except (json.JSONDecodeError, Exception) as e:
                            print(f"Error parsing or displaying structured user list: {e}")
                            # Display error in chat window if popup fails
                            display_text_for_gui = "\nSYSTEM: Error displaying user list.\n\n"
                    # All other messages (time, poem, search, PMs, broadcasts, status)
                    # are now expected to be pre-formatted by ClientSM.
                    else:
                        # Ensure sm_output_string is stripped and has a newline if it's not empty
                        stripped_output = sm_output_string.strip()
                        if stripped_output: # Only add newlines if there's content
                            display_text_for_gui = stripped_output + "\n\n"
                        else:
                            display_text_for_gui = "" # Avoid inserting just newlines for empty sm_output
                        print("mistake in gui handling moves")
                    # --- Insert the processed text into the main chat window ---
                    if display_text_for_gui:
                        self.textCons.insert(END, display_text_for_gui)
                        self.textCons.see(END)
                        print(f"gui display into chat window {display_text_for_gui}")
                    # Re-disable textCons after potential insertion
                    self.textCons.config(state=DISABLED)
    
    
    
    def show_user_list_popup(self, user_list_data):
        if hasattr(self, 'user_list_window') and self.user_list_window.winfo_exists():
            self.user_list_window.destroy() # Close existing window first

        self.user_list_window = Toplevel(self.Window)
        self.user_list_window.title("People Here")
        self.user_list_window.configure(bg=self.panel_color)
        self.user_list_window.geometry("400x500") # Adjust as needed
        self.user_list_window.transient(self.Window)

        canvas = Canvas(self.user_list_window, bg=self.panel_color)
        scrollbar = Scrollbar(self.user_list_window, orient="vertical", command=canvas.yview)
        scrollable_frame = Frame(canvas, bg=self.panel_color)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.pack(side="right", fill="y")

        if not user_list_data:
            Label(scrollable_frame, text="No users online.", font=("Arial", 10), bg=self.panel_color, fg=self.aol_text_on_grey).pack(pady=10)
            return

        for user_info in user_list_data:
            user_frame = Frame(scrollable_frame, bg=self.aol_widget_bg, relief=RAISED, borderwidth=1, padx=5, pady=5)
            user_frame.pack(fill=X, pady=3, padx=3)

            pfp_label = Label(user_frame, bg=self.aol_widget_bg) # Placeholder for PFP
            pfp_label.pack(side=LEFT, padx=(0, 10))

            name_label = Label(user_frame, text=user_info.get("name", "N/A"), font=("Arial", 11, "bold"), bg=self.aol_widget_bg, fg=self.aol_text_on_grey)
            name_label.pack(side=LEFT, anchor="w")
            
            if PIL_AVAILABLE and user_info.get("pfp_url"):
                # Load PFP in a separate thread to avoid freezing GUI
                threading.Thread(target=self.load_pfp_image, args=(user_info["pfp_url"], pfp_label), daemon=True).start()
            else:
                # Default placeholder if PIL not available or no PFP URL
                try:
                    # Create a small grey square as a placeholder
                    placeholder_img = Image.new('RGB', (50, 50), color = 'grey')
                    placeholder_photo = ImageTk.PhotoImage(placeholder_img)
                    pfp_label.config(image=placeholder_photo)
                    pfp_label.image = placeholder_photo # Keep a reference
                except Exception as e:
                    # This might happen if even Pillow for placeholder fails (e.g. Tkinter issue)
                    print(f"Error creating placeholder image: {e}")
                    pfp_label.config(text="[PFP]")


    def load_pfp_image(self, url, pfp_label_widget):
        try:
            response = requests.get(url, stream=True, timeout=5)
            response.raise_for_status() # Raise an exception for HTTP errors
            img = Image.open(response.raw)
            img.thumbnail((50, 50)) # Resize to a thumbnail
            photo = ImageTk.PhotoImage(img)
            
            # Schedule the update on the main Tkinter thread
            self.Window.after(0, lambda: self.update_pfp_label(pfp_label_widget, photo))

        except requests.exceptions.RequestException as e:
            print(f"Error fetching PFP from {url}: {e}")
            self.Window.after(0, lambda: self.set_pfp_placeholder(pfp_label_widget, "[Fetch Err]"))
        except Exception as e:
            print(f"Error processing PFP image from {url}: {e}")
            self.Window.after(0, lambda: self.set_pfp_placeholder(pfp_label_widget, "[Load Err]"))

    def update_pfp_label(self, label_widget, photo_image):
        if label_widget.winfo_exists(): # Check if widget still exists
            label_widget.config(image=photo_image)
            label_widget.image = photo_image # Keep a reference!

    def set_pfp_placeholder(self, label_widget, text="[PFP]"):
        if label_widget.winfo_exists():
            # Attempt to create a small grey square as a placeholder if PIL is available
            if PIL_AVAILABLE:
                try:
                    placeholder_img = Image.new('RGB', (50, 50), color = 'lightgrey')
                    # Optionally, add text to the placeholder
                    # from PIL import ImageDraw
                    # draw = ImageDraw.Draw(placeholder_img)
                    # draw.text((5,20), text, fill="black") # Basic text
                    placeholder_photo = ImageTk.PhotoImage(placeholder_img)
                    label_widget.config(image=placeholder_photo, text="") # Clear any previous text
                    label_widget.image = placeholder_photo
                    return
                except Exception as e:
                    print(f"Error creating placeholder image during set_pfp_placeholder: {e}")
            
            # Fallback if PIL placeholder fails or PIL_AVAILABLE is false
            label_widget.config(image=None, text=text, width=7, height=3) # Approx 50x50 with text


    def run(self):
        self.login()
# create a GUI class object
if __name__ == "__main__": 
    # This part is usually handled by chat_client_class.py
    # If running GUI.py directly, it needs setup.
    # For now, assume it's run via chat_client_class.py
    # g = GUI() # This will fail without args
    pass # Do nothing if run directly
