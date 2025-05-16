# Plan for Emoji Phase A: Unicode-Based Picker and Display

**Goal:** Create a pop-up emoji picker that allows users to select emojis. These emojis will be inserted as Unicode characters into the message input fields and rendered by the system's font in the chat display areas.

**1. Emoji Data Source (Curated List within `GUI.py`):**
   *   Define a dictionary `EMOJI_SET` in `GUI.py` (or a helper file) to store Unicode emoji characters, organized by categories.
     ```python
     # Example:
     EMOJI_SET = {
         "Smileys & People": [("😀", "Grinning Face"), ("😂", "Face With Tears of Joy"), ("👍", "Thumbs Up"), /* ... */],
         "Animals & Nature": [("🐶", "Dog Face"), ("🐱", "Cat Face"), /* ... */],
         # Add more categories and emojis as desired
     }
     ```

**2. `GUI.__init__` Additions:**
   *   `self.emoji_picker_window = None` (To hold the reference to the picker Toplevel window).
   *   `self.current_target_emoji_entry = None` (To store the Entry widget that should receive the emoji).

**3. New GUI Method: `show_emoji_picker(self, target_entry_widget)`:**
   *   Called by "Emoji" buttons next to message input fields.
   *   `target_entry_widget`: The `Entry` field where the selected emoji should be inserted.
   *   **Functionality:**
        a.  If `self.emoji_picker_window` exists and is visible, `lift()` and `focus_force()` it. Update `self.current_target_emoji_entry = target_entry_widget`.
        b.  Else (first time or previously closed):
            i.  `self.emoji_picker_window = Toplevel(self.Window)`.
            ii. Set title ("Select Emoji"), geometry, make it transient, apply AOL styling.
            iii. Store `self.current_target_emoji_entry = target_entry_widget`.
            iv. Implement a layout for categories and emojis:
                *   **Option 1 (Simple Sections):** Use `Label` widgets for category headers, followed by a `Frame` containing a grid of emoji buttons for that category. The whole picker might be in a scrollable canvas if content exceeds window height.
                *   **Option 2 (Notebook for Categories):** Use `ttk.Notebook`. Each tab represents a category. The content of each tab is a scrollable `Frame` with a grid of emoji buttons.
                *   For each emoji in `EMOJI_SET` for a category:
                    *   Create a `Button` with its `text` as the emoji Unicode character (e.g., "😀").
                    *   Ensure button font is adequate for emoji visibility.
                    *   Button command: `lambda char=emoji_unicode_str, entry=self.current_target_emoji_entry: self._insert_emoji_char(char, entry)`.
        c.  The picker window should remain open after an emoji is selected, allowing multiple selections. Add a close button or rely on the window's standard close button.

**4. New GUI Method: `_insert_emoji_char(self, emoji_char, entry_widget)`:**
   *   `entry_widget.insert(INSERT, emoji_char)` (Inserts the Unicode emoji string at the current cursor position in the specified `Entry` widget).

**5. Add "Emoji" Buttons to Input Areas:**
   *   **Main Chat Input (`GUI.layout`):**
        *   In `input_area_frame` (near [`GUI.py:250`](GUI.py:250)), add an `AOLSmallButton` (e.g., text "🙂" or "Emoji").
        *   Command: `lambda: self.show_emoji_picker(self.entryMsg)`.
   *   **Private Messaging Input (`GUI._create_private_chat_window`):**
        *   In `pm_input_area_frame`, add a similar `AOLSmallButton`.
        *   Command: `lambda: self.show_emoji_picker(self.pm_input_entry)`.

**6. Display in `Text` Widgets (Main Chat & PMs):**
   *   No special rendering logic is added to the `Text` widgets in this phase.
   *   Messages containing Unicode emoji characters will be inserted directly.
   *   Tkinter will use the system's default font to attempt to render these Unicode characters. The visual appearance (monochrome, color, specific glyph) will depend on the capabilities of this font on the user's system.

**Considerations:**
*   **Font:** Select a default font for the application (and specifically for emoji buttons in the picker) that has good Unicode emoji coverage.
*   **Curated Set Size:** Start with a manageable number of emojis (e.g., 100-200) to keep the picker UI reasonable to build and performant.
*   **Picker Closing:** Decide if the picker closes on selection or stays open. Staying open is more modern.