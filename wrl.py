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
DEBUG_PREFIX = 'dbg_'
RESULTS_PREFIX = 'res_'

# 3 possible results for each test
TEST_FAIL = 0
TEST_PASS = 1
TEST_NOMATCH = 2

# Our test cases as ordered tuples of [test_case, delay, count]
#TESTS = [['case-0',1,1], ['case-1',1800,12], ['case-2',900,12], ['case-3',15,240]] # Our old case set
#TESTS = [['case-0',1,1], ['case-1',2,9], ['case-2',4,5], ['case-3',8,2]] # Useful for development
TESTS = [['case-0', 3600, 5],
           ['case-1', 1800, 5],
           ['case-2', 900, 16],
           ['case-3', 450, 32],
           ['case-4', 300, 24],
           ['case-5', 120, 60],
           ['case-6', 60, 60],
           ['case-7', 30, 60],
           ['case-8', 15, 120]]


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
       res = test(whois(self.server, domain), self.server, domain)
       if res == TEST_PASS:
         out("PASS " + logStr)
       elif res == TEST_NOMATCH:
         out("NOMA " + logStr)
       elif res == TEST_FAIL:
         out("FAIL " + logStr)

    except subprocess.TimeoutExpired as e:
      out("FAIL_timeout " + logStr)
      dbg(">whois -h " + self.server + " " + domain + " FAIL_timeout\nstdout:" + str(e.output))
    except subprocess.CalledProcessError as e:
      out("FAIL_whois_cmd " + logStr)
      dbg(">whois -h " + self.server + " " + domain + " FAIL_whois_cmd\nchild_exit_status:" + str(e.returncode) + " " + str(e.output))
    except:
      out("FAIL_general_child_exception " + logStr)
      dbg(">whois -h " + self.server + " " + domain + " FAIL_general_child_exception")
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


# Output a timestamped string
def out(s):
  if DYING:
    return

  dt = datetime.datetime.now()
  ts = dt.strftime("%H:%M:%S.%f")
  rf.write(ts + " " + str(s) + "\n")


# Dump debugging info to file
def dbg(s):
  if DYING:
    return
  
  df.write("\n\n" + str(s))


# Test if we are happy with returned results
# Takes a received string, a whois server, and the domain under test, returns TEST_PASS, TEST_FAIL or TEST_NOMATCH
def test(rs, server, domain):
  if len(rs) > 0:
    for ts in TEST_STRINGS:
      if ts in rs.lower() and domain in rs.lower():
        dbg(">whois -h " + server + " " + domain + " PASS_" + ts.replace(' ', '_').strip(':') + "\n" + rs)
        return TEST_PASS

    if "no match" in rs.lower() and domain in rs.lower():
      dbg(">whois -h " + server + " " + domain + " NOMA\n" + rs)
      return TEST_NOMATCH
      
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
    t = threading.Timer(sleepTime, runCases, args=[cases, subjects, max(int(sleepTime/2), TIMEOUT)])
    t.name = type(t).__name__ + "_runCases"
    t.start()
  else:
    if len(cases) > 0:
      for sub in subjects:
        WrlThr(sub[0], sub[1:], cases[0][0], cases[0][1], cases[0][2]).start()
      random.shuffle(subjects)
      runCases(cases[1:], subjects, int((cases[0][1] * cases[0][2] / 2) + TIMEOUT))
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

  # Close open files
  global df, rf
  df.close()
  rf.close()
  
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

  fname = sys.argv[1].split('.')[0] + "_" + datetime.datetime.now().strftime("%Y_%m_%d") + ".txt"
  
  df = open(DEBUG_PREFIX + fname, 'w', 1)
  rf = open(RESULTS_PREFIX + fname, 'w', 1)
  
  random.seed()
  subjects = []
  with open(sys.argv[1], 'r') as f:
    for line in f.read().split('\n'):
      if len(line) > 0:
        subjects.append(line.strip('\n').split(','))
  f.closed

  random.shuffle(subjects)
  runCases(TESTS, subjects, None)
