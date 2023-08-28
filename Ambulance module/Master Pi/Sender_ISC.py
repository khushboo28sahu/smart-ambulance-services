# Sender side: Interstream coding and traffic adaptation
# ==========================================================
""" Importing all the neccessary packages"""
import fcntl
import struct
import array
import socket
import scapy
from scapy.all import *
import netifaces as ni
import sys
import re
import time
import threading
import datetime
import math
import decimal
from decimal import Decimal
import random
from random import randint
import queue
from extra_fns2 import add_nc, NetworkCoding
from extra_fns_sock_lis import UDP_listener
import numpy as np
import csv
import os
from openpyxl import Workbook
from builtins import bytes, chr
from sympy import *


UDP_IP = "14.139.54.203"
UDP_PORT = {}
UDP_PORT_BASE = 5078
UDP_PORT[0] = 5079
UDP_PORT[1] = 5080
UDP_PORT[2] = 5081
# Stacked Rpi2s IP address
UDP_IP_RpiEth = "169.254.219.242"
UDP_PORT_RpiEth = 30000

## Initialization
sock = {}
counter = 0
Num_IF = 0
first_feedback = 1
pkt_queue = queue.Queue()
pkt_queue_failed = queue.Queue()
epsilon = 0.1
count = 0
# ============= Interface detection function===============
# def all_interfaces():
# 	global sock
# 	global Num_IF
# 	max_possible = 128  # arbitrary. raise if needed.
# 	a_bytes = max_possible * 32
# 	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# 	names = array.array('B', chr('\0') * a_bytes)
# 	outbytes = struct.unpack('iL', fcntl.ioctl(
# 		s.fileno(),
# 		0x8912,  # SIOCGIFCONF
# 		struct.pack('iL', a_bytes, names.buffer_info()[0])
# 	))[0]
# 	namestr = names.tostring()
# 	lst = []
# 	for i in range(0, outbytes, 40):
# 		name = namestr[i:i+16].split('\0', 1)[0]
# 		ip   = namestr[i+20:i+24]
# 		lst.append((name, ip))
# 	return lst


# def format_ip(addr):
# 	return str(ord(addr[0])) + '.' + \
# 		   str(ord(addr[1])) + '.' + \
# 		   str(ord(addr[2])) + '.' + \
# 		   str(ord(addr[3]))
# =======================================================
"""==================================INTERFACE DETECTION=============================================
	Detect the total number of connected interfaces"""
ifs = os.listdir("/sys/class/net")

"""Rearranging 'lo' and 'eth0' in the list"""
for i in ifs:
    if i == "lo":
        tmp = i
        ifs.remove(i)
for i in ifs:
    if i == "eth0":
        tmp = i
        ifs.remove(i)
        ifs.append(tmp)
print(ifs)

"""Creating the socket with available 4 interfaces except 'lo' to connect\
the 3 interfaces with the server and one which is 'eth0' to the stacked Rpi\
with there respected ports."""
for i in ifs:
    if i[:2] == "et" or i[:2] == "wl" or i[:2] == "us":
        if i[:4] == "eth0":
            temp_eth = ifs.index(i)
            print(temp_eth, i[:4])
        sock[Num_IF] = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock[Num_IF].setsockopt(socket.SOL_SOCKET, 25, i.encode())
        ip = ni.ifaddresses(i)[ni.AF_INET][0]["addr"]
        sock[Num_IF].bind((ip, UDP_PORT_BASE + Num_IF))
        Num_IF = Num_IF + 1

print("Total number of interfaces:", Num_IF)
time.sleep(0.1)
"""The Redundant interfaces is for the stacked Rpis interface, like in this\
case stacked Rpi has 1 intefaces to communicate with Server.(Need more clarification)"""
curr_redundancy = 1
# curr_redundancy = int(input("Redundancy Interface:"))  #set 1 for total 3 interfaces

""""========================================CUSTOM ACTION================================
	Custom action is sniffing the RTP packets from the local port and accumulating those
	packets into a queue. This queue will store the packets sequentially and will be used
	to send these packets to the server.
"""


def custom_action(packet):
    global counter, Num_IF, sock, UDP_PORT, UDP_IP, UDP_PORT_BASE, pkt_queue

    """Sniffed packets from local port '1234' is being checked for the UDP with RTP packets.
		The	timestamp is given for the RTP packets. These packets are stored in pkt_queue.
	"""

    if UDP in packet:
        if packet[UDP].dport == 1234:
            packet[UDP].payload = RTP(packet[Raw].load)
            packet[RTP].timestamp = int(1000000 * Decimal(packet.time)) % 100000000
            # packet[RTP].timestamp=int(1000*Decimal(time.time()))%10000		# Time is in Miliseconds or 10^3
            # WARNINIG: Didn't remove the part till UDP layer. Expecting add_nc to do that
            pkt_queue.put(packet)


"""==========================================PACKET SENDER================================
	Taking packets from the Queue for all the avialble interfaces and sending it for the
	networkcoding. It will generate a redundant packet for the a redundant interface and 
	stack it along will these packets. all these packets will be selected randomly and 
	sent it to the server.
"""


def pkt_sender():
    global counter, Num_IF, sock, UDP_PORT, UDP_IP, UDP_PORT_BASE, pkt_queue, curr_redundancy, prob
    indicator = 0

    """Initial probability for each interface will be (1/Total number of interfaces.)
	"""
    prob = np.array([1 / Num_IF for i in range(Num_IF)], dtype=float)

    print("initial_probability", prob, "\n", "No. of interfaces", Num_IF)

    while 1:
        redundant_if = curr_redundancy
        """	Checking the Queue if it has the minimum no packets to send through the available sockets \
			in master Rpi to the server. These packets are sent to the interstream coding part where the \
			UDP header will be removed and Networkcoding header will be added on each packets. For the \
			redundant interface, the matrix multiplication with these packets and made a single packet \
			for it(in linear encode function).
		"""
        if pkt_queue.qsize() >= Num_IF - redundant_if:
            # No of unique packets available for the server from the available interfaces.
            list_pkt_to_send = [pkt_queue.get() for i in range(Num_IF - redundant_if)]

            # These packets are sent to the add_nc function for ISC will return along with
            # 1(interface at Rpi2) packet for the redundant interface.
            list_pkt_to_send = add_nc(list_pkt_to_send, redundant_if)

            if_num = 0

            for pkt_to_send in list_pkt_to_send:
                # Select randomly any interfaces among the available 4 interfaces.
                ifs_select = np.random.choice([i for i in range(Num_IF)], 1, p=prob)

                # set this field in the networkcoding packets header.ifs_select[0] will be the port number,
                pkt_to_send[NetworkCoding].interface = ifs_select[0]
                pkt_to_send[NetworkCoding].redundancy = redundant_if
                pkt_to_send[NetworkCoding].timestamp = (
                    int(1000000 * Decimal(time.time())) % 100000000
                )  # Time in miliseconds or 10^-3 seconds.
                # pkt_to_send[NetworkCoding].timestamp = int(1000*Decimal(time.time()))%10000  # Time in miliseconds or 10^-3 seconds.
                time.sleep(0.008)

                # Sending packets to the satcked Rpi(slave Rpi)
                if ifs_select[0] == (temp_eth):
                    indicator = sock[ifs_select[0]].sendto(
                        bytes(pkt_to_send), (UDP_IP_RpiEth, UDP_PORT_RpiEth)
                    )
                else:
                    # Sending packets to the server from the available interfaces.
                    # print(UDP_IP, UDP_PORT[ifs_select[0]])
                    indicator = sock[ifs_select[0]].sendto(
                        bytes(pkt_to_send), (UDP_IP, UDP_PORT[ifs_select[0]])
                    )

                if_num += 1
                # if the socket fails to send packet, then put it back to the queue.
                if indicator == 0:
                    print("FAILED SENDING A PACKET!")
                    pkt_queue_failed.put(pkt_to_send)

        time.sleep(0.001)


def softmax(x):
    """Compute softmax values for each sets of scores in x."""
    # return np.exp(x) / np.sum(np.exp(x), axis=0)
    return x / np.sum(x)


"""=========================PROBABILITY OPTIMIZER=======================================
	It is receiving the feedback packets from the server.
"""


def prob_optimizer(pakt):
    global previous_jitter, curr_redundancy, prob, epsilon, first_feedback, prev_redundancy, previous_jitter, count
    # pakt.show()
    print("======================Feedback Received===========================\n")
    feedback = list(map(str, pakt[Raw].load.decode().split("@")))  # int
    print("Average Jitter feedback received\n", pakt[Raw].load.decode(), "\n")
    # print("feedback\n", int(feedback[1]), int(feedback[2]), int(feedback[3]),int(feedback[4]))
    feed = [
        int(feedback[0]),
        int(feedback[1]),
        int(feedback[2]),
        int(feedback[3]),
        int(feedback[4]),
    ]
    with open("Av_Jitter_time_100kbs.csv", "a") as jitter_write:
        writer = csv.writer(jitter_write)
        # writer.writerow([1/float(feedback[1]), 1/float(feedback[2]), 1/float(feedback[3]),1/float(feedback[4]), feedback[5]])
        writer.writerow(
            [
                int(feedback[1]),
                int(feedback[2]),
                int(feedback[3]),
                int(feedback[4]),
                feedback[5],
            ]
        )

    score = np.array(feed, dtype=np.float64)
    # print("Probabilities\t",score,"\n")
    if score[0] == 0:
        # prob = (score / np.sum((score), axis=0))
        score = score[1:]
        # print(score, type(score))
        recommended_probability = softmax(score)
        prob = prob + (epsilon) * (recommended_probability - prob)
        # ws.append([str(prob[0]), str(prob[1]), str(prob[2]), str(prob[3])])
        with open("All_probability_100kbps.csv", "a") as f:
            writer = csv.writer(f)
            writer.writerow(prob)
        print("updated_probability\n", prob, "\n")
    else:
        current_jitter = score[1] / 1000
        with open("oai_r500kb_jttr_100kbps.csv", "a") as f:
            writer = csv.writer(f)
            writer.writerow([curr_redundancy, current_jitter])

        if first_feedback:
            first_feedback = 0
            prev_redundancy = curr_redundancy
            # previous_jitter = current_jitter
            curr_redundancy += 1
        elif (
            current_jitter > previous_jitter + 3
            and prev_redundancy > curr_redundancy
            and curr_redundancy < Num_IF - 1
        ):
            prev_redundancy = curr_redundancy
            # previous_jitter = current_jitter
            curr_redundancy += 1
        elif (
            current_jitter > previous_jitter + 3
            and prev_redundancy < curr_redundancy
            and curr_redundancy > 1
        ):
            prev_redundancy = curr_redundancy
            # previous_jitter = current_jitter
            curr_redundancy -= 1
        elif (
            current_jitter < previous_jitter - 3
            and prev_redundancy > curr_redundancy
            and curr_redundancy > 1
        ):
            prev_redundancy = curr_redundancy
            # previous_jitter = current_jitter
            curr_redundancy -= 1
        elif (
            current_jitter < previous_jitter - 3
            and prev_redundancy < curr_redundancy
            and curr_redundancy < Num_IF - 1
        ):
            prev_redundancy = curr_redundancy
            # previous_jitter = current_jitter
            curr_redundancy += 1
        previous_jitter = current_jitter

        with open("m4t5.csv", "a") as f:
            writer = csv.writer(f)
            writer.writerow([time.time(), curr_redundancy, Num_IF - curr_redundancy])
        print("updated_redundancy", curr_redundancy)


def fb_sniff():
    print("...................feedback sniffing started............................")
    sniff(filter="udp and portrange 5078-5080 and inbound", prn=prob_optimizer, store=0)


"""This two threads are running simultaneously with the sleeping time of 0.1 seconds.
	The packets which are coming as a feedback are being sniffed and the packets are
	being sent to the server."""
threadread = threading.Thread(target=pkt_sender)
time.sleep(0.1)
threadread.start()

optim_thread = threading.Thread(target=fb_sniff)
time.sleep(0.1)
optim_thread.start()

"""Setup sniff, filtering for IP traffic
   Sniffing RTP packets from the local interface.
"""
sniff(
    filter="udp and port 1234 and inbound",
    prn=custom_action,
    iface="lo",
    store=0,
    count=350000,
)
# sniff(offline="Sniffed_V3.pcap", prn=custom_action, store = 0)
# sniff(offline="RTP_pkts640x480.pcap", prn=custom_action, store = 0)

# print ("Over !")
# wb.save("sender_log3.xlsx")

# def UDP_listener(ip,port,prn):
# 	# Create a TCP/IP socket
# 	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# 	# Bind the socket to the port
# 	server_address = (str(ip),port)
# 	print('starting up on %s port %s' % server_address)
# 	sock.bind(server_address)

# 	while True:
# 		data, address = sock.recvfrom(4096)
# 		pkt_out=IP(src=address[0],dst=ip)/UDP(sport=address[1],dport=port)/data
# 		prn(pkt_out)

# # def pkt_shower(p): #example usage
# # 	p.show()

# with open('m4t5.csv','a') as f:
# 	writer = csv.writer(f)
# 	writer.writerow([time.time(),curr_redundancy,Num_IF-curr_redundancy])

# UDP_listener("127.0.0.1",1234,custom_action)
port_range = range(1234, 1235)
UDP_listener(["0.0.0.0"] * len(port_range), port_range, custom_action, islist=1)
