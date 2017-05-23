#!/bin/sh
ssh -o StrictHostKeyChecking=no -i /cuckoo/key -o User="${HOST_USER:=root}" "${HOST_IP:=127.0.0.1}" "$0 $@"
