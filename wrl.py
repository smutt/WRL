#!/usr/bin/python3

import sys
import datetime
import signal
import dns.resolver
import threading
import subprocess
import random


#############
# CONSTANTS #
#############


DYING = False # Set to True when a kill signal has been received
WHOIS_BINARY = '/bin/whois'
TIMEOUT = 10 # How many seconds we wait for whois response before registering failure
TEST_STRINGS = ['registry expiry date:', 'domain name:', 'creation date:', 'created date:'] # Strings we test for in registrant data
TESTS = [['case-0',1,1], ['case-1',1800,12], ['case-2',900,12], ['case-3',15,240]] # Our test cases as ordered tuples of [test_case, delay, count]
#TESTS = [['case-0',1,1], ['case-1',2,9], ['case-2',4,5], ['case-3',8,2]] # Our test cases as ordered tuples of [test_case, delay, count]
DEBUG='wrl_debug.txt'
#DEBUG=False

###########
# CLASSES #
###########

# Testing thread
# server = whois server FQDN
# domains = list of domains to test
# case = name of test case
# delay = delay between tests in seconds
# cnt = count of tests
class WrlThr(threading.Thread):
  def __init__(self, server, domains, case, delay, cnt):
    self.server = self.canonicalServer(server)
    self.tld = server.split('.')[-1]
    self.desc = self.server + '_' + case
    self.domains = domains
    random.shuffle(self.domains)
    self.case = case
    self.delay = delay
    self.cnt = cnt
    self.reps = 0

    #out("Starting thread " + type(self).__name__ + '_' + self.desc)
    threading.Thread.__init__(self, name=type(self).__name__ + '_' + self.desc)


  def run(self):
    domain = self.domains[self.reps % len(self.domains)]

    logStr = self.server + " " + domain + " " + self.case + "." + str(self.reps)
    try:
       if test(whois(self.server, domain), self.server, domain):
         out("Pass " + logStr)
       else:
         out("Fail " + logStr)
    except subprocess.TimeoutExpired:
      out("Fail_timeout " + logStr)
    except subprocess.CalledProcessError:
      out("Fail_whois_cmd " + logStr)
    except:
      out("Fail_general " + logStr)
      raise
    finally:
      self.reps += 1
      if self.reps < self.cnt:
        t = threading.Timer(self.delay, self.run)
        t.name = type(t).__name__ + "_" + self.desc
        t.start()


  # Discover canonical name of whois server
  def canonicalServer(self, server):
    d = dns.resolver.Resolver()
    try:
      resp = d.query(server, 'CNAME')
    except:
      return server

    if len(resp.rrset) < 1:
      return server
    else:
      return str(resp.rrset[0]).strip('.')


####################
# GLOBAL FUNCTIONS #
####################

# Call whois binary and returns output
def whois(server, domain):
  s = WHOIS_BINARY + ' -h ' + server + ' ' + domain
  return str(subprocess.check_output(s.split(), timeout=TIMEOUT, stderr=subprocess.STDOUT))
#  return "Test String Registry Expiry Date:"


# Output a timestamped string to console
def out(s):
  if DYING:
    return

  dt = datetime.datetime.now()
  ts = dt.strftime("%H:%M:%S.%f")
  print(ts + " " + str(s))


# Dump debugging info to file if DEBUG is set
def dbg(s):
  if DYING:
    return
  
  if DEBUG:
    df.write("\n\n" + str(s))


# Test if we are happy with returned results
# Takes a received string, a whois server, and the domain under test, returns boolean
def test(rs, server, domain):
  if len(rs) > 0:
    for ts in TEST_STRINGS:
      if ts in rs.lower():
        dbg(">whois -h " + server + " " + domain + " PASS\n" + rs)
        return True

    if 'no match' in rs.lower() and domain in rs.lower():
      dbg(">whois -h " + server + " " + domain + " PASS_nomatch\n" + rs)
      return True

  dbg(">whois -h " + server + " " + domain + " FAIL\n" + rs)
  return False


# Prints error and usage then exits
def usage(s):
  print(s)
  print("wrl.py CSV")
  exit(0)


# Run through our test cases
# Check every 10 seconds minimum if test cases are still running, if not start next case
def runCases(cases, subjects, sleepTime):
  if DYING:
    return

  activeTestThreads = 0
  for thr in threading.enumerate():
    if isinstance(thr, WrlThr) or isinstance(thr, threading.Timer):
      if thr.name != 'Timer_runCases':
        activeTestThreads += 1

  out("ActiveTestThreads:" + str(activeTestThreads))
  if activeTestThreads > 0:
    t = threading.Timer(sleepTime, runCases, args=[cases, subjects, max(int(sleepTime/2), 10)])
    t.name = type(t).__name__ + "_runCases"
    t.start()
  else:
    if len(cases) > 0:
      for sub in subjects:
        WrlThr(sub[0], sub[1:], cases[0][0], cases[0][1], cases[0][2]).start()
      random.shuffle(subjects)
      runCases(cases[1:], subjects, int((cases[0][1] * cases[0][2] / 2) + 10))
    else:
      euthanize('END', None)


# Die gracefully
def euthanize(signal, frame):
  print(str(signal) + " exiting")

  # Set global dying flag
  global DYING
  DYING = True
  
  # Kill all timer threads
  for thr in threading.enumerate():
    if isinstance(thr, threading.Timer):
      try:
        thr.cancel()
      except:
        pass

  # Close debug file if opened
  if DEBUG:
    global df
    df.close()

  sys.exit(0)


###################
# BEGIN EXECUTION #
###################

if(len(sys.argv) < 2):
  usage("Too few arguments")
elif(len(sys.argv) > 2):
  usage("Too many arguments")
else:
  signal.signal(signal.SIGINT, euthanize)
  signal.signal(signal.SIGTERM, euthanize)
  signal.signal(signal.SIGABRT, euthanize)
  signal.signal(signal.SIGALRM, euthanize)
  signal.signal(signal.SIGSEGV, euthanize)
  signal.signal(signal.SIGHUP, euthanize)

  if DEBUG:
    df = open(DEBUG, 'w', 1)

  random.seed()
  subjects = []
  with open(sys.argv[1], 'r') as f:
    for line in f.read().split('\n'):
      if len(line) > 0:
        subjects.append(line.strip('\n').split(','))
  f.closed

  random.shuffle(subjects)
  runCases(TESTS, subjects, None)
