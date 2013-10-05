# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import eventlet
eventlet.monkey_patch()
from daemonize_green import Daemonize
import re


def get_authconfig(cfg_file):
    """
    Read OS auth config file
    """
    rv = {}
    stripchars = " \'\""
    with open(cfg_file) as f:
        for line in f:
            rg = re.match(r'\s*export\s+(\w+)\s*=\s*(.*)', line)
            if rg:
                rv[rg.group(1).strip(stripchars)] = rg.group(2).strip(stripchars)
    return rv


class Daemon(Daemonize):
    """
    Main daemon class
    """
    def __init__(self, cfg, log_name, **kwargs):
        self.options = cfg
        self.auth_config = get_authconfig(cfg.get('authconf'))
        self.debug = cfg.get('debug')
        super(Daemon, self).__init__(log_name, cfg['pid'], **kwargs)
        self.logger.info("Daemon::init done, debug={}...".format(self.debug))

    def sigterm(self, signum, frame):
        # put Your ctuff here
        #
        #
        super(Daemon, self).__init__(signum, frame)

    def run(self):
        # get credentionals for access to the keystone
        # ask keystone API, get token
        # ask nova-api for list nodes
        # process nodes
        self.logger.info("Daemonized... run.method...")
        pass
# vim: tabstop=4 shiftwidth=4 softtabstop=4