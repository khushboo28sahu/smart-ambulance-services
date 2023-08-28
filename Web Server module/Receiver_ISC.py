# Receiver side: Interstreaming coding and adaptive traffic splitting
# ========================================================================


# importing
from scapy.all import *
from scapy.all import RTP, UDP, IP

# from scapy import *
# from scapy import RTP, UDP, IP
import time
from Support_func_Rx import reverse_placeholder, NetworkCoding
import threading
import socket
import queue
import numpy as np
from fractions import Fraction

global seg_point
from decimal import *

# from extra_fns_sock_lis import UDP_listener
from sympy import *
from IPython.display import display
import numpy as np

#################
# import warnings
# from cryptography.utils import CryptographyDeprecationWarning
# warnings.filterwarnings("ignore", category=CryptographyDeprecationWarning)
#################

UDP_IP1 = "10.3.53.16"
UDP_PORT_BASE = 5078


# seg_point=0
first_packet = 1
first_ten = 0
nc_dict = {}
# exist={}
matrix = np.array(
    [
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 1, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 1, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 1, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 1, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 1, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 1, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 1, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [2, 3, 5, 7, 11, 13, 17, 19, 23, 31],
        [37, 41, 43, 47, 53, 59, 61, 67, 71, 73],
        [79, 83, 89, 97, 101, 103, 107, 109, 113, 127],
        [131, 137, 139, 149, 151, 157, 163, 167, 173, 179],
        [181, 191, 193, 197, 199, 211, 223, 227, 229, 233],
        [239, 241, 251, 257, 263, 269, 271, 277, 281, 283],
        [293, 307, 311, 313, 317, 331, 337, 347, 349, 353],
        [359, 367, 373, 379, 383, 389, 397, 401, 409, 419],
        [421, 431, 433, 439, 443, 449, 457, 461, 463, 467],
    ]
)

# Num_IF = int(input("Enter number of interfaces:"))
Num_IF = 4
print("Num of interfaces:", Num_IF)
# redundant_if = 1

q = queue.Queue()
prev_delay = [0 for i in range(Num_IF)]
jitter_avg = [0 for i in range(Num_IF)]
avg_count = [0 for i in range(Num_IF)]
prev_segment_delay = 0
overall_jitter = 0
jitter_count = 0

# Feedback function
# =======================


def feed_back():
    global jitter_avg, avg_count, UDP_IP, UDP_PORT, jitter_count, UDP_PORT
    while 1:
        # print("sssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssss",avg_count[0])
        if np.any(np.array(avg_count) >= 100):
            # print ("=======================Feedback Sent=========================")
            # print("count of packets",avg_count)
            # print("total_jitter",jitter_avg)
            for i in range(Num_IF):
                if avg_count[i] == 0:
                    jitter_avg[i] = 0
                else:
                    jitter_avg[i] = avg_count[i] * 100000 / jitter_avg[i]
                # jitter_avg[i] = (avg_count[i]/jitter_avg[i])
            # print("inverse average jitter",jitter_avg)
            # print("jitter_avg",avg_count,jitter_avg)
            data_send = "0@"
            for i in range(Num_IF):
                data_send += str(int(jitter_avg[i])) + "@"

            data_send = str(data_send[:-1])
            display(
                "Probability data -- ",
                str(data_send),
                "\tfeed_back IP --  ",
                UDP_IP,
                "\tfeed_back port -- ",
                UDP_PORT,
            )
            for i in range(Num_IF):
                indicator = s1[i].sendto(
                    bytes(data_send, encoding="utf8"), (UDP_IP, UDP_PORT)
                )
            if not indicator:
                print("Failed")

            jitter_avg = [0 for i in range(Num_IF)]
            avg_count = [0 for i in range(Num_IF)]
            prev_delay = [0 for i in range(Num_IF)]
            # print("jitter_count",jitter_count)

        # if jitter_count>=500:
        # 	avg_overall_jitter = overall_jitter/jitter_count
        # 	data_send = '1@'+str(int(avg_overall_jitter))
        # 	s1.sendto(bytes(data_send,encoding='utf8'), (UDP_IP, UDP_PORT))
        # 	print("sent feedback for jitter update")
        # 	jitter_count = 0
        if jitter_count >= 500:
            # print("Jitter count ----------\t", jitter_count)
            avg_overall_jitter = overall_jitter  # /jitter_count
            data_send = "1@" + str(int(avg_overall_jitter * 1000))

            """ Changes by KS"""
            display(
                "Average Jitter Data -- ",
                str(data_send),
                "\tfeed_back IP --  ",
                UDP_IP,
                "\tfeed_back port -- ",
                UDP_PORT,
            )
            for i in range(Num_IF):
                indicator = s1[i].sendto(
                    bytes(data_send, encoding="utf8"), (UDP_IP, UDP_PORT)
                )
            if not indicator:
                print("Failed")
            # s1.sendto(bytes(data_send,encoding='utf8'),("10.1.11.149",5085))
            # s1.sendto(bytes(data_send,encoding='utf8'),(UDP_IP, UDP_PORT))
            print("##sent feedback for jitter update", data_send, redundant_if)  # megha

            # with open('r1mb_jttr.csv',"a") as f:
            # 	writer = csv.writer(f)
            # 	writer.writerow([redundant_if,avg_overall_jitter])
            # file_counter+=1
            # if(file_counter>=100):
            # 	print(counter)
            jitter_count = 0
        time.sleep(0.001)


def cal_sum(cur_delay, pkt_num):
    # if pkt_num==2:
    # print("delay",cur_delay,pkt_num)
    # global prev_delay
    # print("packet number------\n", pkt_num, "\nCurrent delay----\n",np.int(cur_delay))
    # print(prev_delay)
    if prev_delay[pkt_num] == 0:
        prev_delay[pkt_num] = cur_delay
    else:
        jitter_avg[pkt_num] += abs(cur_delay - prev_delay[pkt_num])


def cal_overall_jitter(cur_segment_delay):
    global prev_segment_delay, overall_jitter, jitter_count
    if prev_segment_delay == 0:
        prev_segment_delay = cur_segment_delay
    else:
        # print("jitter update")
        # overall_jitter += abs(cur_segment_delay - prev_segment_delay)
        overall_jitter = 0.999 * overall_jitter + 0.001 * abs(
            cur_segment_delay - prev_segment_delay
        )
        prev_segment_delay = cur_segment_delay
        jitter_count += 1


# funtion to create dictionary of packets with keys as segment number for further playout
# ===========================================================================================
def dict_append():
    global seg_point, first_packet, nc_dict, jitter_avg, avg_count, UDP_IP, UDP_PORT, redundant_if
    p = q.get()

    # checking for port num and udp packet
    if UDP in p and Raw in p and p[UDP].dport <= 5084 and p[UDP].dport >= 5078:
        p[UDP].payload = NetworkCoding(p[Raw].load)
        # print(p[NetworkCoding])
        # initializing seg_point
        if first_packet:
            seg_point = p[NetworkCoding].segment - 2
            # s1.bind(('', p[UDP].dport))
            # print(p[UDP].dport,p[UDP].sport)
            first_packet = 0
        # if segment is already flushed return
        redundant_if = p[NetworkCoding].redundancy
        # print("packet number\n",p[NetworkCoding].nc_pkt_num,p[NetworkCoding].interface)

        UDP_IP = p[IP].src
        # print (p[UDP].dport)
        UDP_PORT = p[UDP].sport

        # print("time compare",time.time(),int(100*Decimal(time.time()))%10000,p[NetworkCoding].timestamp)
        # print("\n network Coding---------------\n",  p[NetworkCoding].interface, type( p[NetworkCoding].interface))
        cal_sum(
            abs(int(100 * Decimal(time.time())) % 10000 - p[NetworkCoding].timestamp),
            p[NetworkCoding].interface,
        )
        avg_count[p[NetworkCoding].interface] += 1

        if p[NetworkCoding].segment <= seg_point:
            return
        else:
            pkt_index = p[NetworkCoding].nc_pkt_num
            ifs_num = p[NetworkCoding].interface
            # creating the segment in else and storing the packet in segment dictionary
            if pkt_index < 10:
                p[NetworkCoding].payload = RTP(p[Raw].load)
            if p[NetworkCoding].segment in nc_dict.keys():
                nc_dict[p[NetworkCoding].segment][pkt_index] = p
                # exist[p[NetworkCoding].segment][ifs_num] = True
                # exist[min(exist.keys())][ifs_num] = True
            else:
                nc_dict[p[NetworkCoding].segment] = {}
                nc_dict[p[NetworkCoding].segment][pkt_index] = p
                # exist[p[NetworkCoding].segment] = dict.fromkeys(list(range(Num_IF)),False)
                # exist[p[NetworkCoding].segment][ifs_num] = True
                # exist[min(exist.keys())][ifs_num] = True

        # if required packets have arrived send them for playout
        if len(nc_dict[min(nc_dict.keys())]) >= Num_IF - redundant_if:
            ntwrk_dc()

        """while (len(exist.keys())!=0 and np.all(np.array(list(exist[min(exist.keys())].values()))==True)):
			keys = nc_dict[min(nc_dict.keys())].keys()
			for key in keys:
				if key<10:
					pkt = nc_dict[min(nc_dict.keys())][key][NetworkCoding].payload
					s.sendto(bytes(pkt),("127.0.0.1",4567))  # changed IP
					cal_overall_jitter(abs(int(100*Decimal(time.time()))%10000-nc_dict[min(nc_dict.keys())][key][NetworkCoding].timestamp))
		
			seg_point=nc_dict[min(nc_dict.keys())][min(nc_dict[min(nc_dict.keys())].keys())][NetworkCoding].segment
			del(nc_dict[min(nc_dict.keys())])
			del(exist[min(exist.keys())])"""
        # if packets are lost delete the incomplete segment
        if len(nc_dict.keys()) > 0 and max(nc_dict.keys()) - 10 >= seg_point:
            keys = nc_dict[min(nc_dict.keys())].keys()
            # print(len(keys),"size of dictionary before miniflush")
            for key in keys:
                if key < 10:
                    pkt = nc_dict[min(nc_dict.keys())][key][NetworkCoding].payload

                    s.sendto(bytes(pkt), ("127.0.0.1", 4567))  # changed IP
                    cal_overall_jitter(
                        abs(
                            int(100 * Decimal(time.time())) % 10000
                            - nc_dict[min(nc_dict.keys())][key][NetworkCoding].timestamp
                        )
                    )
            # print("mini_flush",min(nc_dict.keys()),redundant_if)
            seg_point = nc_dict[min(nc_dict.keys())][
                min(nc_dict[min(nc_dict.keys())].keys())
            ][NetworkCoding].segment
            del nc_dict[min(nc_dict.keys())]
            # del(exist[min(exist.keys())])


# function for decoding the packets and sending them to playout
# ================================================================
def ntwrk_dc():
    # segment to playout
    min_pointer = min(nc_dict.keys())

    keys = list(nc_dict[min_pointer].keys())
    keys = keys[: Num_IF - redundant_if]
    length_list = []
    for i in range(Num_IF - redundant_if):
        length_list.append(reverse_placeholder(i, nc_dict, min_pointer, keys[0]))
    # print("length of packet received",length_list)
    for key in keys:
        # nc_dict[min_pointer][key].show()
        cal_overall_jitter(
            abs(
                int(100 * Decimal(time.time())) % 10000
                - nc_dict[min_pointer][key][NetworkCoding].timestamp
            )
        )
        # break

    # storing Raw load of packet in enco_pkt
    enco_pkt = []
    for i in range(Num_IF - redundant_if):
        enco_pkt.append(nc_dict[min_pointer][keys[i]][NetworkCoding].payload)

    # converting bytes to string and storing in int_enco_pkt
    int_enco_pkt = []
    for pkt in enco_pkt:
        int_enco_pkt.append(int.from_bytes(pkt, byteorder="big"))
    # print(matrix[keys,0:len(int_enco_pkt)].shape,"*********************")

    # calculating inverse of matrix
    # print(matrix[keys,0:len(int_enco_pkt)])
    mat_inv = Matrix(matrix[keys, 0 : len(int_enco_pkt)]) ** -1
    # mat_inv = np.linalg.inv(matrix[keys,0:len(int_enco_pkt)])
    # print("inverse of matrix",mat_inv)

    # #decoding using X = A^(-1) * B (A inverse B)

    # decoding a inverse b
    output = mat_inv * Matrix(int_enco_pkt)
    # #changing the decoded "int" into bytes
    deco_pkt = []

    for i in range(len(output)):
        deco_pkt.append(
            RTP(np.int(output[i]).to_bytes(length_list[i], byteorder="big"))
        )

    # sending packet for playout
    for pkt in deco_pkt:
        # pkt.show()
        s.sendto(bytes(pkt), ("127.0.0.1", 4567))

    # updating seg_point
    global seg_point
    seg_point = nc_dict[min_pointer][min(nc_dict[min_pointer].keys())][
        NetworkCoding
    ].segment

    # deleting the segment
    # print("length of flushed segment",len(nc_dict[min_pointer]))
    del nc_dict[min_pointer]
    # del(exist[min(exist.keys())])
    # del exist[min_pointer]
    # print("Flushed" + str(min_pointer))


# function to put elements in the queue
# ===========================================
def queue_push(p):
    # print("Inside queue push function.")
    q.put(p)
    global first_ten
    if q.qsize() == 10 and first_ten == 0:
        print("starting!!")
        t1.start()
        first_ten = 1


"""function (int thread "t1") to check for existing 
packets in queue and calling for "dict_append" function"""


# ==============================================================
def pkt_flusher():
    while 1:
        if q.qsize() > 0:
            dict_append()


# t1 thread for storing packets in dictionary for playout
t1 = threading.Thread(target=pkt_flusher)
time.sleep(0.1)

t2 = threading.Thread(target=feed_back)
time.sleep(0.1)
t2.start()

# creating socket
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# s1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# s1.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)
# #s1.bind(('', 5079))

# creating socket
s1 = {}
for i in range(6):
    s1[i] = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s1[i].setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    print((UDP_IP1, UDP_PORT_BASE + i))
    s1[i].bind((UDP_IP1, UDP_PORT_BASE + i))

# #sniff packets from sender
print("Sniffing the packets from all the ports")
# sniff(prn=queue_push, filter = "udp and portrange 9000-9004 and inbound", store=0)
sniff(prn=queue_push, filter="udp and portrange 5078-5082 and inbound", store=0)

# port_range=range(5078,5082)
# UDP_listener(["0.0.0.0"]*len(port_range),port_range,queue_push,islist=1)
