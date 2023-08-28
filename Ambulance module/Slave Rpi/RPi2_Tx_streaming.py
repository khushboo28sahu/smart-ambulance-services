# Stacked Rpi 2:
# For access: ssh pi@"IP"
# Go to path: cd Desktop/common \files
# To run: sudo python RPi2_Tx_streaming.py


import fcntl
import struct
import socket
import array
import scapy
import netifaces as ni
import sys
import re
import os
from Support_func_Rx import reverse_placeholder, NetworkCoding
from scapy.all import sniff
from scapy.all import *
from scapy.all import UDP
from scapy.all import Raw
from scapy.all import RTP
from scapy.all import IP
from scapy.all import send
import sys
import re
import os
import time
import threading

# import queue
# import Queue
import datetime

# import numpy as np
import math
import decimal
from decimal import Decimal
import random
from random import randint
import array

sock = {}

## Create a Packet Counter
counter = 0

# Destination address
# =======================
UDP_IP = "14.139.54.203"
# UDP_IP="127.0.0.1"
# UDP_IP="192.168.0.103"
UDP_PORT = {}
UDP_PORT_BASE = 5077
# UDP_PORT_BASE=9002 #8000
t = time.time()

sock = {}

Num_IF = 1  # number of interfaces attached
# pkt_queue = Queue.Queue()
# pkt_queue_failed = Queue.Queue()


# Function for automatic interface detection
# =================================================
def all_interfaces():
    global sock
    global Num_IF
    max_possible = 128  # arbitrary. raise if needed.
    a_bytes = max_possible * 32
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    names = array.array("B", chr("\0") * a_bytes)
    outbytes = struct.unpack(
        "iL",
        fcntl.ioctl(
            s.fileno(),
            0x8912,  # SIOCGIFCONF
            struct.pack("iL", a_bytes, names.buffer_info()[0]),
        ),
    )[0]
    namestr = names.tostring()
    lst = []
    for i in range(0, outbytes, 40):
        name = namestr[i : i + 16].split("\0", 1)[0]
        ip = namestr[i + 20 : i + 24]
        lst.append((name, ip))
    return lst


def format_ip(addr):
    return (
        str(ord(addr[0]))
        + "."
        + str(ord(addr[1]))
        + "."
        + str(ord(addr[2]))
        + "."
        + str(ord(addr[3]))
    )


# ifs = all_interfaces()
ifs = os.listdir("/sys/class/net")
print(ifs)
for i in ifs:
    # print ("%12s   %s" % (i[0], format_ip(i[1]))
    if i[:4] == "usb0" or i[:4] == "usb1":
        # if i[0][:2]=="en":
        print(
            str(Num_IF)
            + " <-- this must be to total number of interfaces including the redundant"
        )
        sock[Num_IF] = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock[Num_IF].setsockopt(socket.SOL_SOCKET, 25, i.encode())
        ip = ni.ifaddresses(i)[ni.AF_INET][0]["addr"]
        sock[Num_IF].bind((ip, UDP_PORT_BASE + Num_IF))
        # Num_IF=Num_IF+1
        # print (ip, Num_IF, "\n Socket----------\n", sock[Num_IF])
time.sleep(0.1)

print("Total interfaces on Rpi 2 = ", Num_IF)


## Define our Custom Action function
# =======================================
def custom_action(packet):
    global UDP_IP1, UDP_PORT1, counter, Num_IF, sock, UDP_IP, UDP_PORT, SN, UDP_PORT_BASE, pkt_queue, temp_offset
    if UDP in packet and Raw in packet and packet[UDP].dport == 30000:
        # if_num=bytes(packet[Raw])[:8]
        # print (if_num)
        # print ("=======================================")
        # print (bytes(packet))
        # print ("packet shape =============\n", type(packet), packet.load)
        packet[UDP].payload = NetworkCoding(packet[Raw].load)
        # packet[UDP].payload=NetworkCoding(packet[Raw].load)
        if_num = counter % Num_IF + 1
        # print (bytes(packet))
        # packet.show()
        UDP_IP1 = packet[IP].src
        UDP_PORT1 = packet[UDP].sport
        # print (bytes(packet[NetworkCoding]))
        # print (sock[if_num], UDP_IP, UDP_PORT_BASE+if_num )
        sock[if_num].sendto(
            bytes(packet[NetworkCoding]), (UDP_IP, UDP_PORT_BASE + if_num)
        )
        counter += 1
        if if_num == Num_IF:
            counter = 0
        else:
            pass
        # print "Packet sent on =", UDP_PORT_BASE+if_num, packet[RTP].sequence


def fb_sender(pakt):
    global UDP_IP1, UDP_PORT1
    fb_pkt = pakt[Raw].load.decode()
    # print ("feebback received",fb_pkt)
    s.sendto(bytes(fb_pkt, encoding="utf8"), (UDP_IP1, UDP_PORT1))


def fb_sniff():
    print("receive and send feedback")
    # sniff(filter="udp and portrange 9000-9002 and inbound", prn=fb_sender, iface='wlan0',  store=0)
    sniff(
        filter="udp and portrange 5077-5081 and inbound",
        prn=fb_sender,
        iface="usb0",
        store=0,
    )


optim_thread = threading.Thread(target=fb_sniff)
time.sleep(0.1)
optim_thread.start()


s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)


sniff(iface="eth0", filter="udp and port 30000 and inbound", prn=custom_action)

# For MP4: sudo ffmpeg -f v4l2 -i /dev/video0 -f rtp rtp://localhost:1234?pkt_size=500
# gst-launch-1.0 -v udpsrc port=1234 ! "application/x-rtp, media=(string)video, clock-rate=(int)90000, encoding-name=(string)MP4V-ES, profile-level-id=(string)1, config=(string)000001b001000001b58913000001000000012000c48d88007d0a041e1463000001b24c61766335322e3132332e30, payload=(int)96, ssrc=(uint)298758266, clock-base=(uint)3097828288, seqnum-base=(uint)63478" ! rtpmp4vdepay ! avdec_mpeg4 ! autovideosink
# sudo ffmpeg -re -i jellyfish-3-mbps-hd-h264.mkv -an -vcodec libx264 -b 500k -f rtp rtp://localhost:1234?pkt_size=500
# sudo ffmpeg -f v4l2 -i /dev/video0 -an -vcodec libx264 -f rtp rtp://localhost:1234
#  *. To kill python running tasks: sudo kill -9 $(ps aux | grep python | awk '{print $2}')

# To receive and playout:
# gst-launch-1.0 -v udpsrc port=1234 ! 'application/x-rtp, media=(string)video, clock-rate=(int)90000, encoding-name=(string)H264, sprop-parameter-sets=(string)"Z0JAKLtAZBy/gKJAAAADAEAAAA8YEAALcbAAtx73vheEQjU\=\,aM44gA\=\=", payload=(int)96, ssrc=(uint)3725838184, timestamp-offset=(uint)2716743768, seqnum-offset=(uint)769' ! rtpjitterbuffer ! rtph264depay ! avdec_h264 ! videoconvert ! videoconvert ! glimagesink
