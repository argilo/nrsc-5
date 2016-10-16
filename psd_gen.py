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

import struct

FCSTAB = []
for b in range(256):
    v = b
    for i in range(8):
        v = (v >> 1) ^ 0x8408 if v & 1 else (v >> 1)
    FCSTAB.append(v)

def compute_fcs(bytes):
    fcs = 0xffff
    for byte in bytes:
        fcs = (fcs >> 8) ^ FCSTAB[(fcs ^ byte) & 0xff]
    return fcs ^ 0xffff

def encode_frame(id, data):
    out = id.encode()
    out += struct.pack(">I", len(data) + 1)
    out += b"\x00\x00"
    out += b"\x00"
    out += data.encode()
    return out

def encode_len(l):
    return bytearray([(l >> 21) & 0x7F, (l >> 14) & 0x7F, (l >> 7) & 0x7F, l & 0x7F])

def encode_id3(tags):
    out = b""
    for id, data in tags:
        out += encode_frame(id, data)
    out = b"ID3\x03\x00\x00" + encode_len(len(out)) + out
    return out

def encode_psd_packet(dtpf, port, seq, bytes):
    return struct.pack("<BHH", dtpf, port, seq) + bytes + b"UF"

def encode_ppp(bytes):
    fcs = compute_fcs(bytes)
    bytes += bytearray([fcs & 0xff, fcs >> 8])

    out = bytearray([0x7E])
    for byte in bytes:
        if byte in [0x7D, 0x7E]:
            out.append(0x7D)
            out.append(byte ^ 0x20)
        else:
            out.append(byte)
    return out

port = [0x5100, 0x5201, 0x5202, 0x5203, 0x5204, 0x5205, 0x5206, 0x5207]

for channel in range(8):
    initial_seq_num = 0
    tags = [
        ["TIT2", "Title for HD{0}".format(channel+1)],
        ["TPE1", "Artist for HD{0}".format(channel+1)]
    ]
    with open('psd{0}.raw'.format(channel+1), 'wb') as f:
        for seq_num in range(initial_seq_num, initial_seq_num + 100):
            pdu = encode_ppp(encode_psd_packet(0x21, port[channel], seq_num, encode_id3(tags)))
            f.write(pdu)
        f.write(b"\x7E")
