# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from daemonize_green import Daemonize
import re


def get_authconfig(cfg_file):
    """
    Read OS auth config file
    cfg_file -- the path to config file
    """
    rv = {}
    stripchars = " \'\""
    with open(cfg_file) as f:
        for line in f:
            rg = re.match(r'\s*export\s+(\w+)\s*=\s*(.*)', line)
            if rg:
                rv[rg.group(1).strip(stripchars)] = rg.group(2).strip(stripchars)
    return rv


import random, time
def worker1(cls, n):
    w = int(random.random()*30)
    cls.logger.info(" task {} will be working while {} sec.".format(n,w))
    time.sleep(w)
    cls.logger.info("-task {} end of work.".format(n))


class Daemon(Daemonize):
    """
    Main daemon class
    """
    def __init__(self, cfg, log_name):
        self.options = cfg
        self.auth_config = get_authconfig(cfg.get('authconf'))
        self.debug = cfg.get('debug')
        self.loglevel = cfg.get('loglevel')
        super(Daemon, self).__init__(log_name, cfg['pid'], green_pool_size=2000)

    def run(self):
        # get credentionals for access to the keystone
        # ask keystone API, get token
        # ask nova-api for list nodes
        # process nodes
        for i in xrange(10000):
            self.green_pool.spawn_n(worker1, self, i)
            self.logger.info("+spawned: {}".format(i))
        self.green_pool.waitall()
        self.logger.info("*** end of work")
# vim: tabstop=4 shiftwidth=4 softtabstop=4
