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

from datetime import datetime

# 1020sI.pdf table 4-5
NUM_TO_CHAR = [chr(i) for i in range(65, 91)] + [' ', '?', '-', '*', '$']
CHAR_TO_BITS = {c: [int(d) for d in "{0:05b}".format(i)] for (i, c) in enumerate(NUM_TO_CHAR)}

# 1020sI.pdf table 4-4
EXTENSION_NONE = [0,0]
EXTENSION_FM = [0,1]

# 1020sI.pdf figure 4-1
TIME_NOT_LOCKED = [0]
TIME_LOCKED_TO_GPS = [1]

# 1020sI.pdf section 4.10
# Note: The specified CRC is incorrect. It's actually a 16-bit CRC
# truncated to 12 bits, and g(x) = X^16 + X^11 + X^3 + X + 1
def crc12(bits):
    poly = 0xD010
    reg = 0x0000
    for b in bits[::-1] + [0]*16:
        lowbit = reg & 1
        reg >>= 1
        reg ^= (b << 15)
        if lowbit:
            reg ^= poly
    reg ^= 0x955
    return [int(b) for b in "{0:012b}".format(reg & 0x0fff)]

# 1020sI.pdf section 4.2.1
def station_name_short(callsign, extension):
    message = [0,0,0,1]
    for char in callsign[0:4]:
        message += CHAR_TO_BITS[char]
    message += extension
    return message

# 1020sI.pdf figure 4-1
def sis_pdu(messages, time_locked, alfn_bits):
    pdu = [0]
    if len(messages) == 1:
        pdu += [0] + messages[0] + [0]*(62 - len(messages[0]))
    else:
        pdu += [1] + messages[0] + messages[1] + [0]*(62 - len(messages[0]) - len(messages[1]))
    pdu += [0] + time_locked + alfn_bits
    pdu += crc12(pdu)
    return pdu

sdr_fm = station_name_short('ABCD', EXTENSION_FM)

NUM_FRAMES = 32
initial_alfn = int((datetime.now() - datetime(1980, 1, 6)).total_seconds() * 44100 / 65536)

with open('pids.raw', 'wb') as f:
    for alfn in range(initial_alfn, initial_alfn + NUM_FRAMES):
        print("ALFN {0:08x}:".format(alfn))
        alfn_bits = [int(b) for b in "{0:032b}".format(alfn)]
        for block in range(16):
            pids_bits = sis_pdu([sdr_fm], TIME_NOT_LOCKED, alfn_bits[(15-block)*2 : (15-block)*2 + 2])
            print("".join([str(b) for b in pids_bits]))
            f.write(bytearray(pids_bits))
        print("")
