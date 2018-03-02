#!/usr/bin/python

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
#  Copyright (C) 2018, Andrew McConachie, <andrew.mcconachie@icann.org>

import os
import sys
import random
import argparse
import signal
import dns.resolver

ap = argparse.ArgumentParser(description='Find second level domains based on dictionary words')
ap.add_argument('-w', '--words', dest='words', type=str, default='/usr/share/dict/words',
                  required=False, help='Dictionary File')
ap.add_argument('-d', '--domains', dest='numDomains', type=int,
                  required=True, help='Number of domains to find')
ap.add_argument('-t', '--tld', dest='tld', type=str,
                  required=True, help='TLD to search under')
ap.add_argument('-v', '--verbose', dest='verbose', action='store_true', default=False,
                  required=False, help='Verbose')

args = ap.parse_args()

DYING = False
numTestDomains = 100
serverZone = '.ws.sp.am' # DNS Zone containing CNAME records pointing to whois FQDNs
d = dns.resolver.Resolver()

# Die gracefully
def euthanize(signal, frame):
  global DYING
  DYING = True

signal.signal(signal.SIGINT, euthanize)
signal.signal(signal.SIGTERM, euthanize)
signal.signal(signal.SIGABRT, euthanize)
signal.signal(signal.SIGALRM, euthanize)
signal.signal(signal.SIGSEGV, euthanize)
signal.signal(signal.SIGHUP, euthanize)
  
# Get WHOIS server for TLD
try:
  resp = d.query(args.tld + serverZone, 'CNAME')
  if len(resp.rrset) < 1:
    whois = 'UNKNOWN'
  else:
    whois = str(resp.rrset[0]).strip('.')
except:
  whois = 'UNKNOWN'

# Get random words
random.seed()
wf = open(args.words, 'r')
ll = wf.read().splitlines()
random.shuffle(ll)
wf.close()

# Look for words in DNS
found = []
for word in ll:
  if DYING:
    break
  if len(found) == args.numDomains:
    break

  try:
    resp = d.query(word.strip() + '.' + args.tld, 'NS')
    if len(resp.rrset) >= 1:
      found.append(word)
      if args.verbose:
        print word
  except:
    pass

# Print it
rv = whois + ','
for out in found:
  rv += out + '.' + args.tld + ','

print rv.strip(',')
sys.exit(0)
