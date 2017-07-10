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
TESTS = [[1,1], [1800,12], [900,12], [15,240]] # Our test cases as ordered tuples of [delay, count]

###########
# CLASSES #
###########

# Chief testing thread
# server == whois server FQDN
# domains == list of domains to test
# delay == delay between tests in seconds
# cnt == count of tests
class wrlThr(threading.Thread):
  def __init__(self, server, domains, delay, cnt):
    self.server = server
    self.domains = domains
    self.delay = delay
    self.cnt = min(cnt, len(domains))
    self.reps = 0

    dbg("Starting thread " + type(self).__name__ + '_' + self.server)
    threading.Thread.__init__(self, name=type(self).__name__ + '_' + self.server)


  def run(self):
    if reps == cnt:
      return

    logStr = self.server + " " + self.domains[cnt] + " d:" + str(self.delay) + " c:" + str(self.cnt)
    try:
       if test(whois(server, domains[cnt])):
         dbg("Pass " + logStr)
       else:
         dbg("Fail " + logStr)
    except TimeoutExpired:
      dbg("Fail_timeout " + logStr)
    except E as e:
      dbg("Fail_error " + e.strerror + " " + logStr)
      raise
    finally:
      reps += 1
      threading.Timer(self.delay, self.run)


####################
# GLOBAL FUNCTIONS #
####################

# Call whois binary and returns output
def whois(server, domain):
  s = WHOIS_BINARY + ' -h ' + server + ' ' + domain
  return subp.check_output(s.split(), timeout=TIMEOUT).strip()


def dbg(s):
  print(str(s))


# Test if we are happy with returned results
# Takes a string, returns boolean
def test(s):
  if len(s) > 0: # This will likely need to get fancier
    return True
  else:
    return False
  

# Prints error, then usage and exits
def usage(s):
  print(s)
  print("wrl.py CSV")
  exit(0)
  

###################
# BEGIN EXECUTION #
###################

if(len(sys.argv) < 2):
  usage("Too few arguments")
elif(len(sys.argv) > 2):
  usage("Too many arguments")
else:
  lines = []
  with open(sys.argv[1], 'r') as f:
    lines.append(f.read().split(','))
  f.closed

  for T in TESTS:
    for l in lines:
     wrlThr(l[0],l[1:], T[0], T[1]).start()
