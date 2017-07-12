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

WHOIS_BINARY = '/bin/whois'
TIMEOUT = 5 # How many seconds we wait for whois response before registering failure
#TESTS = [['case-0',1,1], ['case-1',1800,12], ['case-2',900,12], ['case-3',15,240]] # Our test cases as ordered tuples of [test_case, delay, count]
TESTS = [['case-0',1,1], ['case-1',2,9], ['case-2',4,5], ['case-3',8,2]] # Our test cases as ordered tuples of [test_case, delay, count]
#DEBUG='wrl.dbg'
DEBUG=False

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
    self.server = server
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
       if test(whois(self.server, domain)):
         out("Pass " + logStr)
       else:
         out("Fail " + logStr)
    except subprocess.TimeoutExpired:
      out("Fail_timeout " + logStr)
    except subprocess.CalledProcessError:
      out("Fail_process " + logStr)
    except:
      out("Fail_general " + logStr)
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
  return str(subprocess.check_output(s.split(), timeout=TIMEOUT))
#  return "Test String Registry Expiry Date:"


# Output a timestamped string
def out(s):
  dt = datetime.datetime.now()
  ts = dt.strftime("%H:%M:%S.%f")
  print(ts + " " + str(s))


# Dump debugging info to file if DEBUG is set
def dbg(s):
  if DEBUG:
    df.write("\n\n" + str(s))


# Test if we are happy with returned results
# Takes a string, returns boolean
def test(s):
  dbg(s)
  if len(s) > 0:
    if 'Registry Expiry Date:' in s:
      return True
  return False


# Prints error and usage then exits
def usage(s):
  print(s)
  print("wrl.py CSV")
  exit(0)


# Die gracefully
def euthanize(signal, frame):
  print(str(signal) + " exiting")

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
