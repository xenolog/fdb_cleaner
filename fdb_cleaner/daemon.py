# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from daemonize_green import Daemonize
from config import AuthConfig
from settings import LOG_NAME



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
    def __init__(self, cfg, log_name=LOG_NAME):
        self.options = cfg
        self.auth_config = AuthConfig.read(cfg.get('authconf'))
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
