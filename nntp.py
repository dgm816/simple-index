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
    parser = argparse.ArgumentParser(description="index the posts of a newsgroup group")

    group = parser.add_mutually_exclusive_group()
    group.add_argument("-v", "--verbose", help="increase output verbosity", action="store_true")
    group.add_argument("-q", "--quiet", help="disable output", action="store_true")

    parser.add_argument("-n", "--newsgroups", help="newsgroup(s) to index (comma separated)")
    parser.add_argument("--host", help="server hostname")
    parser.add_argument("--port", help="server port", type=int)
    parser.add_argument("--ssl", help="use ssl for connecting to server", action="store_true")
    parser.add_argument("--user", help="username for posting server")
    parser.add_argument("--pass", help="password for posting server")
    args = parser.parse_args()
    
    # override any passed values
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
    
    # get ourself a nntp object
    conn = nntp.nntp.MyNntp(server, port, use_ssl)
    
    # connect to server
    if conn.connect():
        print("Connected to server...")
    else:
        print("Unable to connect to server.")
        sys.exit()
    
    # authenticate to server
    if conn.login(username, password):
        print("Successfully authenticated...")
    else:
        print("Failed authentication...")
        print("Exiting...")
        sys.exit()

    # list newsgroups
    results = conn.listactive()
    if results is False:
        print("Listing newsgroups failure: Bad response!")
        print("Exiting...")

    for r in results:
        print r[0], " ", r[1], " ", r[2], " ", r[3]

    print ("Listing complete... %d results..." % len(results))