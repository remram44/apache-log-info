#!/usr/bin/env python

# This script is supposed to be executed right before logrotate
# moves/compresses/deletes the log file
# For example, put it in /etc/logrotate.d/httpd-prerotate/

from datetime import datetime, timedelta, tzinfo
import logging
import re
import sqlite3
import sys


logging.basicConfig(level=logging.DEBUG)


# Which log file to read (the one about to be log rotated)
LOGFILE = '/var/log/apache2/access.log'
# Which database to update
DATABASE = '/var/log/file_downloads.sqlite3'
# Regex that matches the request path; should have one capture, which is what
# gets inserted into the database's 'what' column
WHAT = r'^/downloads/([a-zA-Z0-9_-]+).(?:tar\.gz|tar\.bz2|zip|exe|msi)$'


class UTC(tzinfo):
    def utcoffset(self, dt):
        return timedelta(0)

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return timedelta(0)


utc = UTC()


def parse_date(s):
    if s[-5] in '-+':
        offset = (1, -1)[s[-5] == '-'] * int(s[-4:], 10)
        s = s[:-6]
    else:
        offset = 0
    dt = datetime.strptime(s, '%d/%b/%Y:%H:%M:%S')
    dt = dt + timedelta(seconds=offset)
    return dt.replace(tzinfo=utc)


def main():
    global LOGFILE, DATABASE
    if len(sys.argv) >= 2:
        LOGFILE = sys.argv[1]
    if len(sys.argv) >= 3:
        DATABASE = sys.argv[2]

    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row

    # 172.16.8.66 - - [23/May/2016:03:57:06 -0400] "GET /downloads/vistrails-2.2.4.tar.gz HTTP/1.1" 200 4242 "-" "python-requests/2.10.0"
    log_re = re.compile(r'^([0-9.:]+) [^ ]+ [^ ]+ \[([^\]]+)\] "GET ([^ ]+) HTTP/[0-9.]+" ([0-9]+) [0-9]+ ".+"$')
    what_re = re.compile(WHAT)
    results = []
    with open(LOGFILE, 'r') as fp:
        for line in fp:
            match = log_re.match(line)
            if match is not None:
                ip, timestamp, what, status = match.groups()
                timestamp = parse_date(timestamp)
                status = int(status, 10)
                what = what_re.match(what)
                if what is None:
                    continue
                what = what.group(1)
                results.append((timestamp, ip, what, status))

    db.executemany(
        '''
        INSERT INTO gets(timestamp, ip, what, status)
        VALUES(?, ?, ?, ?);
        ''',
        results)
    db.commit()
    db.close()


if __name__ == '__main__':
    main()
