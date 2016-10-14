```
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
```

NRSC-5 Tools
============

The goal of this project is to implement an HD Radio receiver and transmitter in software, for use with GNU Radio. HD Radio is standardized in NRSC-5. The latest version of the standard is NRSC-5-C, which can be found at http://www.nrscstandards.org/NRSC-5-C.asp.

## Quick start

To transmit and HD Radio signal on 95.7 FM:

1. Download https://drive.google.com/file/d/0BwvnypgBYJseSWREQ0kwd29QakE/view?usp=sharing, rename it to audio.txt and place it alongside the other files in this repo.
1. Run `python pids_gen.py && python psd_gen.py && python p1_gen.py && python l1_gen.py` to generate OFDM symbols.
1. Plug in a USRP B200 and run `./hd_tx.py`.

## Components

The following tools have been implemented so far:

### pids_gen.py

This script produces SIS (Station Information Service) PDUs (as defined in http://www.nrscstandards.org/SG/NRSC-5-C/1020sI.pdf) and assembles them into the PIDS logical channel. Each byte of the output file (pids.raw) contains one bit of the PIDS channel.

Currently it produces only the "station name - short format" message which contains the station's four-letter callsign followed by an optional "-FM" suffix.

### psd_gen.py

This script generates PSD (Program Services Data) transport PDUs (as defined in http://www.nrscstandards.org/SG/NRSC-5-C/1028sD.pdf and http://www.nrscstandards.org/SG/NRSC-5-C/1085sC.pdf) for use in the audio transport. The PDUs contain metadata such as the song & artist name. Output is written to psd.raw.

### p1_gen.py

This script assembles audio packets and PSD PDUs into the audio transport, producing the P1 logical channel (as defined in http://www.nrscstandards.org/SG/NRSC-5-C/1014sI.pdf and http://www.nrscstandards.org/SG/NRSC-5-C/1017sG.pdf). It reads PSD PDUs from psd.raw and audio packets from audio.txt. It writes the P1 logical channel bytes to p1.raw.

The format for the audio.txt file containing audio packets is as follows: The first line consists of a single integer (n) indicating the number of audio packets to be packed into the first audio transport PDU. It is followed by n lines, each containing one audio packet whose bytes are written in hexadecimal format with no spaces. Each subsequent audio transport PDU then appears in the same format (number of audio packets, following by audio packets in hexadecimal). Two sample files containing 32 audio transport PDUs each are available here:

* https://drive.google.com/file/d/0BwvnypgBYJseSWREQ0kwd29QakE/view?usp=sharing
* https://drive.google.com/file/d/0BwvnypgBYJseMS0xaEZKUW1IUGM/view?usp=sharing

For Reed Solomon encoding, p1_gen.py uses [reedsolo 0.3](https://pypi.python.org/pypi/reedsolo), written by Tomer Filiba, which can be found in reedsolo.py. The generator polynomial (defined in the `rs_generator_poly` function) was changed to match the one defined in http://www.nrscstandards.org/SG/NRSC-5-C/1019sG.pdf section 6.3.

### l1_gen.py

This script implements Layer 1 FM (as defined in http://www.nrscstandards.org/SG/NRSC-5-C/1011sG.pdf). It reads in PIDS and P1 PDUs from pids.raw and p1.raw respectively, and writes OFDM symbols to symbols.raw. So far only Primary Service Mode MP1 is implemented.

### hd_tx.grc, hd_tx.py

This GNU Radio flowgraph transmits a hybrid (analog & digital) FM signal. The analog portion is simply a 1 kHz tone. The OFDM symbols for the digital portion are read from symbols.raw. The FFT size is 2048, and each byte of the symbol file contains one channel's OFDM symbol, which can be one of the following values:

| byte | constellation value |
|:----:|---------------------|
| 0    | -1-j                |
| 1    | -1+j                |
| 2    | 1-j                 |
| 3    | 1+j                 |
| 4    | 0 (unused channel)  |
