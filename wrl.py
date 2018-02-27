#!/usr/bin/env python3

#  The file is part of the WRL Project.
#
#  The WRL Project is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  The WRL Project is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#  Copyright (C) 2017, Andrew McConachie, <andrew.mcconachie@icann.org>

import os
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
TIMEOUT = 10 # How many seconds we wait for whois response before registering failure
TEST_STRINGS = ['registry expiry date:', 'domain name:', 'creation date:', 'created date:'] # Strings we test for in registrant data
DEBUG_PREFIX = 'dbg_'
RESULTS_PREFIX = 'res_'
if os.uname().sysname.lower() == 'linux':
  WHOIS_BINARY = '/bin/whois'
elif os.uname().sysname.lower() == 'freebsd':
  WHOIS_BINARY = '/usr/bin/whois'

# 3 possible results for each test
TEST_FAIL = 0
TEST_PASS = 1
TEST_NOMATCH = 2

# Our test cases as ordered tuples of [test_case, delay, count]
#TESTS = [['case-0',1,1], ['case-1',1800,12], ['case-2',900,12], ['case-3',15,240]] # Our old case set
#TESTS = [['case-0',1,1], ['case-1',30,8], ['case-2',10,5], ['case-3',8,2]] # Useful for development
#TESTS = [['case-0', 3600, 5],   # 5 hours, 1q/h
#           ['case-1', 1800, 5], # 2.5 hours, 2q/h
#           ['case-2', 900, 16], # 4 hours, 4q/h
#           ['case-3', 450, 32], # 4 hours, 8q/h
#           ['case-4', 300, 24], # 2 hours, 12q/h
#           ['case-5', 120, 60], # 2 hours, 30q/h
#           ['case-6', 60, 60],  # 1 hour, 60q/h
#           ['case-7', 30, 60],  # 0.5 hours, 120q/h
#           ['case-8', 15, 120]] # 0.5 hours, 240q/h
                                # Total queries == 382
                                # Total time == 21.5 hours

#TESTS = [['case-0', 3600, 5],	# 5 hours, 1q/h
#           ['case-1', 1800, 10], # 5 hours, 2q/h
#           ['case-2', 900, 20],  # 5 hours, 4q/h
#           ['case-3', 450, 40],  # 5 hours, 8q/h
#           ['case-4', 240, 75],  # 5 hours, 15q/h
#           ['case-5', 120, 150], # 5 hours, 30q/h
#           ['case-6', 60, 300],  # 5 hour, 60q/h
#           ['case-7', 30, 600],  # 5 hours, 120q/h
#           ['case-8', 15, 1200]] # 5 hours, 240q/h
                                 # Total queries == 2,450
                                 # Total time == 45 hours

TESTS = [['case-0', 3600, 10],   # 10 hours, 1q/h
           ['case-1', 1800, 20], # 10 hours, 2q/h
           ['case-2', 900, 40],  # 10 hours, 4q/h
           ['case-3', 450, 80],  # 10 hours, 8q/h
           ['case-4', 240, 150], # 10 hours, 15q/h
           ['case-5', 120, 300], # 10 hours, 30q/h
           ['case-6', 60, 600],  # 10 hour, 60q/h
           ['case-7', 30, 1200], # 10 hours, 120q/h
           ['case-8', 15, 2400]] # 10 hours, 240q/h
                                 # Total queries == 4,900
                                 # Total time == 90 hours


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
      elif self.reps == self.cnt:
        t = threading.Timer(self.delay, lambda:None)
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
  ts = dt.strftime("%m/%d/%H:%M:%S.%f")
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

    if "domain not found" in rs.lower():
      dbg(">whois -h " + server + " " + domain + " NOMA\n" + rs)
      return TEST_NOMATCH

  dbg(">whois -h " + server + " " + domain + " FAIL\n" + rs)
  return TEST_FAIL


# Prints error and usage then exits
def usage(s):
  print(s)
  print("wrl.py CSV")
  exit(0)


# Run through our test cases
# Check every TIMEOUT seconds minimum if test cases are still running, if not start next case
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
      runCases(cases[1:], subjects, int((cases[0][1] * (cases[0][2] + 1) / 2) + TIMEOUT))
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

  fname = os.uname().nodename.split('.')[0] + "_" + sys.argv[1].split('.')[0] + "_" + datetime.datetime.now().strftime("%Y_%m_%d") + ".txt"

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
