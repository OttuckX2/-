#!/usr/bin/python3
'''
$ tftp ip_address [-p port_number] <get|put> filename
'''

import os
import sys
import socket
import argparse
from struct import pack, unpack
from select import select

DEFAULT_PORT = 69
BLOCK_SIZE = 512
DEFAULT_TRANSFER_MODE = 'octet'
TIMEOUT = 5  # seconds

OPCODE = {'RRQ': 1, 'WRQ': 2, 'DATA': 3, 'ACK': 4, 'ERROR': 5}

ERROR_CODE = {
    0: "Not defined, see error message (if any).",
    1: "File not found.",
    2: "Access violation.",
    3: "Disk full or allocation exceeded.",
    4: "Illegal TFTP operation.",
    5: "Unknown transfer ID.",
    6: "File already exists.",
    7: "No such user."
}

def send_request(sock, server_address, opcode, filename, mode):
    request = pack(f'>h{len(filename)}sB{len(mode)}sB', opcode, filename.encode(), 0, mode.encode(), 0)
    sock.sendto(request, server_address)

def send_ack(sock, server, block_number):
    ack = pack('>hh', OPCODE['ACK'], block_number)
    sock.sendto(ack, server)

def receive_data(sock):
    try:
        data, server = sock.recvfrom(516)
        return data, server
    except socket.timeout:
        print("Timeout: No response from server")
        sys.exit(1)

def handle_error(data):
    error_code = unpack('>h', data[2:4])[0]
    print("Error:", ERROR_CODE.get(error_code, "Unknown error"))
    sys.exit(1)

def tftp_get(sock, server_address, filename):
    send_request(sock, server_address, OPCODE['RRQ'], filename, DEFAULT_TRANSFER_MODE)
    
    file = open(filename, 'wb')
    expected_block = 1

    while True:
        data, server = receive_data(sock)
        opcode = unpack('>h', data[:2])[0]
        
        if opcode == OPCODE['DATA']:
            block_number = unpack('>h', data[2:4])[0]
            if block_number == expected_block:
                file.write(data[4:])
                send_ack(sock, server, block_number)
                expected_block += 1
            if len(data[4:]) < BLOCK_SIZE:
                break
        elif opcode == OPCODE['ERROR']:
            handle_error(data)
    
    print("File transfer completed")
    file.close()

def tftp_put(sock, server_address, filename):
    send_request(sock, server_address, OPCODE['WRQ'], filename, DEFAULT_TRANSFER_MODE)

    try:
        file = open(filename, 'rb')
    except FileNotFoundError:
        print("File not found.")
        sys.exit(1)
    
    block_number = 0
    while True:
        block_number += 1
        data_block = file.read(BLOCK_SIZE)
        data_packet = pack(f'>hh{len(data_block)}s', OPCODE['DATA'], block_number, data_block)
        sock.sendto(data_packet, server_address)
        
        ready = select([sock], [], [], TIMEOUT)
        if ready[0]:
            ack, server = receive_data(sock)
            ack_opcode = unpack('>h', ack[:2])[0]
            ack_block_number = unpack('>h', ack[2:4])[0]

            if ack_opcode == OPCODE['ACK'] and ack_block_number == block_number:
                if len(data_block) < BLOCK_SIZE:
                    break
            elif ack_opcode == OPCODE['ERROR']:
                handle_error(ack)
                break
        else:
            print("Timeout: No ACK received")
            sys.exit(1)
    
    print("File transfer completed")
    file.close()

# Parse command line arguments
parser = argparse.ArgumentParser(description='TFTP client program')
parser.add_argument("host", help="Server IP address", type=str)
parser.add_argument("operation", help="get or put a file", type=str)
parser.add_argument("filename", help="Name of file to transfer", type=str)
parser.add_argument("-p", "--port", help="Server port number", type=int, default=DEFAULT_PORT)
args = parser.parse_args()

# Create UDP socket
server_address = (args.host, args.port)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(TIMEOUT)

if args.operation == "get":
    tftp_get(sock, server_address, args.filename)
elif args.operation == "put":
    tftp_put(sock, server_address, args.filename)
else:
    print("Invalid operation. Use 'get' or 'put'.")
    sys.exit(1)

sock.close()
sys.exit(0)
