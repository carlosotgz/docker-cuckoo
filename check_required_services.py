#!/usr/bin/env python

import sys
import ConfigParser
import re
import socket
import time
import requests
from psycopg2 import connect as postgres_connection

class REMatcher(object):
    def __init__(self, matchstring):
        self.matchstring = matchstring

    def match(self,regexp):
        self.rematch = re.match(regexp, self.matchstring)
        return bool(self.rematch)

    def group(self,i):
        return self.rematch.group(i)
"""
Knock a TCP port once per second, 20 seconds at most.
"""
def check_tcp_port(address, port, name):
    for attempt in range(20):
        s = socket.socket()
        try:
            s.connect((address, port))
            print "{0} is ready".format(name)
            s.close()
            return True
        except socket.error, e:
            time.sleep(1)
    else:
        print "{0} is not available".format(name)
        sys.exit(1)

"""
Check Elasticsearch health consulting its own endpoint for status information
It will wait for 60 seconds at most.
"""
def check_elasticsearch(address, port, user = None, password = None):
    url = 'http://{0}:{1}/_cat/health'.format(address, port)
    for attempt in range(60):
        try:
            r = requests.get(url)
            status = r.text.split()[3]
            if status == 'green' or status == 'yellow':
                print "Elasticsearch at {0}:{1} is ready".format(address, port)
                return
            else:
                time.sleep(1)
        except requests.exceptions.ConnectionError, e:
            time.sleep(1)
    else:
        print 'Elasticsearch is not available at {0}:{1}'.format(address, port)
        sys.exit(1)

"""
Check Postgres health performing a real connection to it, not just a TCP handshake.
It will wait for 20 seconds at most.
"""
def check_postgres(address, port, db, user, password):
    for attempt in range(20):
        try:
            conn = postgres_connection(host = address, port = port, dbname = db, user = user, password = password)
            print "Postgres is ready"
            conn.close()
            return
        except Exception as e:
            print e
            time.sleep(1)
    else:
        print 'Postgres is not available.'
        sys.exit(1)

cuckoo_cfg = ConfigParser.ConfigParser()
cuckoo_cfg.read("/cuckoo/conf/cuckoo.conf")

database_connection =  cuckoo_cfg.get('database', 'connection')
db = REMatcher(database_connection)

# Parse connection string. Port section can be omitted
if db.match(r"(\w+)://(\w+):([^:@]+)@([-A-Za-z0-9]+)(?::(\d+))?/(\w+)"):
    database_engine = db.group(1).lower()
    database_user = db.group(2)
    database_password = db.group(3)
    database_host = db.group(4)

    # Port might be missing. Checking, just in case adding default
    # values is necessary.
    if db.group(5):
        database_port = int(db.group(5))
    else:
        if database_engine == 'postgresql':
            database_port = 5432
        elif database_engine == 'mysql':
            database_port = 3306
    database_name = db.group(6)

    if database_engine == 'postgresql':
        check_postgres(database_host, database_port, database_name, database_user, database_password)

reporting_cfg = ConfigParser.ConfigParser()
reporting_cfg.read("/cuckoo/conf/reporting.conf")

if reporting_cfg.get('mongodb', 'enabled') == 'yes':
    mongo_host = reporting_cfg.get('mongodb', 'host')
    mongo_port = int(reporting_cfg.get('mongodb', 'port'))
    # Unfortunately, PyMongo does not differentiate between a success on TCP handshake
    # and a real session with MongoDB, so we use a simple TCP check.
    check_tcp_port(mongo_host, mongo_port, "Mongo")

if reporting_cfg.get('elasticsearch', 'enabled') == 'yes':
    # Remove spaces for further simplicity and convert to list
    elasticsearch_hosts = reporting_cfg.get('elasticsearch', 'hosts').replace(' ', '').split(',')
    for host in elasticsearch_hosts:
        elasticsearch_match = REMatcher(host)
        if elasticsearch_match.match(r"([-A-Za-z0-9.]+)(:(\d+))?"):
            elasticsearch_host = elasticsearch_match.group(1)
            if elasticsearch_match.group(3):
                elasticsearch_port = int(elasticsearch_match.group(3))
            else:
                elasticsearch_port = 9200
        check_elasticsearch(elasticsearch_host, elasticsearch_port)

sys.exit()
