"""yEnc

This is a library for decoding the yEnc standard.
"""

import zlib
import yEncException


class Decoder:

    def __init__(self, raw):
        # holds the data to decode
        self.data = None

        # holds header/footer and the encoded data
        self.yenc_header = None
        self.yenc_footer = None
        self.yenc_data = None

        # configuration variables.
        self.line_length = None

        # flag for determining single/multi-part encoding
        self.multipart = None

        # single part yEnc attributes
        self.crc = None
        self.size = None
        self.name = None

        # was data passed?
        self.scan(raw)

    def ydecode(self, line):
        """Decode one character using the yEnc algorithm.


        """

        escaped = False
        output = ''

        # loop over the whole line
        for char in line:
            # get ascii value of the character
            decoded = ord(char)

            # do we have an escape character?
            if decoded == 0x3d:
                # set our escaped flag; clear our temp character
                escaped = True
            else:
                # see if we have seen our escaped flag
                if escaped:
                    # undo the critical character encoding; clear flag
                    decoded = (decoded - 42 - 64 + 256) % 256
                    escaped = False
                else:
                    # undo the normal encoding
                    decoded = (decoded - 42 + 256) % 256

                # store character
                output += chr(decoded)

        # this should never be true unless a bad encoding
        if escaped:
            raise yEncException('Escape character found as last entry on line')

        # return the output to caller
        return output

    def scan(self, raw):
        """Scan the raw data for yEnc data

        """

        # break the lines apart
        lines = raw.splitlines()

        # flags for processing
        header_flag = False
        part_flag = False
        data_flag = False
        footer_flag = False

        # process line by line
        for line in lines:
            # remove proceeding/trailing whitespace
            line.strip()

            # check for header
            if line.startswith('=ybegin '):
                if self.yenc_header is None:
                    self.yenc_header = line
                    self.yenc_data = []
                    header_flag = True
                    data_flag = True
                    self.processheader()
                else:
                    raise yEncException('At least two =ybegin lines found')
                continue

            # check for part
            if line.startswith('=ypart ') and header_flag:
                header_flag = False
                continue

            # check for footer
            if line.startswith('=yend '):
                if self.yenc_footer is None:
                    self.yenc_footer = line
                    data_flag = False
                    footer_flag = True
                    self.processfooter()
                else:
                    raise yEncException('At least two =yend lines found')
                continue

            # determine if this is data
            if data_flag:
                self.yenc_data.append(line)

        # decode to data
        self.data = ''

        for line in self.yenc_data:
            self.data += self.ydecode(line)

        # compare the size to decoded data
        length = len(self.data)
        if self.size != length:
            raise yEncException('Size does not match header/footer value')

        # crc the data for compare
        calc_crc = zlib.crc32(self.data) & 0xffffffff
        if self.crc != calc_crc:
            raise yEncException('CRC32 does not match footer value')

    def processheader(self):
        """Process the =ybegin line into its components

        """
        parts = self.yenc_header.split()

        for part in parts:
            check = part.split('=')

            if check[0] == 'line':
                self.line_length = int(check[1])
                continue

            if check[0] == 'size':
                self.size = int(check[1])
                continue

            if check[0] == 'name':
                self.name = check[1]
                continue

    def processfooter(self):
        """Process the =yend line into its components

        """
        parts = self.yenc_footer.split()

        for part in parts:
            check = part.split('=')

            if check[0] == 'size':
                if self.size != int(check[1]):
                    raise yEncException("Size in footer does not match size in header")
                continue

            if check[0] == 'crc32':
                self.crc = int(check[1], 16)
                continue