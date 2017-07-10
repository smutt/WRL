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
#TESTS = [['case-1',1,1], ['case-2',1800,12], ['case-3',900,12], ['case-4',15,240]] # Our test cases as ordered tuples of [test_case, delay, count]
TESTS = [['case-0',1,1], ['case-1',60,10], ['case-2',9,12], ['case-3',15,15]] # Our test cases as ordered tuples of [test_case, delay, count]


###########
# CLASSES #
###########

# Chief testing thread
# server = whois server FQDN
# domains = list of domains to test
# case = name of test case
# delay = delay between tests in seconds
# cnt = count of tests
class wrlThr(threading.Thread):
  def __init__(self, server, domains, case, delay, cnt):
    self.server = server
    self.tld = server.split('.')[-1]
    self.desc = self.tld + '_' + case
    self.domains = domains
    self.case = case
    self.delay = delay
    self.cnt = cnt
    self.reps = 0

    #dbg("Starting thread " + type(self).__name__ + '_' + self.desc)
    threading.Thread.__init__(self, name=type(self).__name__ + '_' + self.desc)

  def run(self):
    domain = self.domains[self.reps % len(self.domains)]

    logStr = self.server + " " + domain + " " + self.case + "." + str(self.reps)
    try:
       if test(whois(self.server, domain)):
         dbg("Pass " + logStr)
       else:
         dbg("Fail " + logStr)
    except TimeoutExpired:
      dbg("Fail_timeout " + logStr)
    except E as e:
      dbg("Fail_error " + e.strerror + " " + logStr)
      raise
    finally:
      self.reps += 1
      if self.reps < self.cnt:
        t = threading.Timer(self.delay, self.run)
        t.start()

        
####################
# GLOBAL FUNCTIONS #
####################

# Call whois binary and returns output
def whois(server, domain):
  s = WHOIS_BINARY + ' -h ' + server + ' ' + domain
#  return subp.check_output(s.split(), timeout=TIMEOUT).strip()
  return "THIS IS TEST"


def dbg(s):
  dt = datetime.datetime.now()
  ts = dt.strftime("%H:%M:%S.%f")
  print(ts + " " + str(s))


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


# Die gracefulle
def euthanize(signal, frame):
  print("SIG " + str(signal) + " caught, exiting")

  # Kill all timer threads
  for thr in threading.enumerate():
    if isinstance(thr, threading.Timer):
      try:
        thr.cancel()
      except:
        pass

  sys.exit(0)


###################
# BEGIN EXECUTION #
###################

# Register some signals
signal.signal(signal.SIGINT, euthanize)
signal.signal(signal.SIGTERM, euthanize)
signal.signal(signal.SIGABRT, euthanize)
signal.signal(signal.SIGALRM, euthanize)
signal.signal(signal.SIGSEGV, euthanize)
signal.signal(signal.SIGHUP, euthanize)

if(len(sys.argv) < 2):
  usage("Too few arguments")
elif(len(sys.argv) > 2):
  usage("Too many arguments")
else:
  lines = []
  with open(sys.argv[1], 'r') as f:
    for line in f.read().split('\n'):
      if len(line) > 0:
        lines.append(line.strip('\n').split(','))
  f.closed
  
  for T in TESTS:
    for l in lines:
     wrlThr(l[0], l[1:], T[0], T[1], T[2]).start()
