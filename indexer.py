# -*- coding: utf-8 -*-

import pickle

class Index:
    def __init__(self, name):
        self.name = name
        self.msgs = []
        self.index = {}
        self.total_msgs = 0
        self.total_words = 0
        
    def get_total_words(self):
        return self.total_words
        
    def get_msg_size(self):
        return self.total_msgs
        
    def get_msg(self, n):
        return self.msgs[n]
        
    def add_msg(self, m):
        self.msgs.append(m)
        self.total_msgs += 1
        
    def add_msg_and_index(self, m):
        self.add_msg(m)
        line_at = self.total_msgs - 1
        self.indexing(m, line_at)
 
    def indexing(self, m, l):
        words = m.split()
        self.total_words += len(words)
        for wd in words:
            if wd not in self.index:
                self.index[wd] = [l,]
            else:
                self.index[wd].append(l)
                                     
    def search(self, term):
        msgs = []
        if (term in self.index.keys()):
            indices = self.index[term]
            msgs = [(i, self.msgs[i]) for i in indices]
        return msgs

class PIndex(Index):
    def __init__(self, name):
        super().__init__(name)
        try:
            with open('roman.txt.pk', 'rb') as roman_int_f:
                self.int2roman = pickle.load(roman_int_f)
        except FileNotFoundError:
            print("ERROR: roman.txt.pk not found. Please ensure it's in the correct location.")
            raise
        except pickle.PickleError as e:
            print(f"ERROR: Could not load Roman numeral mapping from roman.txt.pk: {e}")
            raise
        self.load_poems()
        
    def load_poems(self):
        try:
            with open(self.name, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            for l in lines:
                self.add_msg_and_index(l.rstrip())
        except FileNotFoundError:
            print(f"ERROR: Poem file '{self.name}' not found.")
        except Exception as e:
            print(f"ERROR: An unexpected error occurred while loading poems from '{self.name}': {e}")
    
    def get_poem(self, p):
        # Check if the requested sonnet number is valid
        if p not in self.int2roman:
            return []

        p_str = self.int2roman[p] + '.'
        
        # Determine the marker for the next sonnet, if it exists
        p_next_str = None
        if (p + 1) in self.int2roman:
            p_next_str = self.int2roman[p + 1] + '.'
        temp = self.search(p_str)
        if temp:
            [(go_line, m)] = temp
        else:
            return []
        # in case of wrong number
        poem = []
        end = self.get_msg_size()

        # Advance go_line past the Roman numeral marker itself.
        # The initial go_line IS the marker line.
        go_line += 1
        
        # Skip any blank lines immediately following the marker
        while go_line < end and not self.get_msg(go_line).strip():
            go_line += 1
            
        # Collect actual poem lines
        while go_line < end:
            this_line = self.get_msg(go_line)
            # Stop if we hit the marker for the next sonnet
            # Stop if we hit the marker for the next sonnet (and p_next_str is defined)
            if p_next_str is not None and this_line == p_next_str:
                break
            # Add non-blank lines, stripping leading spaces
            if this_line.strip():
                poem.append(this_line.lstrip())
            go_line += 1
        return poem
