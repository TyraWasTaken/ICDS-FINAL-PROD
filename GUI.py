#!/usr/bin/env python3
# -*- coding: utf-8 -*-


# Import necessary modules for GUI, threading, and chat functionality.
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

class AOLSmallButton(Button): # For smaller action buttons.
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
    """Main class for the Chat Application's Graphical User Interface."""
    def __init__(self, send, recv, sm, s):
        """
        Initializes the GUI.
        
        Args:
            send: Function to send messages to the server.
            recv: Function to receive messages from the server.
            sm: Client state machine instance.
            s: Client socket instance.
        """
        self.Window = Tk() # Main Tkinter window.
        self.Window.withdraw() # Hide main window initially until login.
        self.send = send
        self.recv = recv
        self.sm = sm
        self.socket = s
        self.my_msg = "" # Stores message typed by the user.
        self.system_msg = "" # Stores system messages for display.
        
        # --- AOL Theme Colors ---
        self.aol_main_blue = "#003399"    # Primary AOL blue for backgrounds.
        self.aol_panel_bg = "#D1D1D1"     # Light grey for UI panels and frames.
        self.aol_widget_bg = "#C0C0C0"    # Standard grey for widgets like buttons.
        self.aol_chat_bg = "#FFFFFF"      # White background for the chat display area.
        self.aol_text_on_blue = "#FFFFFF" # White text on dark blue backgrounds.
        self.aol_text_on_grey = "#000000" # Black text on grey backgrounds.
        self.aol_text_on_white = "#000000" # Black text on white backgrounds.
        self.aol_accent_yellow = "#FFCC00" # AOL's signature yellow, used sparingly for accents.

        # Assigning theme colors to generic variable names for easier application.
        self.bg_color = self.aol_main_blue       # Overall window background color.
        self.panel_color = self.aol_panel_bg     # Background color for major content frames.
        self.chat_area_bg_color = self.aol_chat_bg # Background for the main chat text area.
        self.text_color = self.aol_text_on_blue # Default text color (e.g., for labels on blue backgrounds).
        self.widget_text_color = self.aol_text_on_grey # Text color for widgets like buttons and entries.
        self.chat_text_color = self.aol_text_on_white  # Text color for messages in the chat area.

        # Configure ttk styles for themed widgets if any are used.
        self.style = ttk.Style()
        self.style.configure("TFrame", background=self.panel_color) # Default style for ttk.Frame.

    def login(self):
        """Displays the login window."""
        self.login = Toplevel() # Create a new top-level window for login.
        self.login.title("AOL Chat - Sign On")
        self.login.resizable(width=False, height=False)
        self.login.configure(width=350, height=250, bg=self.bg_color)
        
        # Center the login window on the screen.
        screen_width = self.login.winfo_screenwidth()
        screen_height = self.login.winfo_screenheight()
        x = (screen_width - 350) // 2
        y = (screen_height - 250) // 2
        self.login.geometry(f"350x250+{x}+{y}")

        # Central panel for login elements.
        login_panel = Frame(self.login, bg=self.panel_color, relief=RAISED, borderwidth=2, padx=20, pady=20)
        login_panel.pack(expand=True, padx=15, pady=15)

        welcome_label = Label(login_panel, text="Welcome!", font=("Arial", 16, "bold"), bg=self.panel_color, fg=self.aol_text_on_grey)
        welcome_label.pack(pady=(0, 10))

        name_label = Label(login_panel, text="Screen Name:", font=("Arial", 10), bg=self.panel_color, fg=self.aol_text_on_grey)
        name_label.pack(pady=(5,0))

        self.entryName = Entry(login_panel, font=("Arial", 12), width=20, relief=SUNKEN, borderwidth=2)
        self.entryName.pack(pady=(0,10))
        self.entryName.focus() # Set focus to the name entry field.

        self.go_button = AOLButton(login_panel, text="Sign On", command=lambda: self.goAhead(self.entryName.get()))
        self.go_button.pack(pady=10)
        
        # Placeholder for a small AOL-like logo.
        logo_spot_frame = Frame(self.login, bg=self.aol_accent_yellow, width=30, height=30, relief=SUNKEN, borderwidth=1)
        logo_spot_frame.place(x=10, y=10)
        logo_spot_frame.pack_propagate(False)

        if PIL_AVAILABLE: # Attempt to load and display the logo if Pillow is available.
            try:
                img = Image.open("aol_logo.png")
                img = img.resize((28, 28), Image.Resampling.LANCZOS)
                self.aol_logo_photo = ImageTk.PhotoImage(img) # Keep a reference.
                
                logo_label = Label(logo_spot_frame, image=self.aol_logo_photo, bg=self.aol_accent_yellow)
                logo_label.pack(expand=True, fill=BOTH)
            except FileNotFoundError:
                print("aol_logo.png not found. Displaying yellow box as placeholder.")
            except Exception as e:
                print(f"Error loading AOL logo: {e}")
        else:
            # Fallback if Pillow is not available.
            print("Pillow (PIL) not available, AOL logo will not be displayed.")

        self.Window.mainloop() # Start the Tkinter event loop for the login window.
  
    def goAhead(self, name):
        """Handles the login attempt after the user enters their name."""
        if len(name) > 0:
            msg = json.dumps({"action":"login", "name": name})
            self.send(msg) # Send login request to the server.
            response_json = self.recv() # Receive server's response.
            if response_json:
                response = json.loads(response_json)
                if response["status"] == 'ok': # Login successful.
                    self.login.destroy() # Close the login window.
                    self.sm.set_state(S_CHATTING) # Set client state to chatting.
                    self.sm.set_myname(name)
                    self.layout(name) # Setup the main chat window layout.
                    self.textCons.config(state=NORMAL)
                    # Display initial welcome message in the chat.
                    initial_chat_text = menu.replace("===", "--").replace("•", "-")
                    self.textCons.insert(END, initial_chat_text + "\n\n")
                    self.textCons.config(state=DISABLED)
                    self.textCons.see(END) # Scroll to the end of the chat.
                    # Start a new thread to process incoming messages from the server.
                    process = threading.Thread(target=self.proc)
                    process.daemon = True # Allow main program to exit even if thread is running.
                    process.start()
                else: # Login failed (e.g., duplicate name).
                    messagebox.showerror("Sign On Failed", f"Could not sign on: {response.get('status', 'Unknown error')}", parent=self.login)
            else: # No response from server.
                messagebox.showerror("Connection Error", "No response from server.", parent=self.login)
        else: # User did not enter a name.
            messagebox.showwarning("Input Needed", "Please enter a Screen Name.", parent=self.login)
  
    def layout(self,name):
        """Sets up the main chat window layout after successful login."""
        self.name = name
        self.Window.deiconify() # Show the main chat window.
        self.Window.title(f"AOL Chat - ({self.name})")
        self.Window.resizable(width=True, height=True)
        self.Window.configure(width=1200, height=800, bg=self.bg_color)
        
        # Center the main chat window on the screen.
        screen_width = self.Window.winfo_screenwidth()
        screen_height = self.Window.winfo_screenheight()
        x = (screen_width - 1200) // 2
        y = (screen_height - 800) // 2
        self.Window.geometry(f"1200x800+{x}+{y}")

        # Main content panel.
        main_panel = Frame(self.Window, bg=self.panel_color, relief=RAISED, borderwidth=2)
        main_panel.pack(fill=BOTH, expand=True, padx=5, pady=5)
        
        # Top bar for status information.
        top_bar_frame = Frame(main_panel, bg=self.aol_widget_bg, relief=SUNKEN, borderwidth=1, height=30)
        top_bar_frame.pack(fill=X, padx=2, pady=2)
        Label(top_bar_frame, text=f"You are signed on as: {self.name}", font=("Arial", 9), bg=self.aol_widget_bg, fg=self.aol_text_on_grey).pack(side=LEFT, padx=5)

        # Left panel for command buttons.
        command_panel = Frame(main_panel, bg=self.panel_color, relief=RIDGE, borderwidth=2, width=150)
        command_panel.pack(side=LEFT, fill=Y, padx=(2,1), pady=2)
        command_panel.pack_propagate(False) # Prevent panel from shrinking.

        Label(command_panel, text="Channels", font=("Arial", 10, "bold"), bg=self.panel_color, fg=self.aol_text_on_grey).pack(pady=5)
        
        AOLButton(command_panel, text="People Here", command=lambda: self.handle_command("who")).pack(fill=X, padx=5, pady=3)
        AOLButton(command_panel, text="Daily Sonnet", command=lambda: self.handle_command("poem")).pack(fill=X, padx=5, pady=3)
        AOLButton(command_panel, text="Get Specific Sonnet", command=self.show_poem_dialog).pack(fill=X, padx=5, pady=3)
        AOLButton(command_panel, text="Get Time", command=lambda: self.handle_command("time")).pack(fill=X, padx=5, pady=3)
        
        search_btn = AOLButton(command_panel, text="Find...", command=self.show_search_dialog)
        search_btn.pack(fill=X, padx=5, pady=3)

        AOLButton(command_panel, text="Set PFP", command=self.show_set_pfp_dialog).pack(fill=X, padx=5, pady=3)
        
        AOLButton(command_panel, text="Leave Chat", command=lambda: self.handle_command("disconnect")).pack(fill=X, padx=5, pady=3)

        tic_tac_toe_btn = AOLButton(command_panel, text="Tic Tac Toe", command=lambda: self.choose_player_dialog())
        tic_tac_toe_btn.pack(fill=X, padx=5, pady=3)
        
        # Right panel for chat messages and input.
        chat_panel = Frame(main_panel, bg=self.panel_color, relief=RIDGE, borderwidth=2)
        chat_panel.pack(side=RIGHT, fill=BOTH, expand=True, padx=(1,2), pady=2)

        # Text area for displaying chat messages.
        self.textCons = Text(chat_panel,
                             wrap=WORD,
                             bg=self.chat_area_bg_color,
                             fg=self.chat_text_color,
                             font=("Arial", 11),
                             relief=SUNKEN,
                             borderwidth=2,
                             padx=5,
                             pady=5)
        self.textCons.pack(fill=BOTH, expand=True, padx=5, pady=(5,0))

        # Scrollbar for the chat text area.
        scrollbar = Scrollbar(self.textCons, relief=FLAT, troughcolor=self.aol_widget_bg)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.textCons.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.textCons.yview)

        # Frame for message input field and send button.
        input_area_frame = Frame(chat_panel, bg=self.panel_color, relief=FLAT)
        input_area_frame.pack(fill=X, padx=5, pady=(1,5))

        # Message entry field.
        self.entryMsg = Entry(input_area_frame,
                            font=("Arial", 11),
                            relief=SUNKEN,
                            borderwidth=2)
        self.entryMsg.pack(side=LEFT, fill=X, expand=True)
        self.entryMsg.bind("<Return>", lambda event: self.sendButton(self.entryMsg.get())) # Send on Enter key.
          
        # Send button.
        self.buttonMsg = AOLButton(input_area_frame,
                                    text="Send",
                                    command=lambda: self.sendButton(self.entryMsg.get()))
        self.buttonMsg.pack(side=RIGHT, padx=(5,0))
          
        self.textCons.config(cursor = "arrow") # Set cursor for text area.
        self.textCons.config(state = DISABLED) # Make text area read-only initially.
        self.entryMsg.focus() # Set focus to message entry field.
  
    def handle_command(self, command):
        """Handles commands triggered by buttons in the GUI."""
        if command == "who":
            self.my_msg = "who"
        elif command == "time":
            self.my_msg = "time"
        elif command == "search":
            self.show_search_dialog() # Opens a dialog, which then sets self.my_msg.
        elif command == "poem":
            # Get a random sonnet number for the "Daily Sonnet" feature.
            random_sonnet = random.randint(1, 154)
            self.my_msg = f"p {random_sonnet}"
        elif command == "disconnect":
            self.my_msg = "disconnect"
        elif command == "OPEN_TTT": # Internal command for opening TTT window.
            self.my_msg = "OPEN_TTT"
        

    def show_search_dialog(self):
        """Displays a dialog for entering a chat search term."""
        search_dialog = Toplevel(self.Window)
        search_dialog.title("Keyword Search")
        search_dialog.configure(bg=self.panel_color)
        search_dialog.geometry("300x150")
        search_dialog.resizable(False, False)
        search_dialog.transient(self.Window) # Keep dialog on top of the main window.

        Label(search_dialog, text="Find text in chat:", font=("Arial", 10), bg=self.panel_color, fg=self.aol_text_on_grey).pack(pady=10)
        
        search_entry = Entry(search_dialog, font=("Arial", 10), width=30, relief=SUNKEN, borderwidth=1)
        search_entry.pack(pady=5)
        search_entry.focus()
        
        def perform_search():
            term = search_entry.get()
            if term:
                self.my_msg = f"? {term}" # ClientSM uses '?' prefix for search.
                search_dialog.destroy()
            else:
                messagebox.showwarning("Input Needed", "Please enter a search term.", parent=search_dialog)
        
        AOLButton(search_dialog, text="Find", command=perform_search).pack(pady=10)

    def show_poem_dialog(self):
        """Displays a dialog for entering a specific sonnet number."""
        poem_dialog = Toplevel(self.Window)
        poem_dialog.title("Get Specific Sonnet")
        poem_dialog.configure(bg=self.panel_color)
        poem_dialog.geometry("300x180")
        poem_dialog.resizable(False, False)
        poem_dialog.transient(self.Window)

        Label(poem_dialog, text="Enter Sonnet Number (1-154):", font=("Arial", 10), bg=self.panel_color, fg=self.aol_text_on_grey).pack(pady=10)
        
        poem_entry = Entry(poem_dialog, font=("Arial", 10), width=5, relief=SUNKEN, borderwidth=1)
        poem_entry.pack(pady=5)
        poem_entry.focus()
        
        def submit_specific_sonnet():
            num_str = poem_entry.get()
            if num_str.isdigit() and 1 <= int(num_str) <= 154:
                self.my_msg = f"p {num_str}" # ClientSM uses 'p <number>' for poem.
                poem_dialog.destroy()
            else:
                messagebox.showerror("Invalid Number", "Please enter a number between 1 and 154.", parent=poem_dialog)
        
        AOLButton(poem_dialog, text="Get Sonnet", command=submit_specific_sonnet).pack(pady=10)

    def show_set_pfp_dialog(self):
        """Displays a dialog for setting the user's profile picture URL."""
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
                self.my_msg = f"/setpfp {url}" # Command for ClientSM to set PFP.
                pfp_dialog.destroy()
            else:
                messagebox.showwarning("Input Needed", "Please enter a URL.", parent=pfp_dialog)
        
        AOLButton(pfp_dialog, text="Set Picture", command=submit_pfp_url).pack(pady=10)

    # Emoji related methods were removed as functionality is not implemented.
  
    def choose_player_dialog(self):
        """Displays a dialog to choose an opponent for Tic-Tac-Toe."""
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
            if name and name != self.name: # Ensure a name is entered and it's not self.
                self.my_msg = f"ttt{name}" # Command for ClientSM to start TTT.
                choose_dialog.destroy()
            elif name == self.name:
                messagebox.showwarning("Invalid Opponent", "You cannot play Tic-Tac-Toe against yourself.", parent=choose_dialog)
            else:
                messagebox.showwarning("Input Needed", "Please enter an opponent's name.", parent=choose_dialog)

        
        AOLButton(choose_dialog, text="Play", command=submit_player_name).pack(pady=10)
        
    def open_ttt_window(self,symbol):
        """Opens the Tic-Tac-Toe game window."""
        self.symbol = symbol # Player's symbol ('X' or 'O').
        peer_symbol = "O" if self.symbol == "X" else "X"
        
        # Tic-Tac-Toe window colors.
        color_blue = "#4584b6"
        color_yellow = "#ffde57"
        color_gray = "#343434"
        # color_light_gray = "#646464" # Unused variable

        self.board = [[None for _ in range(3)] for _ in range(3)] # 2D list to store TTT buttons.
        self.ttt_window = Toplevel(self.Window)
        self.ttt_window.title(f"Tic Tac Toe with {peer_symbol}")
        self.ttt_window.configure(bg=self.panel_color)
        
        # Set window size and center it.
        default_width = 450
        default_height = 555
        screen_width = self.ttt_window.winfo_screenwidth()
        screen_height = self.ttt_window.winfo_screenheight()
        window_x = int((screen_width / 2) - (default_width / 2))
        window_y = int((screen_height / 2) - (default_height / 2))
        self.ttt_window.geometry(f"{default_width}x{default_height}+{window_x}+{window_y}")
        
        self.ttt_window.resizable(False, False)
        self.ttt_window.transient(self.Window)

        # Main frame for TTT board and status.
        self.frame = Frame(self.ttt_window, bg=color_gray)
        self.frame.pack(padx=10, pady=10)
    
        # Status label to indicate whose turn it is.
        curr_player="X" # Initial display, will be updated by server.
        self.label = Label(self.frame, text=curr_player +"'s turn", font=("Consolas", 16), bg=color_gray, fg="white")
        self.label.grid(row=0, column=0, columnspan=3, sticky="we")

        # Create TTT board buttons.
        for r in range(3): # Changed 'row' to 'r' to avoid conflict
            for c in range(3): # Changed 'column' to 'c' to avoid conflict
                self.board[r][c] = Button(self.frame, text="", font=("Consolas", 50, "bold"),
                                                 background=color_gray, foreground=color_yellow,
                                                 width=4, height=1,
                                                 command=lambda r_btn=r, c_btn=c: self.make_move(r_btn, c_btn))
                self.board[r][c].grid(row=r+1, column=c)
                
        # Restart button.
        self.restart_button = Button(self.frame, text="Restart", font=("Consolas", 20),
                                     background=color_gray, foreground="white",
                                     command=lambda: messagebox.showinfo("Restart", "Restart functionality not fully implemented yet."))
        self.restart_button.grid(row=4, column=0, columnspan=3, sticky="we")
        
    
    def make_move(self, row, column):
        """Handles a Tic-Tac-Toe move made by the player."""
        if self.board[row][column]["text"] != "": # Cell already taken.
            return
        
        self.board[row][column]["text"] = self.symbol # Mark the cell with player's symbol.
        self.my_msg="move "+ str(row)+" "+ str(column)+ " from "+self.symbol # Prepare message for server.
        
        # Disable all board buttons after making a move, until server confirms next turn.
        for r_idx in range(3):
            for c_idx in range(3):
                if self.board[r_idx][c_idx]:
                    self.board[r_idx][c_idx].config(state=DISABLED)
        
    def sendButton(self, msg):
        """Handles sending a message when the send button is clicked or Enter is pressed."""
        msg = msg.strip() # Remove leading/trailing whitespace.
        if msg:
            # Check for /pm command for private messages.
            if msg.startswith("/pm "):
                parts = msg.split(" ", 2)
                if len(parts) == 3:
                    target_user = parts[1]
                    pm_message = parts[2]
                    self.my_msg = f"@{target_user} {pm_message}" # Format for ClientSM.
                else: # Invalid PM format, treat as a regular message.
                    self.my_msg = msg
            else: # Regular broadcast message.
                 self.my_msg = msg
                 
            self.entryMsg.delete(0, END) # Clear the message entry field.
            
    def proc(self):
        """
        Main processing loop that runs in a separate thread.
        Handles receiving messages from the server and processing user input/commands.
        """
        while True:
            # Check for incoming messages from the server without blocking.
            read, write, error = select.select([self.socket], [], [], 0)
            peer_msg_json = "" # Stores incoming JSON message string from the server.
            
            command_this_client_sent = self.my_msg # Capture user's command/message.

            if self.socket in read:
                peer_msg_json = self.recv() # Receive message if available.

            # Process if there's a user message or a message from the server.
            if len(self.my_msg) > 0 or len(peer_msg_json) > 0:
                # Let the state machine process the message/command.
                sm_output_string = self.sm.proc(self.my_msg, peer_msg_json)
                self.my_msg = "" # Clear user's message as it's being processed.

                if sm_output_string: # If state machine generated output for GUI.
                    self.textCons.config(state=NORMAL) # Enable text area for writing.
                    display_text_for_gui = ""

                    # --- Handle specific GUI updates based on state machine output ---
                    if sm_output_string.strip().startswith("GAME_OVER_UPDATE:"):
                        # Tic-Tac-Toe game ended, update TTT window.
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

                                # Update TTT board display with final state.
                                if final_board_state and hasattr(self, 'board'):
                                    for r_idx in range(3):
                                        for c_idx in range(3):
                                            if self.board[r_idx][c_idx]:
                                                self.board[r_idx][c_idx].config(text=final_board_state[r_idx][c_idx], state=DISABLED)
                                # Ensure all buttons are disabled.
                                for r_idx in range(3):
                                    for c_idx in range(3):
                                        if hasattr(self, 'board') and self.board[r_idx][c_idx]:
                                             self.board[r_idx][c_idx].config(state=DISABLED)
                            else: # If TTT window isn't open, show result in main chat.
                                display_text_for_gui = f"\nSYSTEM: Game Over! Winner: {winner if winner else 'Tie'}\n\n"
                            
                        except (json.JSONDecodeError, Exception) as e:
                            display_text_for_gui = "\nSYSTEM: Error processing game over message.\n\n"

                    elif "OPEN_TTT" in sm_output_string:
                        # Server or client initiated TTT, open the game window.
                        try:
                            # Parse the assigned symbol ('X' or 'O') from the state machine output.
                            stripped_sm_output = sm_output_string.strip()
                            parts = stripped_sm_output.split()
                            parsed_symbol = parts[-1]

                            if parsed_symbol not in ["X", "O"]: # Fallback parsing logic.
                                if len(parts) >= 3 and parts[-3].lower() == "opponent" and parts[-2].lower() == "turn" and parts[-1] in ["X", "O"]:
                                    parsed_symbol = parts[-1]
                                else:
                                    if hasattr(self.sm, 'symbol') and self.sm.symbol in ["X", "O"]:
                                        parsed_symbol = self.sm.symbol
                                    else:
                                        parsed_symbol = "X" # Absolute fallback.

                            self.symbol = parsed_symbol

                            if not hasattr(self, "ttt_window") or not self.ttt_window.winfo_exists():
                                self.open_ttt_window(self.symbol)
                            
                            if hasattr(self, 'label') and self.label.winfo_exists():
                                self.label.config(text="X's Turn (pending server)") # Initial status.
                            display_text_for_gui = "" # No text for main chat, TTT window handles display.
                            
                        except Exception as e:
                            display_text_for_gui = "\nSYSTEM: Error opening TTT window.\n\n"
                        
                    
                    elif "myturn" in sm_output_string and len(sm_output_string.split()) >= 4 :
                        # Opponent made a move, update TTT board for current player.
                        parts = sm_output_string.split()
                        row=int(parts[-2])
                        column=int(parts[-1])
                        opponent_symbol_played = "X" if self.symbol=="O" else "O"

                        if hasattr(self, 'board') and self.board[row][column]:
                            self.board[row][column]["text"]=opponent_symbol_played
                        
                        if hasattr(self, 'label'):
                            self.label["text"]=self.name+"'s turn (" + self.symbol + ")"
                        
                        # Enable empty buttons for the current player's move.
                        if hasattr(self, 'board'):
                            for r_idx in range(3):
                                for c_idx in range(3):
                                    if self.board[r_idx][c_idx]:
                                        if self.board[r_idx][c_idx]["text"] == "":
                                            self.board[r_idx][c_idx].config(state=NORMAL)
                                        else:
                                            self.board[r_idx][c_idx].config(state=DISABLED)
                        display_text_for_gui = "" # TTT window handles display.
                        
                                
                    elif "oppo nent turn" in sm_output_string and len(sm_output_string.split()) >= 3:
                        # Current player made a move, now it's opponent's turn. Disable board.
                        if hasattr(self, 'board'):
                            for r_idx in range(3):
                                for c_idx in range(3):
                                    if self.board[r_idx][c_idx]:
                                        self.board[r_idx][c_idx].config(state=DISABLED)
                        
                        turn_player_name = sm_output_string.split()[-1]
                        opponent_symbol_for_display = "X" if self.symbol == "O" else "O"

                        if hasattr(self, 'label'):
                            self.label["text"]=turn_player_name+"'s turn ("+ opponent_symbol_for_display +")"
                        display_text_for_gui = "" # TTT window handles display.
                        
                         
                        
                    elif command_this_client_sent == "who" and sm_output_string.startswith("USER_LIST_STRUCT:"):
                        # Received list of online users, display in a popup.
                        try:
                            user_list_json_str = sm_output_string.replace("USER_LIST_STRUCT:", "", 1)
                            user_list_data = json.loads(user_list_json_str)
                            self.show_user_list_popup(user_list_data)
                            display_text_for_gui = "" # Popup handles display.
                        except (json.JSONDecodeError, Exception) as e:
                            display_text_for_gui = "\nSYSTEM: Error displaying user list.\n\n"
                    
                    else: # General messages (time, poem, search, PMs, broadcasts, status).
                        stripped_output = sm_output_string.strip()
                        if stripped_output:
                            display_text_for_gui = stripped_output + "\n\n"
                        else:
                            display_text_for_gui = ""
                    
                    # Insert the processed text into the main chat window if any.
                    if display_text_for_gui:
                        self.textCons.insert(END, display_text_for_gui)
                        self.textCons.see(END) # Scroll to the latest message.
                    
                    self.textCons.config(state=DISABLED) # Disable text area after update.
    
    
    
    def show_user_list_popup(self, user_list_data):
        """Displays a popup window listing online users with their profile pictures."""
        if hasattr(self, 'user_list_window') and self.user_list_window.winfo_exists():
            self.user_list_window.destroy() # Close any existing user list window.

        self.user_list_window = Toplevel(self.Window)
        self.user_list_window.title("People Here")
        self.user_list_window.configure(bg=self.panel_color)
        self.user_list_window.geometry("400x500")
        self.user_list_window.transient(self.Window)

        # Canvas and scrollbar for a scrollable user list.
        canvas = Canvas(self.user_list_window, bg=self.panel_color)
        scrollbar = Scrollbar(self.user_list_window, orient="vertical", command=canvas.yview)
        scrollable_frame = Frame(canvas, bg=self.panel_color)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
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

            pfp_label = Label(user_frame, bg=self.aol_widget_bg) # Label to display PFP.
            pfp_label.pack(side=LEFT, padx=(0, 10))

            name_label = Label(user_frame, text=user_info.get("name", "N/A"), font=("Arial", 11, "bold"), bg=self.aol_widget_bg, fg=self.aol_text_on_grey)
            name_label.pack(side=LEFT, anchor="w")
            
            if PIL_AVAILABLE and user_info.get("pfp_url"):
                # Load PFP image in a separate thread to avoid freezing the GUI.
                threading.Thread(target=self.load_pfp_image, args=(user_info["pfp_url"], pfp_label), daemon=True).start()
            else:
                # Set a default placeholder if PIL is not available or no PFP URL.
                self.set_pfp_placeholder(pfp_label)


    def load_pfp_image(self, url, pfp_label_widget):
        """Loads a profile picture from a URL and updates the given label widget."""
        try:
            response = requests.get(url, stream=True, timeout=5) # Fetch image with timeout.
            response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx).
            img = Image.open(response.raw)
            img.thumbnail((50, 50)) # Resize image to a 50x50 thumbnail.
            photo = ImageTk.PhotoImage(img)
            
            # Schedule the GUI update on the main Tkinter thread.
            self.Window.after(0, lambda: self.update_pfp_label(pfp_label_widget, photo))

        except requests.exceptions.RequestException as e:
            self.Window.after(0, lambda: self.set_pfp_placeholder(pfp_label_widget, "[Fetch Err]"))
        except Exception as e: # Catch other image processing errors.
            self.Window.after(0, lambda: self.set_pfp_placeholder(pfp_label_widget, "[Load Err]"))

    def update_pfp_label(self, label_widget, photo_image):
        """Updates the PFP label with the loaded image. Must be called from the main thread."""
        if label_widget.winfo_exists(): # Ensure widget still exists before updating.
            label_widget.config(image=photo_image)
            label_widget.image = photo_image # Keep a reference to prevent garbage collection.

    def set_pfp_placeholder(self, label_widget, text="[PFP]"):
        """Sets a placeholder for the PFP if loading fails or PIL is unavailable."""
        if label_widget.winfo_exists():
            if PIL_AVAILABLE: # Try to create a graphical placeholder if PIL is available.
                try:
                    placeholder_img = Image.new('RGB', (50, 50), color = 'lightgrey')
                    placeholder_photo = ImageTk.PhotoImage(placeholder_img)
                    label_widget.config(image=placeholder_photo, text="")
                    label_widget.image = placeholder_photo
                    return
                except Exception as e:
                    pass # Fall through to text placeholder if graphical one fails.
            
            # Fallback to a simple text placeholder.
            label_widget.config(image=None, text=text, width=7, height=3)


    def run(self):
        """Starts the GUI by displaying the login window."""
        self.login()

# Main execution block (typically not run directly, GUI is started by chat_client_class.py).
# if __name__ == "__main__":
#     pass
