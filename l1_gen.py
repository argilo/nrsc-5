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

# 1011sG.pdf section 8.2
def scramble(bits):
    reg = 0b01111111111
    for i in range(len(bits)):
        next_bit = ((reg >> 9) ^ reg) & 1
        bits[i] ^= next_bit
        reg = (reg >> 1) | (next_bit << 10)
    return bits

def parity(n):
    parity = 0
    while n != 0:
        parity ^= 1
        n &= (n-1)
    return parity

PARITY = [parity(n) for n in range(128)]

# 1011sG.pdf section 9.3
def conv_enc(bits, poly_punc):
    reg = (bits[-6] << 1) | (bits[-5] << 2) | (bits[-4] << 3) | (bits[-3] << 4) | (bits[-2] << 5) | (bits[-1] << 6)
    out = []
    for i in range(len(bits)):
        reg = (reg >> 1) | (bits[i] << 6)
        out += [PARITY[reg & p] for p in poly_punc[i & 1]]
    return out

# 1011sG.pdf section 9.3.4.1
def conv_1_3(bits):
    return conv_enc(bits, [[0o0133, 0o0171, 0o0165], [0o0133, 0o0171, 0o0165]])

# 1011sG.pdf section 9.3.4.2
def conv_2_5(bits):
    return conv_enc(bits, [[0o0133, 0o0171, 0o0165], [0o0133, 0o0171]])

# 1011sG.pdf section 9.3.4.3
def conv_1_2(bits):
    return conv_enc(bits, [[0o0133, 0o0165], [0o0133, 0o0165]])

# 1011sG.pdf section 9.3.4.4
def conv_2_7(bits):
    return conv_enc(bits, [[0o0133, 0o0171, 0o0165, 0o0165], [0o0133, 0o0171, 0o0165]])

def reverse_bytes(bits):
    for i in range(0, len(bits), 8):
        bits[i], bits[i+7] = bits[i+7], bits[i]
        bits[i+1], bits[i+6] = bits[i+6], bits[i+1]
        bits[i+2], bits[i+5] = bits[i+5], bits[i+2]
        bits[i+3], bits[i+4] = bits[i+4], bits[i+3]
    return bits

# 1011sG.pdf section 10.4.1.1
V = [10,2,18,6,14,8,16,0,12,4,11,3,19,7,15,9,17,1,13,5]
Vinv = [V.index(i) for i in range(20)]

# 1011sG.pdf section 10.2.3.3
def row_col(ki, C):
    return (ki * 11) % 32, ((ki * 11) + (ki // (32*9))) % C

# 1011sG.pdf sections 10.2.3 & 10.2.4
def interleaver_i_ii(p1_g, pids_g):
    J = 20 # number of partitions
    B = 16 # blocks
    C = 36 # columns per partition
    M = 1  # factor: 1, 2 or 4

    b = 200
    N1 = 365440
    N2 = 3200

    int_mat = [[0]*(20*36) for row in range(16*32)]

    for i in range(N1):
        partition = V[((i + (2 * (M // 4))) // M) % J] # V[i % J] when M = 1
        if M == 1:
            block = ((i // J) + (partition * 7)) % B
        ki = i // (J*B)
        row, col = row_col(ki, C)
        int_mat[(block * 32) + row][(partition * C) + col] = p1_g[i]

    for i in range(N2):
        partition = V[i % J]
        block = i // b
        ki = ((i // J) % (b // J)) + (N1 // (J * B))
        row, col = row_col(ki, C)
        int_mat[(block * 32) + row][(partition * C) + col] = pids_g[i]

    return int_mat

# 1011sG.pdf section 12.3.2
REF_SC_CHAN = list(range(-546, -280+1, 19)) + [-279] + list(range(-266, 266+1, 19)) + [279] + list(range(280, 546+1, 19))
# 1011sG.pdf section 11.2.3
REF_SC_ID = [abs(n-30) % 4 for n in range(61)]

def add_parity(bits):
    parity = "0" if (bits.count("1") % 2 == 0) else "1"
    return bits + parity

# 1011sG.pdf section 11.3
def differential_bpsk(bits):
    symbols = []
    last_symbol = 0
    for bit in bits:
        if bit == "1":
            last_symbol ^= 3
        symbols.append(last_symbol)
    return symbols

# 1011sG.pdf table 11-1
def primary_sc_data_seq(scid, sci, bc, psmi):
    return "0110010" + add_parity("0") \
        + "1" + add_parity("{:02b}{:01b}".format(scid, sci)) \
        + "0" + add_parity("0{:04b}".format(bc)) \
        + "11" + add_parity("10{:06b}".format(psmi))

# 1011sG.pdf table 11-2
def secondary_sc_data_seq(scid, sci, bc, ssmi):
    return "0110010" + add_parity("0") \
        + "1" + add_parity("{:02b}0".format(scid)) \
        + "0" + add_parity("0{:04b}".format(bc)) \
        + "11" + add_parity("000{:05b}".format(ssmi))

def frame_primary_sc_data_symbols(scid, sci, psmi):
    bits = ""
    for bc in range(16):
        bits += primary_sc_data_seq(scid, sci, bc, psmi)
    return differential_bpsk(bits)

def frame_secondary_sc_data_symbols(scid, sci, ssmi):
    bits = ""
    for bc in range(16):
        bits += primary_sc_data_seq(scid, sci, bc, ssmi)
    return differential_bpsk(bits)

PRIMARY_SC_SYMBOLS = [frame_primary_sc_data_symbols(scid, 0, 1) for scid in range(4)]


with open('pids.raw', 'rb') as fpids:
    with open('p1.raw', 'rb') as fp1:
        with open('symbols.raw', 'wb') as fout:
            while True:
                pids_bits = bytearray(fpids.read(80 * 16))
                if len(pids_bits) < 1280: break

                pids_g = []
                for i in range(0, len(pids_bits), 80):
                    pids_g += conv_2_5(scramble(reverse_bytes(pids_bits[i:i+80])))


                p1_bytes = bytearray(fp1.read(146176 // 8))
                if len(p1_bytes) < 146176 // 8: break

                p1_bits = []
                for byte in p1_bytes:
                    p1_bits += [int(b) for b in "{0:08b}".format(byte)][::-1]

                p1_g = conv_2_5(scramble(p1_bits))


                int_mat = interleaver_i_ii(p1_g, pids_g)

                for i in range(512):
                    syms = bytearray([4] * 2048)
                    for chan in list(range(0, 10+1)) + list(range(50, 60+1)):
                        syms[REF_SC_CHAN[chan]+1024] = PRIMARY_SC_SYMBOLS[REF_SC_ID[chan]][i]

                    # subcarrier mapping
                    part = 0
                    for chan in list(range(0, 10)) + list(range(50, 60)):
                        for j in range(18):
                            ii = int_mat[i][(part * 36) + (j * 2)]
                            qq = int_mat[i][(part * 36) + (j * 2) + 1]
                            symbol = (ii << 1) | qq
                            carrier = (REF_SC_CHAN[chan] + 1024) + (j + 1)
                            syms[carrier] = symbol
                        part += 1

                    fout.write(syms)
                print("Wrote frame.")
