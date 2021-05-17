#!/usr/bin/python3
#
# (C) 2021 Michael J. Beer
# All rights reserved.
#
# Redistribution  and use in source and binary forms, with or with‐
# out modification, are permitted provided that the following  con‐
# ditions are met:
#
# 1. Redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above  copy‐
# right  notice,  this  list  of  conditions and the following dis‐
# claimer in the documentation and/or other materials provided with
# the distribution.
#
# 3.  Neither the name of the copyright holder nor the names of its
# contributors may be used to endorse or promote  products  derived
# from this software without specific prior written permission.
#
# THIS  SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBU‐
# TORS "AS IS" AND ANY EXPRESS OR  IMPLIED  WARRANTIES,  INCLUDING,
# BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
# FITNESS FOR A PARTICULAR PURPOSE  ARE  DISCLAIMED.  IN  NO  EVENT
# SHALL  THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DI‐
# RECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR  CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE
# GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS IN‐
# TERRUPTION)  HOWEVER  CAUSED  AND  ON  ANY  THEORY  OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING  NEGLI‐
# GENCE  OR  OTHERWISE)  ARISING  IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
#------------------------------------------------------------------------------

"""
De/Encoding of RTP frames

Encode a frame:

    >>> encode(ssrc=12, payload_type = 1, payload = [1, 2, 3, 4], seq = 0, timestamp = 1234)
    b'\\x80\\x01\\x00\\x00\\x00\\x00\\x04\\xd2\\x00\\x00\\x00\\x0c\\x01\\x02\\x03\\x04'

Decode a frame:

    >>> decoded = decode(b'\\x80\\x01\\x00\\x00\\x00\\x00\\x04\\xd2\\x00\\x00\\x00\\x0c\\x01\\x02\\x03\\x04')
    >>> decoded(Rtp.Version, Rtp.Payload)
    [2, b'\\x01\\x02\\x03\\x04']

Note:

   * Extension header unsupported - if present in encoded frame, will be skipped

@author Michael J. Beer <michael.josef.beer@gmail.com>
@copyright (c) 2021 Michael J. Beer
@date 2021-05-14

@license MIT

@status Development

"""

#------------------------------------------------------------------------------

import os
from sys import argv, stdout
from struct import unpack, pack
from enum import Enum, unique

#-------------------------------------------------------------------------------

@unique
class Rtp(Enum):

    Payload = 0
    PayloadType = 1
    Ssrc = 2
    Csrcs = 3
    Timestamp = 4
    SequenceNumber = 5
    Version = 6
    Marker = 7
    Padding = 8

#-------------------------------------------------------------------------------

def decode(frame):

    '''
    Decode an RTP frame.
    Returns a function, which takes as argument the field one wants to querry:

    decoded = decode(frame)
    payload = decoded(Rtp.Payload)

    Sample:

    >>> decoded = decode(b'\\x80\\x01\\x00\\x00\\x00\\x00\\x04\\xd2\\x00\\x00\\x00\\x0c\\x01\\x02\\x03\\x04')
    >>> decoded(Rtp.Timestamp)
    1234

    You might also query several fields at once:
    >>> decoded = decode(b'\\x80\\x01\\x00\\x00\\x00\\x00\\x04\\xd2\\x00\\x00\\x00\\x0c\\x01\\x02\\x03\\x04')
    >>> decoded(Rtp.Version, Rtp.Payload)
    [2, b'\\x01\\x02\\x03\\x04']
    '''

    def parse_32bit_nums_big_endian(num, inbytes):

        print(f"{num}")

        numbers = []

        for i in range(num):
            numbers.append(unpack(">I", inbytes[i * 4: i * 4 + 4])[0])

        return numbers


    possible_indices = set(item.value for item in Rtp)

    data = [None] * len(Rtp)

    def get_fields(index, *more_indices):

        def get_field(i):
            if not i in Rtp:
                raise ValueError()
            return data[i.value]

        if not more_indices:
            return get_field(index)

        return [get_field(index)] + [get_field(i) for i in more_indices]


    (h1, h2, seq, ts, ssrc) = unpack(">BBHII", frame[:12])

    data[Rtp.SequenceNumber.value] = seq
    data[Rtp.Timestamp.value] = ts
    data[Rtp.Ssrc.value] = ssrc
    data[Rtp.PayloadType.value] = h2 & 0x7f
    data[Rtp.Marker.value] = (h2 & 0x80) >> 7
    data[Rtp.Version.value] = (h1 & 0xc0) >> 6

    num_csrcs = h1 & 0x0f
    data[Rtp.Csrcs.value] = parse_32bit_nums_big_endian(num_csrcs, frame[12:])

    read_index = num_csrcs * 4 + 12

    if (h1 & 0x10):
        read_index = index_after_extension_header(frame[read_index:])

    payload = frame[read_index:]

    if (h1 & 0x20):
        padding_length = payload[-1]
        data[Rtp.Padding.value] = payload[-padding_length - 1:-1]
        payload = payload[:-padding_length - 1]


    data[Rtp.Payload.value] = payload

    return get_fields

#-------------------------------------------------------------------------------

def encode(ssrc, payload_type, payload, seq, timestamp, **args):

    '''
    Encode to an RTP (v2) frame
    Additional arguments might be
    version 1 or 2 are supported (but really, only 2 makes actual sense)
    csrcs   List of CSRC ids (maximum of 15 are supported by RTP)
    padding byte string that will be appended to the payload as padding
    marker  true or false depending whether marker bit should be set

    Example:

    >>> encode(4711, 42, b'12345', 23, 2012, csrcs=[17,4], version=1)
    b'B*\\x00\\x17\\x00\\x00\\x07\\xdc\\x00\\x00\\x12g\\x00\\x00\\x00\\x11\\x00\\x00\\x00\\x0412345'
    '''

    if 0x7f < payload_type:
        raise ValueError(f'Payload Type out of range: 0 - {0x7f} allowed')

    version = args.get("version", 2)
    csrcs = args.get('csrcs', [])
    padding = args.get('padding', [])
    marker = args.get('marker', False)


    if version not in set([1, 2]):
        raise ValueError("Version must be either 1 or 2")

    if 15 < len(csrcs):
        raise ValueError(
                f"Maximum supported number of CSRC ids (15) surpassed: " +
                f"{len(csrcs)}")

    h1 = (version << 6)

    if padding:
        h1 = h1 | 0x20

    h1 += len(csrcs)

    h2 = payload_type & 0x7f

    if marker:
        h2 = h2 | 0x80

    frame = pack(">BBHII", h1, h2, seq, timestamp, ssrc)

    for csrc in csrcs:

        if csrc > 0xffffffff:
            raise ValueError("CSRC out of range")

        frame += pack(">I", csrc)

    frame += bytes(payload)

    if len(padding) > 0xff:
        raise ValueError(f"Padding too long - max. supported length is {0xff}")

    if padding:
        frame += bytes(padding)
        frame += bytes([len(padding)])

    return frame

#--------------------------------------------------------------------------------

def dump(decoded_frame, out=stdout):

    '''
    Dumps a decoded RTP frame to `out`.
    '''

    for field in Rtp:
        out.write(f'{field} :  {decoded_frame(field)}\n')

#------------------------------------------------------------------------------

if __name__ == "__main__":

    '''
    Run doctests / unit tests
    '''

    import doctest
    print(doctest.testmod())

    # Some test data ...

    payload = bytes([0xf1, 0xe2, 0xd3, 0xc4, 0xb5, 0xa6])

    payload_type = 127

    sequence_number = 4660
    timestamp = 2729690325
    ssrc = 3519198116

    version = 1

    csrcs = [3, 4, 7, 11, 0x192837ff]

    # This is the above data properly encoded as RTP frame

    test_frame = [
            0x45, 0x7f, 0x12, 0x34, 0xa2, 0xb3, 0xc4, 0xd5,
            0xd1, 0xc2, 0xb3, 0xa4, 0x00, 0x00, 0x00, 0x03,
            0x00, 0x00, 0x00, 0x04, 0x00, 0x00, 0x00, 0x07,
            0x00, 0x00, 0x00, 0x0b, 0x19, 0x28, 0x37, 0xff,
            0xf1, 0xe2, 0xd3, 0xc4, 0xb5, 0xa6]

    decoded = decode(bytes(test_frame))

    encoded = encode(ssrc, payload_type, payload, sequence_number, timestamp,
            version = version, csrcs = csrcs)

    decoded = decode(encoded)

    dump(decoded)

    assert(ssrc == decoded(Rtp.Ssrc))
    assert(sequence_number == decoded(Rtp.SequenceNumber))
    assert(timestamp == decoded(Rtp.Timestamp))
    assert(payload_type == decoded(Rtp.PayloadType))
    assert(payload == decoded(Rtp.Payload))
    assert(None == decoded(Rtp.Padding))
    assert(False == decoded(Rtp.Marker))

    for csrc, ref in zip(csrcs, decoded(Rtp.Csrcs)):
        assert(csrc == ref)

    print("\n\nTest padding ...\n")

    padding = bytes([1, 2, 3])
    test_frame += padding + bytes([len(padding)])
    test_frame[0] = test_frame[0] | 0x20

    decoded = decode(bytes(test_frame))

    encoded = encode(ssrc, payload_type, payload, sequence_number, timestamp,
            version = version, csrcs = csrcs, padding=padding)

    assert(bytes(test_frame) == encoded)

    decoded = decode(encoded)

    dump(decoded)

    assert(ssrc == decoded(Rtp.Ssrc))
    assert(sequence_number == decoded(Rtp.SequenceNumber))
    assert(timestamp == decoded(Rtp.Timestamp))
    assert(payload_type == decoded(Rtp.PayloadType))
    assert(payload == decoded(Rtp.Payload))
    assert(padding == decoded(Rtp.Padding))
    assert(False == decoded(Rtp.Marker))

    print("\n\nTest marker bit ...\n")

    test_frame[1] = test_frame[1] | 0x80

    decoded = decode(bytes(test_frame))

    encoded = encode(ssrc, payload_type, payload, sequence_number, timestamp,
            version = version, csrcs = csrcs, padding=padding, marker=True)

    assert(bytes(test_frame) == encoded)

    decoded = decode(encoded)

    dump(decoded)

    assert(ssrc == decoded(Rtp.Ssrc))
    assert(sequence_number == decoded(Rtp.SequenceNumber))
    assert(timestamp == decoded(Rtp.Timestamp))
    assert(payload_type == decoded(Rtp.PayloadType))
    assert(payload == decoded(Rtp.Payload))
    assert(padding == decoded(Rtp.Padding))
    assert(True == decoded(Rtp.Marker))
