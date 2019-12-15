# COMP 9331 Assignment:Instant message application
# client.py: functions of a client
# Author: Junyu Ren
# Student ID: z5195715
# Date: 2019-11-19
# Python version: 3.7.2

import socket
import threading
import sys
import select


class Client(threading.Thread):
    sock = None
    name = ''
    privates = {}
    server = None
    ip = ''
    port = ''

    def __init__(self, ip, port):
        super(Client, self).__init__()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((ip, port))

        hostname = socket.gethostname()
        self.ip = socket.gethostbyname(hostname)
        # self.port = str(random.randint(60000, 64444))
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.ip, 0))
        self.port = str(self.server.getsockname()[1])
        self.server.listen(10)

        t = threading.Thread(target=self.private_server, args=(self.server,))
        t.start()

    def private_server(self, server):
        while True:
            try:
                r, w, e = select.select([server, ], [], [], 1)
                for server in r:
                    conn, addr = server.accept()
                    t = threading.Thread(target=self.process, args=(conn,))
                    t.start()
            except Exception as e:
                sys.exit(0)

    def process(self, conn):
        while True:
            req1 = conn.recv(1024).decode('utf-8')
            if req1:
                if " " in req1:
                    cmd1 = req1.split(' ')[0]
                    data = ' '.join(req1.split(' ')[1:])
                else:
                    cmd1 = req1
                if cmd1 == 'stop' and len(data) > 0:
                    print('Private coversation with %s has been stopped!' % data)
                    conn.send(('stop ' + self.name).encode('utf-8'))
                    self.privates.pop(data)
                    break
                elif cmd1 == 'iam':
                    self.privates[data] = conn
                    # print(data, self.privates[data])
                else:
                    print(req1)

    def run(self):
        while True:
            resp = self.sock.recv(1024).decode('utf-8')
            if resp == 'wrong username':
                print('Invalid username, try again!')
                self.name = input('Enter your username: ')
                pwd = input('Enter your password: ')
                req = 'login ' + self.name + '&' + pwd
                self.sock.send(req.encode('utf-8'))
            elif resp == 'wrong password':
                print('Invalid credentials, try again!')
                self.name = input('Enter your username: ')
                pwd = input('Enter your password: ')
                req = 'login ' + self.name + '&' + pwd
                self.sock.send(req.encode('utf-8'))
            elif resp == 'timeout':
                print('Timeout, log out!')
                break
            elif resp.split(' ')[0] == 'newer':
                print(resp.split(' ')[1] + ' has just logged in!')
            elif resp.split(' ')[0] == 'whoelse':
                print('Users that are currently online ', end=': ')
                users = resp.split(' ')[1].split('&')
                for i in range(len(users) - 1):
                    print(users[i], end=' ')
                print()
            elif resp.split(' ')[0] == 'message':
                sender = resp.split(' ')[1]
                msg = resp.split(' ')[2:]
                print(sender + ': ' + ' '.join(msg))
            elif resp.split(' ')[0] == 'broadcast':
                sender = resp.split(' ')[1]
                msg = resp.split(' ')[2:]
                print('Broadcast from ' + sender + ': ' + ' '.join(msg))
            elif resp.split(' ')[0] == 'whoelsesince':
                print('Users that logged in ', end=': ')
                users = resp.split(' ')[1].split('&')
                for i in range(len(users) - 1):
                    print(users[i], end=' ')
                print()
            elif resp.split(' ')[0] == 'block':
                blocker = resp.split(' ')[1]
                print(blocker + ' is blocked!')
            elif resp.split(' ')[0] == 'unblock':
                blocker = resp.split(' ')[1]
                print(blocker + ' is unblocked!')
            elif resp.split(' ')[0] == 'Invalidreceiver!':
                print('Invalid receiver!')
            elif resp.split(' ')[0] == 'Invalidblock!':
                print('Invalid user to block!')
            elif resp.split(' ')[0] == 'Invalidunblock!':
                print('Invalid user to unblock!')
            elif resp.split(' ')[0] == 'Blocked':
                receiver = resp.split(' ')[2]
                # print('You are blocked by ' + receiver + '!')
                print('Your message cannot be received because message receiver block you.')
            elif resp.split(' ')[0] == 'nbroadcast':
                # blocks = resp.split(' ')[1].split('&')
                print("Your broadcast cannot be received by all online users because someone blocked you")
                # for i in range(len(blocks)):
                #     print(blocks[i], end=' ')
                # print()
            elif resp.split(' ')[0] == 'nologin':
                print('You are not logged in!')
            elif resp.split(' ')[0] == 'Invalidprivate':
                print('Invalid user to start private conversation!')
            elif resp.split(' ')[0] == 'startprivate':
                privater = resp.split(' ')[1]
                addr = (resp.split(' ')[2], int(resp.split(' ')[3]))
                # print(addr)
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect(addr)

                t = threading.Thread(target=self.process, args=(sock, ))
                t.start()

                # print(privater)
                self.privates[privater] = sock
                sock.send(('iam ' + self.name).encode('utf-8'))
                print('Connected to ' + privater + ' ' + 'successfully!')
            elif resp.split(' ')[0] == 'history':
                sender = resp.split(' ')[1]
                msg1 = resp.split(' ')[2:]
                print(sender + '(history): ' + ' '.join(msg1))
            elif resp.split(' ')[0] == 'youlogout':
                print('You just logged out!')
            elif resp.split(' ')[0] == 'logout':
                username = resp.split(' ')[1]
                print(username + ' just logged out!')


if __name__ == '__main__':

    if len(sys.argv) == 3:
        ip = sys.argv[1]
        port = int(sys.argv[2])

        client = Client(ip, port)

        # prompting login
        client.name = input('Enter your username: ')
        pwd = input('Enter your password: ')
        req = 'login ' + client.name + '&' + pwd
        client.sock.send(req.encode('utf-8'))
        while True:
            resp = client.sock.recv(1024).decode('utf-8')
            if resp == 'online':
                print('Already online!')
                client.sock.close()
                client.server.close()
                sys.exit(0)
            elif resp == 'wrong username':
                print('Invalid username, try again!')
                client.name = input('Enter your username: ')
                pwd = input('Enter your password: ')
                req = 'login ' + client.name + '&' + pwd
                client.sock.send(req.encode('utf-8'))
            elif resp == 'wrong password':
                print('Invalid credentials, try again!')
                # client.name = input('Enter your username: ')
                pwd = input('Enter your password: ')
                req = 'login ' + client.name + '&' + pwd
                client.sock.send(req.encode('utf-8'))
            elif resp.split(' ')[0] == 'success':
                client.sock.send((client.name + '@success ' + client.ip + '&' + client.port).encode('utf-8'))
                print('Welcome to this message application')
                break
            elif resp == 'blocked':
                print('You are blocked to login, try again later!')
                client.sock.close()
                client.server.close()
                sys.exit(0)
                # client.name = input('Enter your username: ')
                # pwd = input('Enter your password: ')
                # req = 'login ' + client.name + '&' + pwd
                # client.sock.send(req.encode('utf-8'))

        client.start()
        while True:
            req = input(">>>")
            #  get command
            if " " in req:
                cmd = req.split(" ")[0]
            else:
                cmd = req
            if cmd == 'message':
                receipt = req.split(" ")[1]
                msg = req.split(" ")[2:]
                client.sock.send((client.name + '@message ' + receipt + '&' + ' '.join(msg)).encode('utf-8'))
            elif cmd == 'broadcast':
                msg = req.split(" ")[1:]
                client.sock.send((client.name + '@broadcast ' + ' '.join(msg)).encode('utf-8'))
            elif cmd == 'whoelse':
                client.sock.send((client.name + '@whoelse').encode('utf-8'))
            elif cmd == 'whoelsesince':
                period = req.split(' ')[1]
                client.sock.send((client.name + '@whoelsesince ' + period).encode('utf-8'))
            elif cmd == 'block':
                user = req.split(' ')[1]
                client.sock.send((client.name + '@block ' + user).encode('utf-8'))
            elif cmd == 'unblock':
                user = req.split(' ')[1]
                client.sock.send((client.name + '@unblock ' + user).encode('utf-8'))
            elif cmd == 'logout':
                client.sock.send((client.name + '@logout').encode('utf-8'))
            elif cmd == 'startprivate':
                user = req.split(' ')[1]
                client.sock.send((client.name + '@startprivate ' + user).encode('utf-8'))
            elif cmd == 'private':
                receipt = req.split(" ")[1]
                msg = req.split(" ")[2:]
                if receipt == client.name:
                    print('Invalid username!')
                elif receipt not in client.privates:
                    print("Have not built private connection with " + receipt)
                else:
                    # print('###')
                    try:
                        # print(receipt,client.privates[receipt])
                        client.privates[receipt].send((client.name + '(private): ' + (' '.join(msg))).encode('utf-8'))
                    except Exception as e:
                        print(receipt + ' is not online!')
            elif cmd == 'stopprivate':
                receipt = req.split(" ")[1]
                if receipt == client.name:
                    print('Invalid username!')
                elif receipt not in client.privates:
                    print("Have not built private connection with " + receipt)
                else:
                    try:
                        client.privates[receipt].send(('stop ' + client.name).encode('utf-8'))
                        # client.privates.pop(receipt)
                    except Exception as e:
                        print(receipt + ' is not online!')
            else:
                print('Invalid commands!')
