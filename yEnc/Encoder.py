"""yEnc

This is a library for encoding using the yEnc standard.
"""

import zlib
import os


class yEnc:

    def __init__(self, data=None):
        # holds the data to encode
        self.data = None

        # holds the encoded data
        self.encoded = None

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

    def encode(self, char, first=False, last=False):
        """Encode one character using the yEnc algorithm.

        A character, and two flags are passed to this function. The character
        is the value to be encoded (a single ASCII character) while the flags
        represent the position of the character (first position of the line or
        last position of the line).

        Additional checks will be preformed if the character is in the first or
        last position of the line.

        Both space and tab characters will be considered critical characters if
        they are the first or last character on a line. This is to ensure that
        a yEnc decoder does not discard the whitespace on either end of the
        encoded line.

        Additionally, if the first character of a line is a period, this yEnc
        implementation *WILL* consider it a critical character and encode it to
        ensure conformance to the NNTP RFC when writing to a raw socket. This
        can be removed if it is undesired behavior.
        """

        # encode the character
        e = (ord(char) + 42) % 256

        # check for critical characters
        if e == 0x00:
            e = (e + 64) % 256
            self.temp = '='
        elif e == 0x0a:
            e = (e + 64) % 256
            self.temp = '='
        elif e == 0x0d:
            e = (e + 64) % 256
            self.temp = '='
        elif e == 0x3d:
            e = (e + 64) % 256
            self.temp = '='

        # the encoded 0x09 (tab char) was removed in version 1.2 of the yEnc
        # spec; however, we still should still consider this a critical
        # character if it is the first or last character of a line
        elif (first or last) and e == 0x09:
            e = (e + 64) % 256
            self.temp = '='
        # the encoded 0x20 (space char) should be considered a critical
        # character if it is the first or last character of a line
        elif (first or last) and e == 0x20:
            e = (e + 64) % 256
            self.temp = '='
        # the encoded 0x2e (period) only needs encoding on the first line to
        # adhere to the nntp rfc
        elif first and e == 0x2e:
            e = (e + 64) % 256
            self.temp = '='

        # append the encoded value to the output string
        self.temp += chr(e)

    def yencodedata(self, data):
        """Encode an entire data chunk obeying the formatting rules.

        This function will use the yencode function to do the actual work of
        encoding. It will pass along the proper flags for first/last character
        designation of each encoded character. This will allow yencode to use
        the alternate encoding rules if required.
        """

        # holds our output
        line = ''
        output = ''
        count = 1

        # loop over data passed
        for char in data:

            # check for first character of line
            if len(line) == 0:
                self.yencode(char, first=True)
            # check for last character of line
            elif len(line) == self.linelength:
                self.yencode(char, last=True)
            # check for last character of data
            elif len(data) == count:
                self.yencode(char, last=True)
            # otherwise, encode normally
            else:
                self.yencode(char)

            # store the encoded character(s) on our line
            line += self.temp

            # check if we have a full line
            if len(line) >= self.linelength:
                # save to output
                output += line + "\r\n"
                # clear the line
                line = ''

        # check if we have a partial line to append
        if len(line) > 0:
            output += line + "\r\n"

        # return our encoded and formatted data
        return output

    def yencodesingle(self, filename):
        """Encode a single (non-multipart) yEnc message.

        Using yEncodeData we will encode the data passed to us into a yEnc message
        with header/footer attached.

        This function does not support multi-part yEnc messages.
        """

        # holds our output
        output = ''

        # get the size of the file.
        size = os.path.getsize(filename)

        # read in the file
        data = file(filename, 'rb').read()

        # store crc of data before encoding
        crc = zlib.crc32(data)

        # attach the header
        output = '=ybegin line=' + str(self.chars) + ' size=' + str(size) + ' name=' + filename + '\r\n'

        # append yEnc data
        output += self.yencodeData(data)

        # attach the footer
        output += '=yend size=' + str(size) + ' crc32=' + "%08x"%(crc & 0xFFFFFFFF) + '\r\n'

        # return our encoded and formatted data
        return output

    def yencodemultiple(self, filename, partSize):
        """Encode a multi-part yEnc message.

        Using yEncodeData we will encode the data passed to us into a number of
        yEnc messages with headers/footers attached.

        This function only supports multi-part yEnc messages.
        """

        # holds our output
        output = []

        # get the size of the file.
        size = os.path.getsize(filename)

        # read in the file
        data = file(filename, 'rb').read()

        # determine number of parts
        totalParts = size / partSize
        if (size % partSize) != 0:
            totalParts += 1

        # store crc of data before encoding
        crc = zlib.crc32(data)

        # loop for each part
        for i in range(totalParts):

            # determine our start/stop offsets
            startOffset = i * partSize
            stopOffset = (i+1) * partSize
            if stopOffset > size:
                stopOffset = size

            # grab the portion of the data for this part
            partData = data[startOffset:stopOffset]

            # determine the part size
            partSize = len(partData)

            # store crc of this parts data before encoding
            pcrc = zlib.crc32(partData)

            # attach the header
            partOutput = '=ybegin part=' + str(i+1) + ' total=' + totalParts + ' line=' + str(self.chars) + ' size=' + str(size) + ' name=' + filename + '\r\n'

            # attach the part header
            partOutput += '=ypart begin=' + str(startOffset+1) + ' end=' + str(stopOffset) + '\r\n'

            # append yEnc data
            partOutput += self.yencodeData(partData)

            # attach the footer
            partOutput += '=yend size=' + str(partSize) + ' part=' + str(i+1) + ' pcrc=' + "%08x"%(pcrc & 0xFFFFFFFF) + ' crc32=' + "%08x"%(crc & 0xFFFFFFFF) + '\r\n'

            # append to our output list
            output.append(partOutput)

        # return our encoded and formatted data
        return output