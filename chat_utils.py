import socket
import time

# Default IP address for the chat server.
CHAT_IP = '127.0.0.1'  # Using localhost.

CHAT_PORT = 1112
SERVER = (CHAT_IP, CHAT_PORT)

menu = "\n=== Welcome to Chat ===\n\n" + \
       "Use the buttons on the left sidebar to navigate the chat.\n" + \
       "Enjoy chatting! 💬\n"

S_OFFLINE   = 0
S_CONNECTED = 1
S_LOGGEDIN  = 2
S_CHATTING  = 3

SIZE_SPEC = 5

CHAT_WAIT = 0.2

def print_state(state):
    print('**** State *****::::: ')
    if state == S_OFFLINE:
        print('Offline')
    elif state == S_CONNECTED:
        print('Connected')
    elif state == S_LOGGEDIN:
        print('Logged in')
    elif state == S_CHATTING:
        print('Chatting')
    else:
        print('Error: wrong state')

def mysend(s, msg):
    # Prepend message with its size, formatted to SIZE_SPEC digits.
    msg = ('0' * SIZE_SPEC + str(len(msg)))[-SIZE_SPEC:] + str(msg)
    msg = msg.encode()
    total_sent = 0
    while total_sent < len(msg) :
        sent = s.send(msg[total_sent:])
        if sent==0:
            print('server disconnected')
            break
        total_sent += sent

def myrecv(s):
    # First, receive the size of the incoming message.
    size = ''
    while len(size) < SIZE_SPEC:
        text = s.recv(SIZE_SPEC - len(size)).decode()
        if not text:
            print('disconnected')
            return('')
        size += text
    size = int(size)
    # Then, receive the actual message content based on the determined size.
    msg = ''
    while len(msg) < size:
        text = s.recv(size-len(msg)).decode()
        if text == b'': # Check for empty byte string indicating disconnection.
            print('disconnected')
            break
        msg += text
    return (msg)

def text_proc(text, user):
    # Formats a chat message with a timestamp and username.
    ctime = time.strftime('%I:%M %p', time.localtime())
    return(f'[{ctime}] {user}: {text}')
