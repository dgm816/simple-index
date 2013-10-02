"""yEnc

This is a library for decoding the yEnc standard.
"""

import zlib
import os


class yEnc:

    def __init__(self, data=None):
        # holds the data to decode
        self.data = None

        # holds the decoded data
        self.decoded = None

        # configuration variables.
        self.linelength = None

        # yEnc headers/footers
        self.header = None
        self.partheader = None
        self.footer = None

        # flag for determining single/multi-part encoding
        self.multipart = None

        # single part yEnc attributes
        self.crc = None
        self.size = None
        self.line = None
        self.name = None

        # multi-part yEnc attributes
        self.part = None
        self.partsize = None
        self.partbegin = None
        self.partend = None
        self.pcrc = None
        self.total = None

        # was data passed?
        if data is not None:
            # TODO determine if we have encoded data
            pass

    def decode(self, char):
        """Decode one character using the yEnc algorithm.


        """

        # get ascii value of the character
        d = ord(char)

        # do we have an escape character?
        if d == 0x3d:
            # set our escaped flag; clear our temp character
            self.escaped = True
            self.temp = None
        else:
            # see if we have seen our escaped flag
            if self.escaped:
                # undo the critical character encoding; clear flag
                d = (d - 42 - 64 + 256) % 256
                self.escaped = False
            else:
                # undo the normal encoding
                d = (d - 42 + 256) % 256

            # store temp character
            self.temp = chr(d)