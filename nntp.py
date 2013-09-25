"""simple-post

This is intended to be a very simple python NNTP posting application that can
be fully implemented within a single python file.
"""

import argparse
import sys

import nntp.nntp

# Begin configuration area

server = 'news.example.com'
port = 563
username = 'username'
password = 'password'
use_ssl = True

# End configuration area


if __name__ == '__main__':
    
    # argument parsing comes first
    parser = argparse.ArgumentParser(description="post a yEnc binary to a newsgroup group")

    group = parser.add_mutually_exclusive_group()
    group.add_argument("-v", "--verbose", help="increase output verbosity", action="store_true")
    group.add_argument("-q", "--quiet", help="disable output", action="store_true")

    #parser.add_argument("file", help="file(s) to post", nargs="+")
    parser.add_argument("-f", "--from", help="from line of the post")
    parser.add_argument("-s", "--subject", help="subject of the post")
    parser.add_argument("-n", "--newsgroups", help="newsgroup(s) to post to (comma seperated)")
    parser.add_argument("--host", help="hostname of server")
    parser.add_argument("--port", help="port for posting server", type=int)
    parser.add_argument("--ssl", help="use ssl for connecting to server", action="store_true")
    parser.add_argument("--user", help="username for posting server")
    parser.add_argument("--pass", help="password for posting server")
    parser.add_argument("--chars", help="set the max characters per line value")
    parser.add_argument("--size", help="set the max size of each part posted")
    args = parser.parse_args()
    
    # override any passed values
    if getattr(args, 'from'):
        fromAddress = getattr(args, 'from')
    if args.subject:
        subject = args.subject
    if args.newsgroups:
        newsgroups = args.newsgroups
    if args.host:
        server = args.host
    if args.port:
        port = args.port
    if args.ssl:
        use_ssl = True
    if args.user:
        username = args.user
    if getattr(args, 'pass'):
        password = getattr(args, 'pass')
    if args.chars:
        defaultCharsPerLine = args.chars
    if args.size:
        defaultPartSize = args.size
    
    # holds our files
    files = []
    
    # expand any patterns pass as files
    #for pattern in args.file:
    #    files += glob.glob(pattern)
    
    # connect to server
    conn = nntp.nntp.MyNntp(server, port, use_ssl)
    
    # check for failure
    if conn.connect() == False:
        print("Unable to connect to server.")
        sys.exit()
    
    # login to server
    if conn.login(username, password) == False:
        print("Unable to login to server.")
        sys.exit()

    # list newsgroups
    if conn.listactive() == False:
        print("Bad response!")