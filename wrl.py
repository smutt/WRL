#!/usr/bin/python3

import sys
import datetime
import signal
import dns.resolver
import threading
import subprocess


#############
# CONSTANTS #
#############


DYING = False # Set to True when a kill signal has been received
WHOIS_BINARY = '/bin/whois'
TIMEOUT = 10 # How many seconds we wait for whois response before registering failure
TEST_STRINGS = ['Registry Expiry Date:', 'Domain Name:', 'Creation Date:', 'Created Date:'] # Strings we test for in registrant data
#TESTS = [['case-0',1,1], ['case-1',1800,12], ['case-2',900,12], ['case-3',15,240]] # Our test cases as ordered tuples of [test_case, delay, count]
TESTS = [['case-0',1,1], ['case-1',2,9], ['case-2',4,5], ['case-3',8,2]] # Our test cases as ordered tuples of [test_case, delay, count]
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
class wrlThr(threading.Thread):
  def __init__(self, server, domains, case, delay, cnt):
    self.server = self.canonicalServer(server)
    self.tld = server.split('.')[-1]
    self.desc = self.tld + '_' + case
    self.domains = domains
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
       who = whois(self.server, domain)
       if test(who, self.server, domain):
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
      if ts in rs:
        dbg(">whois -h " + server + " " + domain + " PASS\n" + rs)
        return True
  dbg(">whois -h " + server + " " + domain + " FAIL\n" + rs)
  return False


# Prints error and usage then exits
def usage(s):
  print(s)
  print("wrl.py CSV")
  exit(0)


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


# Check every 5 seconds to see if all threads dead
# When they're all dead euthanize
def hangout():
  if DYING:
    return

  if threading.active_count() > 2:
    t = threading.Timer(5, hangout)
    t.start()
  else:
    euthanize('END', None)


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

if DEBUG:
  df = open(DEBUG, 'w', 1)

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

  hangout()
