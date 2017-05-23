#!/usr/bin/env python

import os
import shutil
import sys

# These are some Virtualbox workarounds and checks
virtualbox_cfg = ConfigParser.ConfigParser()
virtualbox_cfg.read("/cuckoo/conf/virtualbox.conf")

if cuckoo_cfg.get('cuckoo', 'machinery') == 'virtualbox':
    if os.path.exists('/key'):
        shutil.copyfile('/key', '/cuckoo/key')
    else:
        sys.exit(1)
    if not os.path.exists(virtualbox_cfg.get('virtualbox', 'path')):
        os.link('/wrapper.sh', virtualbox_cfg.get('virtualbox', 'path'))

sys.exit()
