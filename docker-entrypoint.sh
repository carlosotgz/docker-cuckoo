#!/bin/sh

set -e

# Wait for required services based on Cuckoo's configuration files
/check_required_services.py

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
      cuckoo_config_dir="/cuckoo/conf/"
      # If machinery is VirtualBox, apply some tweaks in order to be able to use it from within the container
      if [ -n "$(grep -i -E "^\s*machinery\s*=\s*virtualbox\s*$" "${cuckoo_config_dir}/cuckoo.conf")" ]; then
        /virtualbox_tweaks.py
        if [ "$?" -eq 1 ]; then
          echo >&2 "[ERROR] SSH key cannot be found. Please specify one in order to reach VirtualBox at the host."
          exit 1
        else
          chmod 400 /cuckoo/key
        fi
      fi
      cd /cuckoo
      shift
      set -- su-exec cuckoo /sbin/tini -- cuckoo -d "$@"
      ;;
    submit )
      shift
      set -- su-exec cuckoo /sbin/tini -- cuckoo submit "$@"
      ;;
    api )
      set -- su-exec cuckoo /sbin/tini -- cuckoo api --host 0.0.0.0 --port 1337
      ;;
    web )
      set -- su-exec cuckoo /sbin/tini -- cuckoo web runserver 0.0.0.0:31337
      ;;
  esac
fi

exec "$@"
