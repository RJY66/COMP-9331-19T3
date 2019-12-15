# COMP 9331 Lab3:DNS & Socket Programming
# Python version:3.7.2
# Writer:Junyu Ren
# Date:2019-10-11

import sys
from socket import *

if len(sys.argv) != 2:
    print("Incorrect input! Giving up...")
    sys.exit()

port = int(sys.argv[1])
serversocket = socket(AF_INET, SOCK_STREAM)
serversocket.bind(('', port))
serversocket.listen(100)

while True:
    try:
        conn, addr = serversocket.accept()
        received = conn.recv(4096).decode()
        resourcepath = received.split()[1].strip('/')
        file = open(resourcepath, 'rb')
        display = file.read()
        conn.sendall(b'HTTP/1.1 200 OK\n\n')
        conn.sendall(display)
        conn.close()
    except IOError:
        conn.sendall(b'HTTP/1.1 404 Not Found\n\n')
        conn.sendall(b'<h1><center>404 Not Found</center></h1>')
        conn.close()





