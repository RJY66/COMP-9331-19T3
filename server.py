# COMP 9331 Assignment:Instant message application
# server.py: functions of a server
# Author: Junyu Ren
# Student ID: z5195715
# Date: 2019-11-19
# Python version: 3.7.2

import threading
import socket
import time
import select
import sys


class Server:
    accounts = {}
    online_users = []  # record login time
    login_tries = {}  # record login tries
    login_block = {}  # record login block time
    active_users = {}  # record active time
    login_history = {}
    block_duration = 0
    timeout = 0
    user_sockets = {}  # correlate name and sockets
    messages = {}
    blocks = {}  # block user from receiving messages
    client_servers = {}
    port = 0

    def __init__(self, port, duration, timeout):
        self.block_duration = duration
        self.timeout = timeout
        self.port = port
        # read credentials
        with open('credentials.txt', 'r') as cred:
            for line in cred.readlines():
                name, pwd = line.strip().split(' ')
                self.accounts[name] = pwd
                self.login_tries[name] = 0
                self.login_block[name] = -1
                self.active_users[name] = -1
                self.blocks[name] = []

    # process request from client
    def process(self, client, address):
        while True:
            req = client.recv(1024).decode('utf-8')
            if req:
                if " " in req:
                    cmd = req.split(' ')[0]
                    data = ' '.join(req.split(' ')[1:])
                    # print(data)
                else:
                    cmd = req

                if cmd == 'login':
                    name, pwd = data.split('&')
                    # print(name,pwd)
                    if name in self.accounts:

                        # block duration
                        if self.login_block[name] != -1 and time.time() - \
                                self.login_block[name] < self.block_duration:
                            client.send('blocked'.encode('utf-8'))
                        else:
                            self.login_block[name] = -1  # recover block status
                            if pwd == self.accounts[name]:
                                if self.online(name):  # already login
                                    client.send('online'.encode('utf-8'))
                                else:
                                    # broadcast presence
                                    self.broadcast_presence(name)
                                    self.online_users.append((name, time.time()))
                                    self.active_users[name] = time.time()
                                    self.user_sockets[name] = (client, address)
                                    self.login_tries[name] = 0
                                    self.login_history[name] = time.time()
                                    client.send('success '.encode('utf-8'))
                                    if name in self.messages:
                                        for sender, msg in self.messages[name]:
                                            client.send(('history ' + sender + ' ' + msg).encode('utf-8'))
                                    # print('success')
                            else:
                                self.login_tries[name] += 1  # add tries
                                if self.login_tries[name] >= 3:
                                    # print('block')
                                    client.sendto('blocked'.encode('utf-8'), address)
                                    self.login_block[name] = time.time()
                                    # client.close()
                                    # break
                                else:
                                    client.sendto('wrong password'.encode('utf-8'), address)
                    else:
                        client.sendto('wrong username'.encode('utf-8'), address)
                else:
                    username = cmd.split('@')[0]
                    cmd = cmd.split('@')[1]
                    if self.online(username):
                        # receive command, update active time
                        self.active_users[username] = time.time()

                        # if cmd == 'online':
                        #     users = self.list_online_users(username)
                        #     client.send(('online ' + '&'.join(users)).encode('utf-8'))

                        if cmd == 'message':
                            receipt, msg = data.split('&')
                            if receipt == username or receipt not in self.accounts:
                                client.send('Invalidreceiver!'.encode('utf-8'))
                            elif username in self.blocks[receipt]:
                                client.send(('Blocked by ' + receipt).encode('utf-8'))
                            else:
                                if self.online(receipt):
                                    self.user_sockets[receipt][0].send(
                                        ('message ' + username + ' ' + msg).encode('utf-8'))
                                else:
                                    if receipt in self.messages:
                                        self.messages[receipt].append((username, msg))
                                    else:
                                        self.messages[receipt] = [(username, msg)]
                        elif cmd == 'broadcast':
                            users = self.list_online_users_broadcast(username)
                            for item in users:
                                self.user_sockets[item][0].send(('broadcast ' + username + ' ' + data).encode('utf-8'))
                            # blockedusers = '&'.join(self.blocks[username])
                            # if len(blockedusers) > 2:
                            for user in self.blocks:
                                if username in self.blocks[user]:
                                    client.send(('nbroadcast').encode('utf-8'))
                                    break
                        elif cmd == 'whoelse':
                            names = ''
                            for item in self.online_users:
                                un = item[0]
                                if un != username:
                                    names += un + '&'
                            client.send(('whoelse ' + names).encode('utf-8'))
                        elif cmd == 'whoelsesince':
                            period = int(data)
                            names = self.online_history(period, username)
                            client.send(('whoelsesince ' + names).encode('utf-8'))
                        elif cmd == 'block':
                            if data == username or data not in self.accounts:
                                client.send('Invalidblock!'.encode('utf-8'))
                            else:
                                self.blocks[username].append(data)
                                client.send(('block ' + data).encode('utf-8'))
                        elif cmd == 'unblock':
                            if data == username or data not in self.accounts or data not in self.blocks[username]:
                                client.send('Invalidunblock!'.encode('utf-8'))
                            else:
                                self.blocks[username].remove(data)
                                client.send(('unblock ' + data).encode('utf-8'))
                        elif cmd == 'logout':
                            for item in self.online_users:
                                if item[0] == username:
                                    self.online_users.remove(item)
                                    # you log out
                                    client.send('youlogout'.encode('utf-8'))
                                    # broadcast your log out
                                    for item in self.online_users:
                                        user = item[0]
                                        self.user_sockets[user][0].send(('logout ' + username).encode('utf-8'))
                                    break
                            # client.close()
                        elif cmd == 'startprivate':
                            if data == username or data not in self.accounts or not self.online(data):
                                client.send('Invalidprivate!'.encode('utf-8'))
                            elif username in self.blocks[data]:
                                client.send(('Blocked by ' + data).encode('utf-8'))
                            else:
                                addr = self.client_servers[data]
                                # print(addr)
                                client.send(('startprivate ' + data + ' ' + addr[0] + ' ' + addr[1]).encode('utf-8'))
                        elif cmd == 'success':
                            ip, port = data.split('&')
                            self.client_servers[username] = (ip, port)

                    else:
                        client.send('nologin'.encode('utf-8'))

    # whether is on line
    def online(self, name):
        for item in self.online_users:
            user = item[0]
            if name == user:
                return True
        return False

    # If the server does not receive any commands from a user for a period of timeout seconds
    # log out
    def offline(self):
        while True:
            for item in self.online_users:
                user = item[0]
                if self.active_users[user] != -1 and time.time() - self.active_users[user] > self.timeout:
                    sock, addr = self.user_sockets[user]
                    sock.sendto('timeout'.encode('utf-8'), addr)
                    self.active_users[user] = -1
                    self.online_users.remove(item)
                    self.user_sockets[user] = None

    # broadcast user's login
    def broadcast_presence(self, name):
        for item in self.online_users:
            user = item[0]
            self.user_sockets[user][0].send(('newer ' + name).encode('utf-8'))

    # list online users
    def list_online_users(self, currentuser):
        names = []
        for item in self.online_users:
            user = item[0]
            if user != currentuser and user not in self.blocks[currentuser]:
                names.append(user)
        return names

    # list online users for broadcast
    def list_online_users_broadcast(self, currentuser):
        names = []
        for item in self.online_users:
            user = item[0]
            if user != currentuser and currentuser not in self.blocks[user]:
                names.append(user)
        return names

    # The sever should provide a list of users that logged in for a user specified time in
    # the past
    def online_history(self, period, currentuser):
        names = ''
        for item in self.login_history:
            t = self.login_history[item]
            if item != currentuser and time.time() - t < period:
                names += item + '&'
        return names

    # start the server
    def start(self, port):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(('127.0.0.1', port))
        server.listen(10)
        # log out timeout user
        t1 = threading.Thread(target=self.offline)
        t1.start()
        # listen for user connecting
        while True:
            r, w, e = select.select([server, ], [], [], 1)
            for server in r:
                conn, addr = server.accept()
                t = threading.Thread(target=self.process, args=(conn, addr))
                t.start()
        server.close()


if __name__ == '__main__':
    if len(sys.argv) == 4:
        port = int(sys.argv[1])
        block_duration = int(sys.argv[2])
        timeout = int(sys.argv[3])
        server = Server(port, block_duration, timeout)
        server.start(port)
