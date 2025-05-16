# -*- coding: utf-8 -*-

S_ALONE = 0
S_TALKING = 1

#==============================================================================
# Group Class
# Manages users and their chat group memberships.
#
# Member Fields:
#   - self.members: A dictionary mapping usernames to their status (S_ALONE or S_TALKING).
#   - self.chat_grps: A dictionary mapping group IDs to a list of usernames in that group.
#   - self.grp_ever: A counter to generate unique group IDs.
#
# Member Functions:
#   - join(name): Adds a user to the system.
#   - is_member(name): Checks if a user is in the system.
#   - leave(name): Removes a user from the system and any chat group.
#   - get_all_members(): Returns a list of all online users.
#   - find_group(name): Finds the group ID a user belongs to.
#   - connect(me, peer): Connects two users into a chat group.
#   - disconnect(me): Removes a user from their current chat group.
#   - list_all(): Returns a string listing all online users and active chat groups.
#   - list_me(me): Returns a list of users in the same chat group as 'me'.
#==============================================================================

class Group:
    """
    Manages users and their chat group memberships.
    """
    def __init__(self):
        self.members = {}  # Stores username -> status (S_ALONE, S_TALKING)
        self.chat_grps = {}  # Stores group_id -> list_of_usernames
        self.grp_ever = 0  # Counter for unique group IDs

    def join(self, name):
        """Adds a user to the system with S_ALONE status."""
        self.members[name] = S_ALONE
        return

    def is_member(self, name):
        """Checks if a user is currently a member of the system."""
        return name in self.members.keys()

    def leave(self, name):
        """Removes a user from the system and any chat group they are in."""
        self.disconnect(name) # Disconnect from any active chat group first.
        # self.disconnect(name) # Redundant call removed.
        if name in self.members:
            del self.members[name]
        return
    
    def get_all_members(self):
        """Returns a list of all currently logged-in usernames."""
        return list(self.members.keys())

    def find_group(self, name):
        """
        Finds the group ID that a given user belongs to.
        Returns: (bool: found, int: group_key)
        """
        found = False
        group_key = 0 # Default to 0, indicating no specific group or S_ALONE.
        for k in self.chat_grps.keys():
            if name in self.chat_grps[k]:
                found = True
                group_key = k
                break
        return found, group_key

    def connect(self, me, peer):
        """
        Connects user 'me' with user 'peer'.
        If 'peer' is already in a group, 'me' joins that group.
        Otherwise, a new group is created for 'me' and 'peer'.
        """
        peer_in_group, group_key = self.find_group(peer)
        
        if peer_in_group == True:
            # Peer is already in a group, so 'me' joins it.
            # print(peer, "is talking already, connect!") # Debug print removed
            self.chat_grps[group_key].append(me)
            self.members[me] = S_TALKING
        else:
            # Peer is not in a group, create a new group for 'me' and 'peer'.
            # print(peer, "is idle as well") # Debug print removed
            self.grp_ever += 1 # Increment for a new unique group ID.
            group_key = self.grp_ever
            self.chat_grps[group_key] = [me, peer] # Create new group with both users.
            self.members[me] = S_TALKING
            self.members[peer] = S_TALKING
        # print(self.list_me(me)) # Debug print removed
        return

    def disconnect(self, me):
        """
        Disconnects user 'me' from their current chat group.
        If the group becomes empty or has only one member after 'me' leaves,
        the group is dissolved and remaining members are set to S_ALONE.
        """
        in_group, group_key = self.find_group(me)
        if in_group == True:
            self.chat_grps[group_key].remove(me)
            self.members[me] = S_ALONE
            # If the group is now empty or has only one person, dissolve it.
            if len(self.chat_grps[group_key]) <= 1:
                if len(self.chat_grps[group_key]) == 1: # One peer remaining
                    peer = self.chat_grps[group_key].pop()
                    self.members[peer] = S_ALONE
                del self.chat_grps[group_key] # Delete the group.
        return

    def list_all(self):
        """
        Generates a string listing all online users and active chat groups.
        """
        s = "Online Users:\n"
        if not self.members:
            s += "- No users currently online.\n"
        else:
            for user_name in self.members.keys():
                s += f"- {user_name}\n"
        s += "\n"

        s += "Active Chat Groups:\n"
        active_groups_found = False
        if self.chat_grps:
            for grp_id, members_list in self.chat_grps.items():
                if members_list and len(members_list) > 1: # Only list groups with 2+ members.
                    members_str = ", ".join(members_list)
                    s += f"- Chat between: {members_str}\n"
                    active_groups_found = True
        
        if not active_groups_found:
            s += "- No active peer-to-peer chats.\n"
            
        return s

    # def list_all2(self, me): # Debugging method removed
    #     print("Users: ------------")
    #     print(self.members)
    #     print("Groups: -----------")
    #     print(self.chat_grps, "\n")
    #     member_list = str(self.members)
    #     grp_list = str(self.chat_grps)
    #     return member_list, grp_list

    def list_me(self, me):
        """
        Returns a list containing 'me' and other peers in 'me's current chat group.
        If 'me' is not in a group, returns a list containing only 'me'.
        """
        if me in self.members.keys():
            my_list = [me] # Start with 'me'.
            in_group, group_key = self.find_group(me)
            if in_group == True:
                for member in self.chat_grps[group_key]:
                    if member != me:
                        my_list.append(member)
            return my_list
        return [] # Should not happen if 'me' is a valid member.

# if __name__ == "__main__": # Test code removed
#     g = Group()
#     g.join('a')
#     g.join('b')
#     print(g.list_all())
#     g.list_all2('a')
#     g.connect('a', 'b')
#     print(g.list_all())
