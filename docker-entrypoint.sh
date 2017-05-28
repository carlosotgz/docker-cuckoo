#!/bin/sh

set -e

# Wait for required services based on Cuckoo's configuration files
/check_required_services.py
if [ "$?" -eq 1 ]; then
  exit 1
fi

# Change the ownership of /cuckoo to cuckoo, but exclude configuration files
chown -R cuckoo:cuckoo $(ls /cuckoo/ | awk '{if($1 != "conf"){ print $1 }}') /tmp/ && chown cuckoo:cuckoo /cuckoo

# Add cuckoo as command if needed
if [ "${1:0:1}" = '-' ]; then
  cd /cuckoo/
  set -- su-exec cuckoo /sbin/tini -- cuckoo "$@"
fi

# Drop root privileges
if [ "$(id -u)" = '0' ]; then
  case "$1" in
    daemon )
      cd /cuckoo
      shift
      set -- su-exec cuckoo /sbin/tini -- cuckoo -d "$@"
      ;;
    rooter )
      set -- cuckoo rooter /tmp/cuckoo-rooter --service /etc/init.d/openvpn
      ;;
  esac
fi

exec "$@"
