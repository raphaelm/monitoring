#!/usr/bin/env python3
"""
Monitor a mailserver checking sending and receiving. This makes it neccessary to
use two independent mailservers which exchange emails in both ways. This script
logs in to both of the hosts with SMTP and sends mails to the other host. On the
next run, it will login into both hosts via IMAP, checks whether the mails
arrived and delete them, while sending out the next pair of mails.
"""
import argparse
import socket
import time
from smtplib import SMTP

import nagiosplugin


class Twowaymail(nagiosplugin.Resource):
    def __init__(self, conn1, conn2):
        self.conn1 = conn1
        self.conn2 = conn2

    def send(self, conn, to):
        host = conn[0].split(":")[0]
        try:
            port = conn[0].split(":")[1]
        except IndexError:
            port = 587
        with SMTP(host, port) as smtp:
            print(smtp)
            if conn[5]:
                smtp.starttls()
                smtp.ehlo()
            smtp.login(conn[3], conn[4])
            smtp.sendmail(conn[2], to, """From: {fromaddr}
To: {toaddr}
Subject: Monitoring probe

Monitoring host: {monitorhost}
Sender host: {fromhost}
Unixtime: {unixtime}
KTHXBYE
                """.format(
                    fromaddr=conn[2],
                    toaddr=to,
                    monitorhost=socket.gethostname(),
                    fromhost=conn[0],
                    unixtime=time.time()
                )
            )

    def probe(self):
        # Send out mail probes
        self.send(self.conn1, self.conn2[2])
        self.send(self.conn2, self.conn1[2])
        return [nagiosplugin.Metric('mail', True, context='null')]


def main():
    argp = argparse.ArgumentParser(description=__doc__)
    argp.add_argument('-s1', '--smtp1', metavar='HOST', required=True,
                      help='SMTP Hostname for first host')
    argp.add_argument('-S1', '--nossl1', action='store_true', default=False,
                      help='Do not use SSL/STARTLS for first host')
    argp.add_argument('-i1', '--imap1', metavar='HOST', required=True,
                      help='IMAP Hostname for first host')
    argp.add_argument('-u1', '--user1', metavar='USER', required=True,
                      help='Username on first host')
    argp.add_argument('-p1', '--pass1', metavar='PASS', required=True,
                      help='Password on first host')
    argp.add_argument('-a1', '--addr1', metavar='MAIL', required=True,
                      help='Mail address on first host')
    argp.add_argument('-s2', '--smtp2', metavar='HOST', required=True,
                      help='SMTP Hostname on second host')
    argp.add_argument('-S2', '--nossl2', action='store_true', default=False,
                      help='Do not use SSL/STARTTLS for first host')
    argp.add_argument('-i2', '--imap2', metavar='HOST', required=True,
                      help='IMAP Hostname on second host')
    argp.add_argument('-u2', '--user2', metavar='USER', required=True,
                      help='Username on second host')
    argp.add_argument('-p2', '--pass2', metavar='PASS', required=True,
                      help='Password on second host')
    argp.add_argument('-a2', '--addr2', metavar='MAIL', required=True,
                      help='Mail address on second host')
    args = argp.parse_args()
    check = nagiosplugin.Check(
        Twowaymail(
            (args.smtp1, args.imap1, args.addr1, args.user1, args.pass1, not args.nossl1),
            (args.smtp2, args.imap2, args.addr2, args.user2, args.pass2, not args.nossl2)
        ),
    )
    check.main()

if __name__ == '__main__':
    main()
