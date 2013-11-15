# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
import sys
import argparse
import logging
import logging.handlers
from settings import LOG_NAME
from daemon import Daemon


def main():
    pass

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Quantum network node cleaning tool.')
    parser.add_argument("-c", "--auth-config", dest="authconf", default="/root/openrc",
                        help="Authenticating config FILE", metavar="FILE")
    parser.add_argument("-l", "--log", dest="log", action="store",
                        help="log file or logging.conf location")
    parser.add_argument("-p", "--pid", dest="pid", action="store",
                        help="PID file", default="/tmp/{0}.pid".format(LOG_NAME))
    parser.add_argument("--retries", dest="retries", type=int, default=50,
                        help="try NN retries for OpenStack API call", metavar="NN")
    parser.add_argument("--sleep", dest="sleep", type=int, default=2,
                        help="sleep seconds between retries", metavar="SEC")
    parser.add_argument("--endpoint-type", dest="endpoint_type", action="store", default="admin",
                        help="Endpoint type ('admin' or 'public') for use.", metavar="TYPE")
    #parser.add_argument("--activeonly", dest="activeonly", action="store_true", default=False,
    #                    help="cleanup table only on active nodes")
    #parser.add_argument("--external-bridge", dest="external-bridge", default="br-ex",
    #                    help="external bridge name", metavar="IFACE")
    #parser.add_argument("--integration-bridge", dest="integration-bridge", default="br-int",
    #                    help="integration bridge name", metavar="IFACE")
    parser.add_argument("--ssh-username", dest="ssh_username", action="store", default='root',
                        help="Username for ssh connect", metavar="UNAME")
    parser.add_argument("--ssh-keyfile", dest="ssh_keyfile", action="append",
                        help="SSH key file", metavar="FILE")
    parser.add_argument("--ssh-port", dest="ssh_port", type=int, default=22,
                        help="Port for SSH connection", metavar="NN")
    parser.add_argument("--ssh-timeout", dest="ssh_timeout", type=int, default=120,
                        help="Timeout for SSH session", metavar="SEC")
    parser.add_argument("--noop", dest="noop", action="store_true", default=False,
                        help="do not execute, print to log instead")
    parser.add_argument("--debug", dest="debug", action="store_true", default=False,
                        help="debug")
    args = parser.parse_args()

    #setup logging
    if args.debug:
        _log_level = logging.DEBUG
    else:
        _log_level = logging.INFO
    if not args.log:
        # log config or file not given -- log to console
        LOG = logging.getLogger(LOG_NAME)   # do not move to UP of file
        _log_handler = logging.StreamHandler(sys.stdout)
        _log_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        LOG.addHandler(_log_handler)
        LOG.setLevel(_log_level)
    elif args.log.split(os.sep)[-1] == 'logging.conf':
        # setup logging by external file
        import logging.config
        logging.config.fileConfig(args.log)
        LOG = logging.getLogger(LOG_NAME)   # do not move to UP of file
    else:
        # log to given file
        LOG = logging.getLogger(LOG_NAME)   # do not move to UP of file
        LOG.addHandler(logging.handlers.WatchedFileHandler(args.log))
        LOG.setLevel(_log_level)

    LOG.info("Try to start daemon: {0}".format(' '.join(sys.argv)))
    cfg = vars(args)
    cfg['loglevel'] = _log_level
    daemon = Daemon(cfg, LOG_NAME)
    daemon.start()
    #cleaner = QuantumCleaner(get_authconfig(args.authconf), options=vars(args), log=LOG)
    #rc = 0
    #if vars(args).get('test-hostnames'):
    #    rc = cleaner.test_healthy(args.agent[0])
    #else:
    #    for i in args.agent:
    #        cleaner.do(i)
    #
    #LOG.debug("End.")
    sys.exit(0)
# vim: tabstop=4 shiftwidth=4 softtabstop=4