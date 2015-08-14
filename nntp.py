"""simple-post

This is intended to be a very simple python NNTP posting application that can
be fully implemented within a single python file.
"""

import argparse
from dateutil import parser
import sys
import zlib

import nntp.nntp
import yEnc.Decoder

from sqlalchemy.orm import sessionmaker
from sqlalchemy import literal
import database

# Begin configuration area

server = 'news.example.com'
port = 563
username = 'username'
password = 'password'
use_ssl = True

# End configuration area


if __name__ == '__main__':
    
    # argument parsing comes first
    argparser = argparse.ArgumentParser(description="index the posts of a newsgroup group")

    group = argparser.add_mutually_exclusive_group()
    group.add_argument("-v", "--verbose", help="increase output verbosity", action="store_true")
    group.add_argument("-q", "--quiet", help="disable output", action="store_true")

    argparser.add_argument("-n", "--newsgroups", help="newsgroup(s) to index (comma separated)")
    argparser.add_argument("--host", help="server hostname")
    argparser.add_argument("--port", help="server port", type=int)
    argparser.add_argument("--ssl", help="use ssl for connecting to server", action="store_true")
    argparser.add_argument("--user", help="username for posting server")
    argparser.add_argument("--pass", help="password for posting server")
    args = argparser.parse_args()
    
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
    
    # get a nntp object
    conn = nntp.nntp.MyNntp(server, port, use_ssl)
    
    # connect to server
    print("Connecting to server...")
    if conn.connect():
        print("Connected to server...")
    else:
        print("Unable to connect to server.")
        sys.exit()
    
    # authenticate to server
    print("Authenticating...")
    if conn.login(username, password):
        print("Successfully authenticated...")
    else:
        print("Failed authentication...")
        print("Exiting...")
        sys.exit()

    Session = sessionmaker(bind=database.engine)
    session = Session()

    # list newsgroups
    print ("Listing newsgroups...")
    results = conn.listactive()
    if results is False:
        print("Listing newsgroups failure: Bad response!")
        print("Exiting...")

    for r in results:
        # add new entries
        try:
            existing = session.query(database.Groups).filter_by(name=r[0]).one()
        except:
            group = database.Groups(name=r[0])
            session.add(group)

    session.commit()

    print ("Listing complete... %d results..." % len(results))
    
    # group command
    print("Selecting active group...")
    if conn.group("alt.test"):
        print("Group command successful...")
    else:
        print("Group command failed...")

    # xover command
    # print("Sending XOver command...")
    # if conn.over():
    #     print("XOver command successful...")
    # else:
    #     print("XOver command failed...")

    # xzver command
    print("Sending Xzver command...")
    data = conn.zver(conn.group_low, conn.group_low+249999)
    if data:
        print("Xzver command successful...")
        d = yEnc.Decoder.Decoder(data)
        data = zlib.decompress(d.data, -15)

        for line in data.splitlines():

            f = line.split("\t")
            try:
                existing = session.query(database.Articles).filter_by(h_message_id=f[4]).one()
            except:
                article = database.Articles(
                    h_subject=f[1],
                    h_from=f[2],
                    h_date=parser.parse(f[3]),
                    h_message_id=f[4],
                    h_references=f[5],
                    h_bytes=int(f[6]),
                    h_lines=int(f[7])
                )
                session.add(article)

        session.commit()

    else:
        print("Xzver command failed...")

    # quit
    if conn.quit():
        print("Quit command successfull...")
    else:
        print("Quit command failed...")