import re
import socket
import ssl


class MyNntp:
    def __init__(self, server, port, use_ssl):
        """Constructor

        Pass in the server, port, and ssl usage value for connect.
        """

        # just store the values for now
        self.server = server
        self.port = port
        self.ssl = use_ssl

        # define variables we will use throughout our object
        self.s = None
        self.data = unicode()

        self.code = None
        self.text = None

    def parse(self):
        """Parse response to command from server.

        Break the first line from the data buffer into its component parts (if
        it is formatted properly) and retain the three digit server code as well
        as the ASCII string.

        Server code and ASCII string will be set in self.code and self.text if
        it is successfully parsed. The first line will be removed from the data
        buffer as well.

        If the format is not recognized None will be set it both variables. No
        data will be removed from the buffer.
        """

        # make sure we clear any old response stored
        self.code = None
        self.text = None

        # grab the first line from our relieved data (without lin ending)
        index = self.data.find("\r\n")
        line = self.data[:index]

        # break apart the response code and (optionally) the rest of the line
        match = re.match(r"(\d{3})(?: +(.+))?", line)

        # check for match
        if match:
            # store our code and text
            self.code = match.group(1)
            self.text = match.group(2)

            # remove our processed line (including line endings)
            self.data = self.data[index+2:]

        # we are done
        return

    def fetch(self):
        """Get server response.

        Get the response to a command sent to the NNTP server and parse it.
        """

        # receive data from server
        self.data = self.s.recv(1024)

        # parse server response
        self.parse()

        return

    def connect(self):
        """Connect to NNTP server.

        Using the server address, port, and a flag to use ssl, we will connect to
        the server and parse the response from the server using standard sockets.
        """

        # create a socket object and connect
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if self.ssl:
            self.s = ssl.wrap_socket(self.s)
        self.s.connect((self.server, self.port))

        # get data from the server
        self.fetch()

        # check for success
        if self.code != '200':
            return False
        else:
            return True

    def send(self, command):
        """Send a command to the server and get the response.

        Send the command out the connected socket to the server and parse the
        response.
        """

        # send the command to the server
        self.s.sendall(command + "\r\n")

        # get the response from the server
        self.fetch()

        return

    def login(self, username, password):
        """Login to server.

        Login to the server using a username and password. Check for failure to
        login and intelligently handle server responses.
        """

        # send the username to the server
        self.send("AUTHINFO USER " + username)

        # get code 381 if a password is required
        if self.code != '381':
            return False

        # send the password to the server
        self.send("AUTHINFO PASS " + password)

        # get code 281 if successfully logged in
        if self.code != '281':
            return False

        # all went well, return true
        return True

    def listactive(self, processor=None):
        """List Active

        List the active newsgroups available on the server.
        """

        # send the command to the server
        self.send("LIST ACTIVE")

        # check for 215 for multi line response
        if self.code != '215':
            return False

        # regex pattern to recognize results
        pattern = re.compile(r"(\S+) +(\S+) +(\S+) +(\S+)")

        # this is our end of transmission flag
        eot = False

        # are we processing results?
        if processor is None:
            results = []

        # keep looping until our transmission is finished
        while not eot:
            # process the data in our buffer
            for line in self.data.splitlines(True):
                # check for a full line
                if line.endswith("\r\n"):
                    #  check for end of multi line response
                    if line == ".\r\n":
                        eot = True
                    else:
                        # apply pattern to line
                        match = pattern.match(line)
                        if match:
                            if processor is None:
                                results.append([match.group(1), match.group(2), match.group(3), match.group(4)])
                            else:
                                processor(match.group(1), match.group(2), match.group(3), match.group(4))
                        else:
                            print("unexpected line in results: %s", line)

                    # remove line
                    line, self.data = self.data.split("\r\n", 1)

            # if we have not finished...
            if not eot:
                # receive more data from server
                self.data += self.s.recv(1024)

        # all went well, return true
        if processor is None:
            return results
        else:
            return True

    def post(self, fromheader, subjectheader, newsgroupsheader, article):
        """Post a binary article to a newsgroup.

        """

        # send the post command to the server
        self.send("POST")

        # get code 340 if we're ok to post
        if self.code != '340':
            return False

        self.s.sendall("From: " + fromheader + "\r\n")
        self.s.sendall("Subject: " + subjectheader + "\r\n")
        self.s.sendall("Newsgroups: " + newsgroupsheader + "\r\n")
        self.s.sendall("\r\n")
        self.s.sendall(article)

        # send our end of transmission character
        self.send(".")

        # get code 240 if the server accepted our post
        if self.code != '240':
            return False

        return True