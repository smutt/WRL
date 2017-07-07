#!/usr/bin/python3

import sys
import os
import datetime
import time
import signal
import dns.resolver
import threading
import subprocess as subp
import re

#############
# CONSTANTS #
#############

WHOIS_BINARY = '/bin/whois'
TIMEOUT = 5 # How many seconds we wait for whois response before registering failure

###########
# CLASSES #
###########

# Chief testing thread
# server == whois server FQDN
# domains == list of domains to test
# delay == delay between tests
# cnt == count of tests
class wrlThr(threading.Thread):
  def __init__(self, server, domains, delay, cnt):
    self.server = server
    self.domains = domains
    self.delay = delay
    self.cnt = min(cnt, len(domains))
    self.reps = 0

    dbgLog("Starting thread " + type(self).__name__ + '_' + self.server)
    threading.Thread.__init__(self, name=type(self).__name__ + '_' + self.server)

    
  def run(self):
    if reps == cnt:
      return

    logStr = self.server + " " + self.domains[cnt]
    try:
      data = whois(server, domains[cnt])
      if len(data) > 0: # This will likely need to get fancier
        dbgLog("Data returned " + logStr)
    except TimeoutExpired:
      dbgLog("Timeout expired " + logStr)
    except as e:
      dbgLog("Error " + e.strerror + " " + logStr)
      raise
    finally:
      reps += 1
      threading.Timer(self.delay, self.run)


####################
# GLOBAL FUNCTIONS #
####################

# Calls uci to get config vars
def whois(server, domain):
  s = WHOIS_BINARY + ' -h ' + server + ' ' + domain
  return subp.check_output(s.split(), timeout=TIMEOUT).strip()

def dbgLog(s):
  pass




###################
# BEGIN EXECUTION #
###################


