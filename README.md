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

The following tools have been implemented so far:

pids_gen.py
-----------

This script produces SIS (Station Information Service) PDUs (as defined in http://www.nrscstandards.org/SG/NRSC-5-C/1020sI.pdf) and assembles them into the PIDS logical channel. Each byte of the output file (pids.raw) contains one bit of the PIDS channel.

Currently it produces only the "station name - short format" message which contains the station's four-letter callsign followed by an optional "-FM" suffix.

psd_gen.py
----------

This script generates PSD (Program Services Data) transport PDUs (as defined in http://www.nrscstandards.org/SG/NRSC-5-C/1028sD.pdf and http://www.nrscstandards.org/SG/NRSC-5-C/1085sC.pdf) for use in the audio transport. The PDUs contain metadata such as the song & artist name.

hd_tx.grc, hd_tx.py
-------------------

This GNU Radio flowgraph transmits a hybrid (analog & digital) FM signal. The analog portion is simply a 1 kHz tone. The OFDM symbols for the digital portion are read from symbols.raw. The FFT size is 2048, and each byte of the symbol file contains one channel's OFDM symbol, which can be one of the following values:

| byte | constellation value |
|:----:|---------------------|
| 0    | -1-j                |
| 1    | -1+j                |
| 2    | 1-j                 |
| 3    | 1+j                 |
| 4    | 0 (unused channel)  |
