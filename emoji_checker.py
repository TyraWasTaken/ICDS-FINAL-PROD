import tkinter as tk
from tkinter import ttk, messagebox
import emoji  # Import the emoji module

class EmojiTest:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Emoji Test Window")
        self.root.geometry("600x400")
        
        # Create main frame
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Add labels to display emoji
        ttk.Label(main_frame, text="Direct emoji rendering test:", font=("Helvetica", 14)).pack(pady=(0, 5))
        
        # Test direct emoji display
        emoji_frame = ttk.Frame(main_frame)
        emoji_frame.pack(pady=10)
        
        emojis = ["😀", "😃", "😄", "👍", "❤️", "🐱"]
        for e in emojis:
            btn = tk.Button(emoji_frame, text=e, font=("Helvetica", 24), 
                          width=2, height=1, command=lambda x=e: self.show_emoji_info(x))
            btn.pack(side=tk.LEFT, padx=5)
        
        # Test emoji module
        ttk.Label(main_frame, text="Emoji module test:", font=("Helvetica", 14)).pack(pady=(20, 5))
        
        module_frame = ttk.Frame(main_frame)
        module_frame.pack(pady=10)
        
        # Display emoji module version
        try:
            version_label = ttk.Label(module_frame, text=f"Emoji module version: {emoji.__version__}")
            version_label.pack()
        except AttributeError:
            version_label = ttk.Label(module_frame, text="Could not get emoji module version")
            version_label.pack()
        
        # Test emoji.emojize
        try:
            emoji_text = emoji.emojize(":smile:", language="alias")
            emojize_label = ttk.Label(module_frame, text=f"emoji.emojize(':smile:') = {emoji_text}", 
                                    font=("Helvetica", 12))
            emojize_label.pack(pady=5)
        except Exception as e:
            emojize_label = ttk.Label(module_frame, text=f"Error: {str(e)}", 
                                    font=("Helvetica", 12))
            emojize_label.pack(pady=5)
        
        # Test emoji.demojize
        try:
            emoji_text = emoji.demojize("😀", language="alias")
            demojize_label = ttk.Label(module_frame, text=f"emoji.demojize('😀') = {emoji_text}", 
                                     font=("Helvetica", 12))
            demojize_label.pack(pady=5)
        except Exception as e:
            demojize_label = ttk.Label(module_frame, text=f"Error: {str(e)}", 
                                     font=("Helvetica", 12))
            demojize_label.pack(pady=5)
        
        # Check for indentation error in GUI.py
        ttk.Label(main_frame, text="Checking for syntax issues in GUI.py:", font=("Helvetica", 14)).pack(pady=(20, 5))
        
        try:
            with open("GUI.py", "r", encoding="utf-8") as f:
                code = f.read()
            # Try to compile the code to check for syntax errors
            compile(code, "GUI.py", "exec")
            syntax_label = ttk.Label(main_frame, text="No syntax errors found in GUI.py", 
                                   font=("Helvetica", 12))
            syntax_label.pack(pady=5)
        except Exception as e:
            syntax_label = ttk.Label(main_frame, text=f"Syntax error in GUI.py: {str(e)}", 
                                   font=("Helvetica", 12))
            syntax_label.pack(pady=5)
        
    def show_emoji_info(self, emoji_char):
        try:
            emoji_name = emoji.demojize(emoji_char)
            messagebox.showinfo("Emoji Info", f"Emoji: {emoji_char}\nName: {emoji_name}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not process emoji: {str(e)}")
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = EmojiTest()
    app.run() 