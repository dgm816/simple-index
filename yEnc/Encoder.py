"""yEnc

This is a library for encoding using the yEnc standard.
"""

import zlib
import yEncException

class Encoder:

    def __init__(self, data=None, filename=None, line_length=128, part_size=10000):
        # holds the data to encode
        self.data = data

        # holds header/footer and the encoded data
        self.yenc_header = None
        self.yenc_footer = None
        self.yenc_data = None

        # configuration variables.
        self.line_length = line_length
        self.part_size = part_size

        # flag for determining single/multi-part encoding
        self.multipart = None

        # single part yEnc attributes
        self.crc = None
        self.size = None
        self.name = filename

        # was data passed?
        if data is not None:
            # TODO determine if we have encoded data
            pass

    def yencode(self, char, first=False, last=False):
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

        output = ''

        # encode the character
        encoded = (ord(char) + 42) % 256

        # check for critical characters
        if encoded == 0x00:
            encoded = (encoded + 64) % 256
            output = '='
        elif encoded == 0x0a:
            encoded = (encoded + 64) % 256
            output = '='
        elif encoded == 0x0d:
            encoded = (encoded + 64) % 256
            output = '='
        elif encoded == 0x3d:
            encoded = (encoded + 64) % 256
            output = '='

        # the encoded 0x09 (tab char) was removed in version 1.2 of the yEnc
        # spec; however, we still should still consider this a critical
        # character if it is the first or last character of a line
        elif (first or last) and encoded == 0x09:
            encoded = (encoded + 64) % 256
            output = '='
        # the encoded 0x20 (space char) should be considered a critical
        # character if it is the first or last character of a line
        elif (first or last) and encoded == 0x20:
            encoded = (encoded + 64) % 256
            output = '='
        # the encoded 0x2e (period) only needs encoding on the first line to
        # adhere to the nntp rfc
        elif first and encoded == 0x2e:
            encoded = (encoded + 64) % 256
            output = '='

        # append the encoded value to the output string
        output += chr(encoded)

        return output

    def yencodedata(self, chunk):
        """Encode an entire data chunk obeying the formatting rules.

        This function will use the yencode function to do the actual work of
        encoding. It will pass along the proper flags for first/last character
        designation of each encoded character. This will allow yencode to use
        the alternate encoding rules if required.
        """

        # holds our output
        character = ''
        line = ''
        output = []
        count = 1

        # loop over data passed
        for char in chunk:

            # check for first character of line
            if len(line) == 0:
                character = self.yencode(char, first=True)
            # check for last character of line
            elif len(line) == self.line_length:
                character = self.yencode(char, last=True)
            # check for last character of data
            elif len(chunk) == count:
                character = self.yencode(char, last=True)
            # otherwise, encode normally
            else:
                character = self.yencode(char)

            # store the encoded character(s) on our line
            line += character

            # check if we have a full line
            if len(line) >= self.line_length:
                # save to output
                output.append(line)
                # clear the line
                line = ''

        # check if we have a partial line to append
        if len(line) > 0:
            # save to output
            output.append(line)

        # return our encoded and formatted data
        return output

    def yencodesingle(self, data=None, filename=None):
        """Encode a single (non-multipart) yEnc message.

        Using yEncodeData we will encode the data passed to us into a yEnc message
        with header/footer attached.

        This function does not support multi-part yEnc messages.
        """

        # clear anything previously stored
        self.yenc_header = None
        self.yenc_footer = None
        self.yenc_data = []
        self.multipart = False

        # set any passed parameters
        self.setparams(data, filename)

        # ensure we have good object data
        self.checkparams()

        # generate the header
        self.yenc_header = '=ybegin line=' + str(self.line_length) + ' size=' + str(self.size) + ' name=' + filename

        # generate the footer
        self.yenc_footer = '=yend size=' + str(self.size) + ' crc32=' + "%08x"%(self.crc)

        # encode data
        self.yenc_data = self.yencodedata(self.data)

    def yencodemultiple(self, data=None, filename=None):
        """Encode a multi-part yEnc message.

        Using yEncodeData we will encode the data passed to us into a number of
        yEnc messages with headers/footers attached.

        This function only supports multi-part yEnc messages.
        """

        # clear anything previously stored
        self.yenc_header = None
        self.yenc_footer = None
        self.yenc_data = []
        self.multipart = True

        # set any passed parameters
        self.setparams(data, filename)

        # ensure we have good object data
        self.checkparams()

        # determine number of parts
        parts_total = self.size / self.part_size
        if (self.size % self.part_size) != 0:
            parts_total += 1

        # loop for each part
        for i in range(parts_total):

            # holds our generated part
            part = {'yenc_data': []}

            # determine our start/stop offsets
            start_offset = i * self.part_size
            stop_offset = (i+1) * self.part_size
            if stop_offset > self.size:
                stop_offset = self.size

            # grab the portion of the data for this part
            part['part_data'] = self.data[start_offset:stop_offset]

            # determine the part size
            part['part_length'] = len(part['part_data'])

            # store crc of this parts data before encoding
            part['part_crc'] = zlib.crc32(part['part_data']) & 0xffffffff

            # generate the header
            part['yenc_header'] = '=ybegin part=' + str(i+1) + ' total=' + str(parts_total) + ' line=' + str(self.line_length) + ' size=' + str(self.size) + ' name=' + filename

            # generate the part header
            part['yenc_part_header'] = '=ypart begin=' + str(start_offset+1) + ' end=' + str(stop_offset)

            # generate the footer
            part['yenc_footer'] = '=yend size=' + str(part['part_length']) + ' part=' + str(i+1) + ' pcrc=' + "%08x"%(part['part_crc'] & 0xFFFFFFFF) + ' crc32=' + "%08x"%(self.crc)

            # append yEnc data
            part['yenc_data'].append(self.yencodedata(part['part_data']))

            # store to our yenc_data
            self.yenc_data.append(part)

    def checkparams(self):
        """Check the object parameters

        Before operating on the object, ensure we have the minimum required
        information to work with the object.
        """

        # make sure we have all the data we need
        if self.data is None:
            raise yEncException('Data has not been set.')
        if self.name is None:
            raise yEncException('Filename has not been set.')

    def setparams(self, data, filename):
        """Set the object parameters

        Set the object parameters before we use them.  This has been
        made into a function to centralize the parameter assignment
        in an effort to 'DRY' code.
        """

        # set the data
        if data is not None:
            self.data = data
            self.size = len(data)
            self.crc = zlib.crc32(self.data) & 0xffffffff

        # set the name of the file
        if filename is not None:
            self.name = filename