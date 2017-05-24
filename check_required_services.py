#!/usr/bin/env python

import sys
import ConfigParser
import re
import socket
import time
import requests

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
        return

cuckoo_cfg = ConfigParser.ConfigParser()
cuckoo_cfg.read("/cuckoo/conf/cuckoo.conf")

database_connection =  cuckoo_cfg.get('database', 'connection')
m = REMatcher(database_connection)

if m.match(r"\w+://\w+:[^:@]+@([-A-Za-z0-9]+):(\d+)/\w+"):
    database_host = m.group(1)
    database_port = int(m.group(2))
    check_service(database_host, database_port, "Database")

reporting_cfg = ConfigParser.ConfigParser()
reporting_cfg.read("/cuckoo/conf/reporting.conf")

if reporting_cfg.get('mongodb', 'enabled') == 'yes':
    mongo_host = reporting_cfg.get('mongodb', 'host')
    mongo_port = int(reporting_cfg.get('mongodb', 'port'))
    check_service(mongo_host, mongo_port, "Mongo")

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
