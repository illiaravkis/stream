#!/usr/bin/env python

# Connect to BHR via WiFi
# Derived from Rasberry Pi Uart version with 512 sample traces, so we don't have to support different trace lengths in firmware
# Wait for streaming data and plot or stream to file
# Streamed trace format:
# Byte 0     Start Byte 0xAA
# Byte 1:2   Trace count, unsigned int
# Byte 3     Checksum bytes 0:2
# Byte 4:1027 Data: 512 samples x 16 bit signed
# Byte 1028   End Byte  0xC0
# note: currently only Python 2.7

import socket
import time
import numpy as np
import struct

# Settings for the WiFi connection
TCP_IP = '192.168.1.11'
TCP_PORT = 1024
BUFFER_SIZE = 4096
PLOT_ENABLE = False 

# Settings for the data format
# Settings for new 'Wifi' format
NUMTRACES = 256
NUMTOPLOT = 512
TRACELEN = 512
# originally there was a 92 byte header, but now we only use 4 bytes
# STARTBYTE TRACENO_HI TRACENO_LO CHECKSUM DATABYTES ENDBYTE
BYTESINHEADER = 5 # includes endbyte
BYTESINTRACE  = 2 * TRACELEN

# Settings for new 'Wifi' format
STARTBYTE = 0xAA
ENDBYTE = 0xC0

# Settings for the data file
FILENAME = "radar_wifi"
FILEHDR = "#radar v02#"


data = []
datanum = []
tracecount = 0
traceval2d = [[0]*TRACELEN]*NUMTOPLOT
freq_axis = [x*500.0/128.0 for x in range(128)]
#print freq_axis

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((TCP_IP, TCP_PORT))

# Get the timestamp
timestamp = time.strftime("_%d%m%Y_%H%M%S", time.localtime())
print("Starting acquisition at "+timestamp)
print("Ctrl-C to stop")


fp =open(FILENAME+timestamp+'.bhr', 'wb+')
fp.write(FILEHDR.encode())  # 11 character string to denote file format
fp.write(struct.pack('hhhh',BYTESINHEADER-1,TRACELEN, 2, 1)) # short ints with trace hdr and data lengths

while True :
    while len(data) < 2048:
        data = data + list(s.recv(BUFFER_SIZE)) 
        #print "length data ",len(data)
    datanum = []
    for i in range(len(data)):
        datanum.append(data[i])
    #print "length datanum ", len(datanum)
    for i in range(len(datanum)-BYTESINHEADER-BYTESINTRACE):
        if datanum[i] == STARTBYTE and datanum[i+BYTESINHEADER+BYTESINTRACE-1] == ENDBYTE :
            #print "Trace header found at ", i
            # Extract the trace and remove it from the raw data
            hdr   = datanum[i : i+BYTESINHEADER-1]
            trace = datanum[i+BYTESINHEADER-1 : i+BYTESINHEADER-1+BYTESINTRACE]
            tracecount = tracecount + 1
            #if tracecount == 10 :
            #    print trace
            traceval = []
            for j in range(0, len(trace), 2) :
                nextval = trace[j+0] * 256 + trace[j+1]
                if nextval > 127*256 : nextval = nextval - 256*256
                traceval.append( nextval )
            traceval2d.append(traceval)
            traceval2d.pop(0)
            if tracecount == 20 :
                print("trace number ", hdr[1] * 256 + hdr[2])
                tracecount = 0
            data = data[i+BYTESINHEADER+BYTESINTRACE : len(data)]
            fp.write(struct.pack('4B',*hdr))
            fp.write(struct.pack('1024B',*trace))
            break
s.close()


