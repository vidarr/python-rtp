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

## Sample usage

```

from rtp import Rtp,encode,decode
frame=encode(4711, 42, b'12345', 23, 2012, csrcs=[17,4], version=1)
decoded=decode(frame)
decoded(Rtp.PayloadType)
decoded(Rtp.PayloadType,Rtp.Payload,Rtp.Csrcs)

```

# Copyright

(C) 2021 Michael J. Beer
All rights reserved.

This Software is released under the terms of the MIT license.

See the file `LICENSE` for details.

# Authors

         Michael J. Beer <michael.josef.beer@gmail.com>

