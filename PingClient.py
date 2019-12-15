#COMP9331 Lab2: HTTP & Socket Programming
#Author: Junyu Ren
#Student ID: z5195715
#Date:2019-10-03
#Version:Python 3.7.2

from socket import *
import sys
import getopt
import time

ops, args = getopt.getopt(sys.argv[1:], "")
if len(args) > 2 or len(args) < 2:
    print("Incorrect input! Giving up...")
    sys.exit()

HOST = args[0]
PORT = int(args[1])
rttlist = []

clientSock = socket(AF_INET, SOCK_DGRAM)
clientSock.settimeout(1)

for seq in range(1, 11):
    try:
        start_time = time.time()
        message = 'PING'+' '+str(seq)+' '+str(start_time)+' \r\n'
        clientSock.sendto(str.encode(message), (HOST, PORT))
        receiced = clientSock.recv(4096)
        end_time = time.time()
        rtt = int(round(int((end_time-start_time)*1000)))
        rttlist.append(rtt)
        sumrtt=sum(rttlist)
        print("ping to {}, seq = {}, rtt = {} ms".format(HOST, seq, rtt))
    except timeout:
        print("ping to {}, seq = {}, time out".format(HOST, seq))
print("The minimum rtt: "+str(min(rttlist))+" ms"+"\n" +
      "The maximum rtt: "+str(max(rttlist))+" ms"+"\n" +
      "The average rtt: "+str(int(round(sumrtt/len(rttlist))))+" ms.")
