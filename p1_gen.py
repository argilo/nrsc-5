#
# Copyright 2016 Clayton Smith (argilo@gmail.com)
#
# This file is part of NRSC-5 Tools.
#
# NRSC-5 Tools is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# NRSC-5 Tools is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with NRSC-5 Tools.  If not, see <http://www.gnu.org/licenses/>.
#

from __future__ import division
import reedsolo
import struct

silence_packet = bytearray([0x41, 0x2c, 0x41, 0xb0, 0x43, 0xe5, 0x7b, 0x46, 0x80, 0x3e,
    0x6d, 0x21, 0x70, 0x00, 0x00, 0x00, 0x00, 0x02, 0x16, 0x52, 0x00, 0x6f, 0x8d])

# 1014sI.pdf table 5-3
CW0 = [0,0,1,1,1,0,0,0,1,1,0,1,1,0,0,0,1,1,0,1,0,0,1,1] # MPS/SPS
CW1 = [1,1,0,0,1,1,1,0,0,0,1,1,0,1,1,0,0,0,1,1,0,1,0,0] # MPS/SPS + Opportunistic Data
CW2 = [1,1,1,0,0,0,1,1,0,1,1,0,0,0,1,1,0,1,0,0,1,1,0,0] # MPS/SPS + Fixed Data
CW3 = [1,0,0,0,1,1,0,1,1,0,0,0,1,1,0,1,0,0,1,1,0,0,1,1] # MPS/SPS + Fixed Data + Opportunistic Data
CW4 = [0,0,1,1,0,1,1,0,0,0,1,1,0,1,0,0,1,1,0,0,1,1,1,0] # Fixed Data

# 1014sI.pdf table 5-4
def header_spread_params(L):
    if L < 72000:
        n_start = 120
        if L % 8 == 0:
            n_offset = (L - 120) // 24 - 1
            header_len = 24
        elif L % 8 == 7:
            n_offset = ((L // 8 - 14) // 23) * 8 - 1
            header_len = 23
        else:
            n_offset = ((L // 8 - 14) // 22) * 8 - 1
            header_len = 22
    else:
        if L % 8 == 0:
            n_start = L - 30000
            n_offset = 1247
            header_len = 24
        elif L % 8 == 7:
            n_start = 8 * (L // 8) - 29999
            n_offset = 1303
            header_len = 23
        else:
            n_start = 8 * (L // 8) - 29999
            n_offset = 1359
            header_len = 22
    return (n_start, n_offset, header_len)

# 1014sI.pdf figure 5-2
def header_spread(bits, pci):
    n_start, n_offset, header_len = header_spread_params(len(bits) + 24)
    out = bits[:n_start]
    for i in range(header_len - 1):
        out.append(pci[i])
        out += bits[n_start + n_offset * i : n_start + n_offset * (i+1)]
    out.append(pci[header_len - 1])
    out += bits[n_start + n_offset * (header_len - 1):]
    return out

# 1017sG.pdf section 5.2.3.2
CRC_TABLE = []
for b in range(256):
    v = b
    for i in range(8):
        v = ((v << 1) & 0xff) ^ 0x31 if v & 0x80 else ((v << 1) & 0xff)
    CRC_TABLE.append(v)

def crc8(bytes):
    reg = 0xff
    for byte in bytes:
        reg = CRC_TABLE[reg ^ byte]
    return reg

# 1017sG.pdf figure 5-2
def pdu_control_word(codec_mode, stream_id, pdu_seq_no, blend_control, per_stream_delay,
        common_delay, latency, p_first, p_last, start_seq_no, nop, hef, la_loc):
    out = bytearray([0] * 6)
    out[0] = ((pdu_seq_no & 0b11) << 6) | (stream_id << 4) | codec_mode
    out[1] = (per_stream_delay << 3) | (blend_control << 1) | (pdu_seq_no >> 2)
    out[2] = ((latency & 0b11) << 6) | common_delay
    out[3] = ((start_seq_no & 0b11111) << 3) | (p_last << 2) | (p_first << 1) | (latency >> 2)
    out[4] = (hef << 7) | (nop << 1) | (start_seq_no >> 5)
    out[5] = la_loc
    return out

# 1017sG.pdf section 5.2.1.6
def header_expansion_fields(class_ind, program_number, access, program_type):
    out = bytearray()
    # 1017sG.pdf section 5.2.1.6.1.1
    if class_ind != None:
        out.append(0b10000000 | class_ind)
    # 1017sG.pdf section 5.2.1.6.2.1
    out.append(0b10010000 | (program_number << 1))
    # 1017sG.pdf section 5.2.1.6.3.1
    out.append(0b10100000 | (access << 3) | (program_type >> 7))
    out.append(program_type & 0b01111111)
    return out

def read_audio_packets(f):
    nop = 32
    audio_packets = []
    for i in range(nop):
        header = bytearray(f.read(7))
        if len(header) < 7 or header[0] != 0xff or header[1] & 0xf0 != 0xf0:
            return audio_packets
        length = (header[3] & 0x03) << 11 | (header[4] << 3) | (header[5] >> 5)
        packet = bytearray(f.read(length - 7))
        audio_packets.append(packet)
    return audio_packets


rs = reedsolo.RSCodec(8)

NUM_FRAMES = 32

fpsd = [open('psd{0}.raw'.format(channel+1), 'rb') for channel in range(8)]
faudio = open('sample.hdc', 'rb')

with open('p1.raw', 'wb') as fout:
    start_seq_no = 0
    for frame in range(NUM_FRAMES):
        pdu_seq_no = frame % 2
        p1_bytes = bytearray()
        for channel in range(3):
            if channel == 0:
                audio_packets = read_audio_packets(faudio)
            else:
                audio_packets = [silence_packet] * 32

            # 1017sG.pdf figure 5-1
            nop = len(audio_packets)
            la_loc = 8 + 6 + nop*2 + 128 - 1

            end = la_loc
            ends = []
            for packet in audio_packets:
                end += len(packet) + 1
                ends.append(end)

            pdu = pdu_control_word(codec_mode = 0, stream_id = 0, pdu_seq_no = pdu_seq_no, blend_control = 2,
                per_stream_delay = 0, common_delay = 0, latency = 4, p_first = 0, p_last = 0,
                start_seq_no = start_seq_no, nop = nop, hef = 1, la_loc = la_loc)

            pdu += struct.pack("<"+"H"*nop, *ends)

            hef = header_expansion_fields(class_ind = None, program_number = channel, access = 0, program_type = 14)
            pdu += hef
            pdu += bytearray(fpsd[channel].read(128 - len(hef)))

            for packet in audio_packets:
                pdu += packet
                pdu.append(crc8(packet))

            pdu = rs.encode(pdu[87::-1])[::-1] + pdu[88:]
            p1_bytes += pdu

        start_seq_no = (start_seq_no + nop) % 64
        p1_bytes += bytearray([0] * ((146176-24) // 8 - len(p1_bytes)))

        p1_bits = []
        for byte in p1_bytes:
            p1_bits += [int(b) for b in "{0:08b}".format(byte)]

        p1_bits = header_spread(p1_bits, CW0)
        p1_bytes = bytearray([int("".join([str(b) for b in p1_bits[i:i+8]]), 2) for i in range(0, len(p1_bits), 8)])
        fout.write(p1_bytes)

faudio.close()
for channel in range(8):
    fpsd[channel].close()
