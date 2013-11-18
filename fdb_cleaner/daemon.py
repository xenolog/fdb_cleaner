# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import eventlet
eventlet.monkey_patch()
from keystoneclient.v2_0 import client as ks_client
try:
    from neutronclient.neutron import client as n_client
except ImportError:
    from quantumclient.quantum import client as n_client
from daemonize_green import Daemonize
from config import AuthConfig
from settings import LOG_NAME, API_VER
import sys
import os
import re
import random
import time
import paramiko


def execute_remote_command(cls, node_hash):
    # ssh to node
    cls.logger.info(" ssh to '{node}:{port}'".format(node=node_hash.get('host'), port=cls.options.get('ssh_port', '22')))
    ssh = paramiko.SSHClient()
    ssh.load_system_host_keys()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(
        node_hash.get('host'),
        port=cls.options.get('ssh_port') or None,
        username=cls.options.get('ssh_username'),
        password=cls.options.get('ssh_password') or None,
        timeout=cls.options.get('ssh_timeout') or None,
        key_filename=cls.options.get('ssh_keyfile') or None,
        #compress=False,
    )
    w = int(random.random() * 120)
    stdin, stdout, stderr = ssh.exec_command(
        "sleep {0} && echo {1} > /tmp/qqq-{2}.txt".format(w, node_hash.get('host'), os.getpid()),
        #timeout=0.0,  # for non-blocking mode (False -- for blocking mode)
        #get_pty=False
    )
    cls.logger.debug("session to '{node}' done.".format(node=node_hash.get('host')))


class Daemon(Daemonize):
    """
    Main daemon class
    """
    def __init__(self, cfg, logger=None, green_pool_size=2000):
        self.options = cfg
        self.auth_config = AuthConfig.read(cfg.get('authconf'))
        self.debug = cfg.get('debug')
        self.loglevel = cfg.get('loglevel')
        self.os_credentials = None
        self.keystone = None
        self.neutron = None
        super(Daemon, self).__init__(cfg['pid'], logger, green_pool_size=green_pool_size)

    def _get_keystone(self):
        if not (self.os_credentials is None):
            return self.os_credentials
        ret_count = self.options.get('retries', 50)
        while True:
            if ret_count <= 0:
                self.logger.error(">>> Keystone error: no more retries for connect to keystone server.")
                sys.exit(1)
            try:
                self.keystone = ks_client.Client(
                    username=self.auth_config.get('OS_USERNAME'),
                    password=self.auth_config.get('OS_PASSWORD'),
                    tenant_name=self.auth_config.get('OS_TENANT_NAME'),
                    auth_url=self.auth_config.get('OS_AUTH_URL')
                )
                break
            except Exception as e:
                errmsg = e.message.strip()
                if re.search(r"Connection\s+refused$", errmsg, re.I) or \
                        re.search(r"Connection\s+timed\s+out$", errmsg, re.I) or \
                        re.search(r"Service\s+Unavailable$", errmsg, re.I) or \
                        re.search(r"'*NoneType'*\s+object\s+has\s+no\s+attribute\s+'*__getitem__'*$", errmsg, re.I) or \
                        re.search(r"No\s+route\s+to\s+host$", errmsg, re.I):
                    self.logger.info(">>> Can't connect to {0}, wait for server ready..."
                                     .format(self.auth_config.get('OS_AUTH_URL')))
                    time.sleep(self.options.sleep)
                else:
                    self.logger.error(">>> Keystone error:\n{0}".format(e.message))
                    sys.exit(1)
            ret_count -= 1
        self.os_credentials = {
            'net_endpoint': self.keystone.service_catalog.url_for(
                service_type='network',
                endpoint_type=self.options.get('endpoint_type')
            ),
            'nova_endpoint': self.keystone.service_catalog.url_for(
                service_type='compute',
                endpoint_type=self.options.get('endpoint_type')
            ),
            'token': self.keystone.auth_token
        }

    def _get_neutron(self):
        if (self.os_credentials is None) or (self.os_credentials.get('net_endpoint') is None):
            self.logger.error("Neutron: credentials not given.")
            sys.exit(1)
        self.neutron = n_client.Client(
            API_VER,
            endpoint_url=self.os_credentials.get('net_endpoint'),
            token=self.os_credentials.get('token')
        )

    def _get_another_agents_list(self):
        #todo: catch some exceptions for retry
        return self.neutron.list_agents()

    def __run(self):
        time.sleep(60)
        self.remove_pidfile()

    def run(self):
        # get credentials
        self._get_keystone()
        # get neutron interface object
        self._get_neutron()
        # ask neutron-api for list nodes with have ovs-agent
        agents = self._get_another_agents_list()
        if type(agents) != type({}) or type(agents.get('agents')) != type([]):
            return None
        nodes = [i for i in agents.get('agents')
                 if i.get('agent_type') == 'Open vSwitch agent'
                    and i.get('alive')
                    and i.get('host') != os.getenv('HOSTNAME')
        ]
        # process nodes
        for node in nodes:
            self.logger.debug("+spawning: {0}".format(node.get('host')))
            self.green_pool.spawn_n(execute_remote_command, self, node)
            self.logger.debug("+spawned: {0}".format(node.get('host')))
        self.green_pool.waitall()
        self.logger.info("*** end of work")
        time.sleep(10)
        self.remove_pidfile()

# vim: tabstop=4 shiftwidth=4 softtabstop=4
