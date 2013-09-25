"""yEnc

This is a library for encoding/decoding the yEnc standard.
"""

import zlib
import os


def yEncode(char, first=False, last=False):
    """Encode one character using the yEnc algorithm.

    Return the yEnc encoded value and handle the special characters by appending
    the escape character and encoding alternately. One or two characters will be
    returned each time this function is called.

    The 'first' argument has been designed so we encode the characters properly
    if it is the first character of a new line. This will encode period/space/
    tab characters.  Also, passing the 'first' flag inherently will enable the
    'last' flag (to pick up space/tab characters).

    The 'last' argument has been designed to encode the space/tab characters
    properly when the last character of the line is being encoded.
    """

    # check if special rules are being used
    if first:
        last = True

    # holds our output
    output = ''

    # encode the string with yEnc
    e = (ord(char) + 42) % 256

    # check for special characters
    if e == 0x00:
        e = (e + 64) % 256
        output = '='
    # the encoded 0x09 (tab char) was removed in version 1.2 of the yenc spec;
    # however, we still should force to encode this character if it is the
    # first or last character of a line
    elif e == 0x09 and last == True:
        e = (e + 64) % 256
        output = '='
    elif e == 0x0a:
        e = (e + 64) % 256
        output = '='
    elif e == 0x0d:
        e = (e + 64) % 256
        output = '='
    # the encoded 0x20 (space char) should be used it it is the first or the
    # last character of a line
    elif e == 0x20 and last == True:
        e = (e + 64) % 256
        output = '='
    # the encoded 0x2e (period) only needs encoding on the first line to adhere
    # to the nntp rfc
    elif e == 0x2e and first == True:
        e = (e + 64) % 256
        output = '='
    elif e == 0x3d:
        e = (e + 64) % 256
        output = '='

    # append the encoded value to the output string
    output += chr(e)

    # return the value
    return output


def yEncodeData(data, chars):
    """Encode an entire data chunk obeying the formatting rules.

    Using the yEncode function to do the actual work of encoding, yEncodeData
    will pass along things like first/last character flags which will cause
    yEncode to use alternate encoding (encode spaces/tabs at the begining/end
    and encode periods at the start of a line).
    """

    # holds our output
    line = ''
    output = ''
    count = 1

    # loop over data passed
    for char in data:
        # encode each character
        if len(line) == 0:
            line += yEncode(char, first=True)
        elif len(line) == chars:
            line += yEncode(char, last=True)
        elif len(data) == count:
            line += yEncode(char, last=True)
        else:
            line += yEncode(char)

        # check if we have a full line
        if len(line) >= chars:
            # save to output
            output += line + "\r\n"
            # clear the line
            line = ''

    # check if we have a partial line to append
    if len(line) > 0:
        output += line + "\r\n"

    # return our encoded and formatted data
    return output


def yEncodeSingle(filename, chars):
    """Encode a single (non-multipart) yEnc message.

    Useing yEncodeData we will encode the data passed to us into a yEnc message
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
    output = '=ybegin line=' + str(chars) + ' size=' + str(size) + ' name=' + filename + '\r\n'

    # append yEnc data
    output += yEncodeData(data, chars)

    # attach the footer
    output += '=yend size=' + str(size) + ' crc32=' + "%08x"%(crc & 0xFFFFFFFF) + '\r\n'

    # return our encoded and formatted data
    return output


def yEncodeMultiple(filename, partSize, chars):
    """Encode a multipart yEnc message.

    Useing yEncodeData we will encode the data passed to us into a number of
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
        partOutput = '=ybegin part=' + str(i+1) + ' line=' + str(chars) + ' size=' + str(size) + ' name=' + filename + '\r\n'

        # attach the part header
        partOutput += '=ypart begin=' + str(startOffset+1) + ' end=' + str(stopOffset) + '\r\n'

        # append yEnc data
        partOutput += yEncodeData(partData, chars)

        # attach the footer
        # part=10 pcrc32=12a45c78
        partOutput += '=yend size=' + str(partSize) + ' part=' + str(i+1) + ' pcrc=' + "%08x"%(pcrc & 0xFFFFFFFF) + ' crc32=' + "%08x"%(crc & 0xFFFFFFFF) + '\r\n'

        # append to our output list
        output.append(partOutput)

    # return our encoded and formatted data
    return output