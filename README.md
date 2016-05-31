# apache-log-info

This is a really simple script that reads download data from an Apache2 log file and insert it into a SQLite3 database.

Currently, you'll need to create the database in advance. You can add other fields to be filled in later (as long as they are nullable) but you need at least the timestamp, ip, what, and status columns. For example:

```
sqlite3 /var/log/file_downloads.sqlite3 'CREATE TABLE gets(timestamp timestamp, ip text, what text, status integer);'
```
