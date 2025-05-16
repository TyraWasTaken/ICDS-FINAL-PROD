import tkinter as tk
from tkinter import ttk, messagebox
import emoji

class EmojiTestApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Emoji Test Application")
        self.root.geometry("800x600")
        
        # Create main frame
        self.main_frame = ttk.Frame(self.root, padding=20)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Chat display
        ttk.Label(self.main_frame, text="Chat Display:", font=("Helvetica", 14, "bold")).pack(anchor="w")
        
        chat_frame = ttk.Frame(self.main_frame)
        chat_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.chat_display = tk.Text(chat_frame, wrap=tk.WORD, font=("Helvetica", 12))
        self.chat_display.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(chat_frame, command=self.chat_display.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.chat_display.config(yscrollcommand=scrollbar.set)
        
        # Input area
        input_frame = ttk.Frame(self.main_frame)
        input_frame.pack(fill=tk.X, pady=10)
        
        self.emoji_btn = ttk.Button(input_frame, text="😊", width=3, command=self.show_emoji_picker)
        self.emoji_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.message_entry = ttk.Entry(input_frame, font=("Helvetica", 12))
        self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.message_entry.bind("<Return>", self.send_message)
        
        send_btn = ttk.Button(input_frame, text="Send", command=self.send_message)
        send_btn.pack(side=tk.RIGHT)
        
        # Testing buttons
        test_frame = ttk.LabelFrame(self.main_frame, text="Emoji Tests", padding=10)
        test_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(test_frame, text="Test Direct Emoji", command=self.test_direct_emoji).pack(side=tk.LEFT, padx=5)
        ttk.Button(test_frame, text="Test Emoji Module", command=self.test_emoji_module).pack(side=tk.LEFT, padx=5)
        ttk.Button(test_frame, text="Test Emoji Picker", command=self.show_emoji_picker).pack(side=tk.LEFT, padx=5)
        ttk.Button(test_frame, text="Clear Display", command=self.clear_display).pack(side=tk.RIGHT)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set(f"Emoji module version: {emoji.__version__}")
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Focus the entry
        self.message_entry.focus_set()
    
    def send_message(self, event=None):
        message = self.message_entry.get().strip()
        if message:
            try:
                self.chat_display.config(state=tk.NORMAL)
                self.chat_display.insert(tk.END, f"You: {message}\n\n")
                self.chat_display.see(tk.END)
                self.chat_display.config(state=tk.DISABLED)
                self.message_entry.delete(0, tk.END)
                self.status_var.set("Message sent successfully")
            except Exception as e:
                self.status_var.set(f"Error: {str(e)}")
    
    def test_direct_emoji(self):
        emojis = ["😀", "😎", "👍", "❤️", "🐱", "🍕", "🎮", "🚀"]
        try:
            self.chat_display.config(state=tk.NORMAL)
            self.chat_display.insert(tk.END, "=== Direct Emoji Test ===\n")
            for e in emojis:
                self.chat_display.insert(tk.END, f"{e} ")
            self.chat_display.insert(tk.END, "\n\n")
            self.chat_display.see(tk.END)
            self.chat_display.config(state=tk.DISABLED)
            self.status_var.set("Direct emoji test completed")
        except Exception as e:
            self.status_var.set(f"Error: {str(e)}")
    
    def test_emoji_module(self):
        try:
            self.chat_display.config(state=tk.NORMAL)
            self.chat_display.insert(tk.END, "=== Emoji Module Test ===\n")
            
            # Test emojize
            smile = emoji.emojize(":smile:", language="alias")
            heart = emoji.emojize(":heart:", language="alias")
            thumbsup = emoji.emojize(":thumbsup:", language="alias")
            
            self.chat_display.insert(tk.END, f"emojize(':smile:') = {smile}\n")
            self.chat_display.insert(tk.END, f"emojize(':heart:') = {heart}\n")
            self.chat_display.insert(tk.END, f"emojize(':thumbsup:') = {thumbsup}\n\n")
            
            # Test demojize
            self.chat_display.insert(tk.END, f"demojize('😀') = {emoji.demojize('😀')}\n")
            self.chat_display.insert(tk.END, f"demojize('❤️') = {emoji.demojize('❤️')}\n")
            self.chat_display.insert(tk.END, f"demojize('👍') = {emoji.demojize('👍')}\n\n")
            
            self.chat_display.see(tk.END)
            self.chat_display.config(state=tk.DISABLED)
            self.status_var.set("Emoji module test completed")
        except Exception as e:
            self.status_var.set(f"Error: {str(e)}")
            messagebox.showerror("Error", f"Emoji module test failed: {str(e)}")
    
    def show_emoji_picker(self):
        emoji_window = tk.Toplevel(self.root)
        emoji_window.title("Emoji Picker")
        emoji_window.geometry("400x300")
        
        emoji_frame = ttk.Frame(emoji_window, padding=10)
        emoji_frame.pack(fill=tk.BOTH, expand=True)
        
        common_emojis = [
            "😀", "😃", "😄", "😁", "😆", "😅", "😂", "🤣", "☺️", "😊",
            "❤️", "🧡", "💛", "💚", "💙", "💜", "🖤", "🤍", "🤎", "💔",
            "👍", "👎", "👏", "🙌", "🤝", "🙏", "🤲", "👐", "🤟", "🤘"
        ]
        
        row = 0
        col = 0
        for e in common_emojis:
            btn = tk.Button(emoji_frame, text=e, font=("Helvetica", 20), width=2, height=1,
                          command=lambda x=e: self.insert_emoji(x, emoji_window))
            btn.grid(row=row, column=col, padx=5, pady=5)
            col += 1
            if col >= 10:
                col = 0
                row += 1
    
    def insert_emoji(self, emoji_char, window):
        try:
            current_text = self.message_entry.get()
            self.message_entry.delete(0, tk.END)
            self.message_entry.insert(0, current_text + emoji_char)
            window.destroy()
            self.status_var.set(f"Inserted emoji: {emoji_char}")
        except Exception as e:
            self.status_var.set(f"Error inserting emoji: {str(e)}")
            messagebox.showerror("Error", f"Could not insert emoji: {str(e)}")
    
    def clear_display(self):
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete(1.0, tk.END)
        self.chat_display.config(state=tk.DISABLED)
        self.status_var.set("Display cleared")

if __name__ == "__main__":
    root = tk.Tk()
    app = EmojiTestApp(root)
    root.mainloop() 