from scapy.all import *
from scapy.packet import Packet, bind_layers
from scapy.fields import (
    BitEnumField,
    BitField,
    BitFieldLenField,
    FieldLenField,
    FieldListField,
    IntField,
    ShortField,
)
import numpy as np
from decimal import Decimal
from sympy import *


def linear_encode(list_of_packet, redundant_if):
    # print(Raw(list_of_packet[0][NetworkCoding].payload))
    # global redundant_if
    pkt_pload = []
    for pkt in list_of_packet:
        pkt_pload.append(bytes((pkt[NetworkCoding].payload)))
    # a=bytes(Raw(list_of_packet[0][NetworkCoding].payload))
    # b=bytes(Raw(list_of_packet[1][NetworkCoding].payload))
    # c=bytes(Raw(list_of_packet[2][NetworkCoding].payload))
    # print(pkt[Raw].load[:100])
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
    int_pkt_pload = []
    for pkt in pkt_pload:
        int_pkt_pload.append(int.from_bytes(pkt, byteorder="big"))

    # int_a=int.from_bytes(a,byteorder='big')
    # int_b=int.from_bytes(b,byteorder='big')
    # int_c=int.from_bytes(c,byteorder='big')
    # temp = [pkt for pkt in int_pkt_pload]
    # print(matrix[10:10+redundant_if,:redundant_if].shape)
    temp_mat = Matrix(matrix[10 : 10 + redundant_if, : len(int_pkt_pload)]) * Matrix(
        int_pkt_pload
    )
    int_r_pkt = []

    for i in temp_mat:
        # print("redundant packet generated")
        int_r_pkt.append(np.int(i))

    # int_d = np.dot(matrix[3],temp)
    # int_e = np.dot(matrix[4],temp)
    r_pkt = []
    for pkt in int_r_pkt:
        # print("$$$$$$$$$$$$$$",pkt)
        r_pkt.append(pkt.to_bytes(sys.getsizeof(pkt), byteorder="big"))
    # d = int_d.to_bytes(sys.getsizeof(int_d),byteorder='big')
    # e = int_e.to_bytes(sys.getsizeof(int_e),byteorder='big')

    return r_pkt


def load_xor(a, b):
    c = []
    if len(a) > len(b):
        big_pkt = a
    else:
        big_pkt = b

    for i in range(0, min(len(a), len(b))):
        c.append(chr(ord(a[i]) ^ ord(b[i])))

    for i in range(min(len(a), len(b)), max(len(a), len(b))):
        c.append(big_pkt[i])

    return raw("".join(c))


class NetworkCoding(Packet):
    name = "NetworkCoding "
    fields_desc = [
        ShortField("segment", None),
        ShortField("len_pkt0", 0),
        ShortField("len_pkt1", 0),
        ShortField("len_pkt2", 0),
        ShortField("len_pkt3", 0),
        ShortField("len_pkt4", 0),
        ShortField("len_pkt5", 0),
        ShortField("len_pkt6", 0),
        ShortField("len_pkt7", 0),
        # FieldListField('len_pkt', [],[]),
        ShortField("timestamp", 0),
        ShortField("redundancy", 0),
        ShortField("interface", 0),
        ShortField("nc_pkt_num", -1),
    ]


def reverse_placeholder(i, nc_dict, min_pointer, key):
    if i == 0:
        return nc_dict[min_pointer][key][NetworkCoding].len_pkt0
    if i == 1:
        return nc_dict[min_pointer][key][NetworkCoding].len_pkt1
    if i == 2:
        return nc_dict[min_pointer][key][NetworkCoding].len_pkt2
    if i == 3:
        return nc_dict[min_pointer][key][NetworkCoding].len_pkt3
    if i == 4:
        return nc_dict[min_pointer][key][NetworkCoding].len_pkt4
    if i == 5:
        return nc_dict[min_pointer][key][NetworkCoding].len_pkt5
    if i == 6:
        return nc_dict[min_pointer][key][NetworkCoding].len_pkt6
    if i == 7:
        return nc_dict[min_pointer][key][NetworkCoding].len_pkt7


def placeholder(i, val, nc):
    if i == 0:
        nc.len_pkt0 = val
    elif i == 1:
        nc.len_pkt1 = val
    elif i == 2:
        nc.len_pkt2 = val
    elif i == 3:
        nc.len_pkt3 = val
    elif i == 4:
        nc.len_pkt4 = val
    elif i == 5:
        nc.len_pkt5 = val
    elif i == 6:
        nc.len_pkt6 = val
    elif i == 7:
        nc.len_pkt7 = val


def add_nc(list_of_packet, redundant_if):
    # this function will automatically extract only RTP part and add nc layer to them
    nc = NetworkCoding()

    nc.segment = list_of_packet[0][RTP].sequence  # using only seq part of RTP

    # loop for updating list of len(size) of original packets
    for i in range(len(list_of_packet)):
        placeholder(i, len(list_of_packet[i][UDP].payload), nc)

    # making list of output packtes with NC layer
    out_list_of_packets = []
    # length_list = []
    for pkt in list_of_packet:
        nc.nc_pkt_num += 1
        # length_list.append(len(pkt[UDP].payload))
        # nc.len_pkt.append(len(pkt[UDP].payload))
        # print(pkt.summary())
        out_list_of_packets.append(nc / pkt[RTP])

    # placeholder for the redundant packet 1
    parity_packet = []
    if redundant_if > 0:
        parity_list = linear_encode(
            out_list_of_packets[: len(list_of_packet)], redundant_if
        )
    nc.nc_pkt_num = 10
    for i in range(redundant_if):
        # nc.len_pkt = sys.getsizeof(parity_list[i])
        # pkt[RTP].timestamp=int(100*Decimal(time.time()))%10000
        parity_packet.append(nc / pkt[RTP])
        parity_packet[i][NetworkCoding].payload = parity_list[i]
        # print(parity_packet[i].summary())
        nc.nc_pkt_num += 1

    # print(len(parity_list),"^^^^^^^^^^^^^^^^^^^^^^^")

    # for i in range(len(parity_list)):
    # 	parity_packet[i][NetworkCoding].payload = (parity_list[i])

    # 	print("size of RTP payload",sys.getsizeof(parity_packet[i][NetworkCoding].payload))
    # parity_packet[i][RTP].timestamp=int(100*Decimal(time.time()))%10000

    for pkt in parity_packet:
        out_list_of_packets.append(pkt)

    return out_list_of_packets
