#!/usr/bin/env python

import sys
import ConfigParser
import re
import socket
import time

class REMatcher(object):
    def __init__(self, matchstring):
        self.matchstring = matchstring

    def match(self,regexp):
        self.rematch = re.match(regexp, self.matchstring)
        return bool(self.rematch)

    def group(self,i):
        return self.rematch.group(i)

def check_tcp_port(address, port):
    s = socket.socket()
    try:
        s.connect((address, port))
        return True
    except socket.error, e:
        return False

def check_service(address, port, name):
    for attempt in range(20):
        if check_tcp_port(address, port):
            print "{0} is ready".format(name)
            return
        time.sleep(1)
    else:
        print "{0} is not available".format(name)
        return
    
reporting_cfg = ConfigParser.ConfigParser()
reporting_cfg.read("/cuckoo/conf/reporting.conf")

if reporting_cfg.get('mongodb', 'enabled') == 'yes':
    mongo_host = reporting_cfg.get('mongodb', 'host')
    mongo_port = int(reporting_cfg.get('mongodb', 'port'))
    check_service(mongo_host, mongo_port, "Mongo")

# TODO: add Elasticsearch check support
# if reporting_cfg.get('elasticsearch', 'enabled') == 'yes':
    # elasticsearch_hosts = reporting_cfg.get('elasticsearch', 'hosts')
    # elasticsearch_port = int(reporting_cfg.get('mongodb', 'port'))
    # check_service(mongo_host, mongo_port, "Mongo")

cuckoo_cfg = ConfigParser.ConfigParser()
cuckoo_cfg.read("/cuckoo/conf/cuckoo.conf")

database_connection =  cuckoo_cfg.get('database', 'connection')
m = REMatcher(database_connection)

if m.match(r"\w+://\w+:[^:@]+@([-A-Za-z0-9]+):(\d+)/\w+"):
    database_host = m.group(1)
    database_port = int(m.group(2))
    check_service(database_host, database_port, "Database")

sys.exit()
