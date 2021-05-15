# python-rtp

***python-rtp*** is a simple Python 3 module to encode/decode
[RTP](https://en.wikipedia.org/wiki/Real-time_Transport_Protocol) frames.

## requirements

Apart from Python 3 (version <= ), nothing is required.

## Usage

The module provide

* `encode` to encode RTP frames
* `decode` to decode RTP frames

`encode` is straight forward - give the parameters like Stream Source ID and
payload to the function, and it will return a byte string representing the
RTP frame.

`decode` takes a byte string and returns a function.
You can feed the function value of  the `Rtp` enum.
It will return the value of this field for the decoded frame:

```
>>> decoded=decode(b'B*\\x00\\x17\\x00\\x00\\x07\\xdc\\x00\\x00\\x12g\\x00\\x00\\x00\\x11\\x00\\x00\\x00\\x0412345')
>>> decoded(Rtp.PayloadType)
42
```

Or pass several fields at once:

```
>>> decoded(Rtp.PayloadType,Rtp.Payload)
[42, b'12345']
```

See their documentation for more details.

## Sample code

```
>>> from rtp import Rtp,encode,decode
>>> frame=encode(4711, 42, b'12345', 23, 2012, csrcs=[17,4], version=1)
>>> frame
b'B*\\x00\\x17\\x00\\x00\\x07\\xdc\\x00\\x00\\x12g\\x00\\x00\\x00\\x11\\x00\\x00\\x00\\x0412345'
>>> decoded=decode(frame)
>>> decoded(Rtp.PayloadType)
42
>>> decoded(Rtp.PayloadType,Rtp.Payload,Rtp.Csrcs)
[42, b'12345', [17, 4]]

```

# Copyright

(C) 2021 Michael J. Beer
All rights reserved.

Redistribution  and use in source and binary forms, with or with‐
out modification, are permitted provided that the following  con‐
ditions are met:

1. Redistributions of source code must retain the above copyright
notice, this list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above  copy‐
right  notice,  this  list  of  conditions and the following dis‐
claimer in the documentation and/or other materials provided with
the distribution.

3.  Neither the name of the copyright holder nor the names of its
contributors may be used to endorse or promote  products  derived
from this software without specific prior written permission.

THIS  SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBU‐
TORS "AS IS" AND ANY EXPRESS OR  IMPLIED  WARRANTIES,  INCLUDING,
BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
FITNESS FOR A PARTICULAR PURPOSE  ARE  DISCLAIMED.  IN  NO  EVENT
SHALL  THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DI‐
RECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR  CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE
GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS IN‐
TERRUPTION)  HOWEVER  CAUSED  AND  ON  ANY  THEORY  OF LIABILITY,
WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING  NEGLI‐
GENCE  OR  OTHERWISE)  ARISING  IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# Authors

         Michael J. Beer <michael.josef.beer@gmail.com>

