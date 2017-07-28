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
#  Copyright (C) 2017, Andrew McConachie, <andrew.mcconachie@icann.org>

import os
import sys
import random
import dns.resolver

numTestDomains = 100
numTopTLDs = 100
ignoreDomains = ['com', 'net', 'jobs', 'cat', 'mil', 'edu', 'gov', 'int', 'arpa']
serverZone = '.ws.sp.am' # DNS Zone containing CNAME records pointing to whois FQDNs

def dbg(s):
#  print s
  pass

random.seed()
zFiles = os.listdir('zonefiles/')

#dbgFiles = 10 # How many files to read while developing this, remove when finished coding
tlds = []
for zf in zFiles:
#  if len(tlds) >= dbgFiles: # For developing, remove when finished coding
#    break

  dbg(zf)
  tld = {}
  if zf.find(".txt") == -1:
    dbg("This should not happen")
    continue

  zfh = open('zonefiles/' + zf, 'r')
  lines = zfh.read().splitlines()
  zfh.close()

  dbg("after file read")

  tld['name'] = lines[0].split(".")[0].strip()
  if tld['name'] in ignoreDomains:
    dbg("Ignoring:" + tld['name'])
    continue

  dbg("after name split")

  rrs = []
  for line in lines:
    rr = line.split("\t")
    rrs.append(rr)

  dbg("after rr split")

  ns = []
  for rr in rrs:
    if rr[3].lower() == 'ns':
      ns.append(rr[0].split(".")[0])

  dbg("after counting NS records")

  if len(ns) < numTestDomains:
    continue
  else:
    tld['size'] = len(ns)

  tld['domains'] = random.sample(ns, numTestDomains)
  for d in tld['domains']:
    dbg(d + "." + tld['name'])

  dbg(tld['name'] + ": " + str(tld['size']))
  tlds.append(tld)

tlds.sort(key=lambda tld: tld['size'], reverse=True)

for ii in xrange(numTopTLDs):
  # Find FQDN of whois server 
  d = dns.resolver.Resolver()
  try:
    resp = d.query(tlds[ii]['name'] + serverZone, 'CNAME')
    if len(resp.rrset) < 1:
      whois = 'UNKNOWN'
    else:
      whois = str(resp.rrset[0]).strip('.')
  except:
    whois = 'UNKNOWN'

  s = whois + ','
  for dom in tlds[ii]['domains']:
    s += dom + '.' + tlds[ii]['name'] + ','
  print s.strip(',')
