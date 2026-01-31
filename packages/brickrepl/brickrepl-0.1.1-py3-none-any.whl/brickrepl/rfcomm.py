# EV3-compatible RFCOMM connection
from usocket import socket, AF_BLUETOOTH, SOCK_STREAM, BTPROTO_RFCOMM
from uctypes import addressof, sizeof, struct as cstruct
from uctypes import struct as cstruct
from uctypes import addressof
from uctypes import sizeof
from uctypes import struct as cstruct

# Minimal sockaddr_rc for EV3
sockaddr_rc = {
    "rc_family": 0 | 0 << 0,        # 16-bit
    "rc_bdaddr": 2 | 0 << 0,        # 6 bytes
    "rc_channel": 8 | 0 << 0        # uint8
}

def str2ba(addr_str, ba):
    # Convert MAC string to byte array
    for i, x in enumerate(addr_str.split(":")):
        ba[i] = int(x, 16)
    return ba

def connect_rfcomm(mac, channel=1):
    import uctypes
    addr_data = bytearray(10)  # EV3 sockaddr_rc size
    addr = cstruct(addressof(addr_data), sockaddr_rc)
    addr.rc_family = AF_BLUETOOTH
    str2ba(mac, addr.rc_bdaddr)
    addr.rc_channel = channel
    sock = socket(AF_BLUETOOTH, SOCK_STREAM, BTPROTO_RFCOMM)
    sock.connect(addr_data)
    return sock
