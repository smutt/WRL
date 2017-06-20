#!/usr/local/bin/python

import os
import sys
import random

numTestDomains = 10
numTopTLDs = 10
ignoreDomains = ['com', 'net', 'jobs', 'cat', 'mil', 'edu', 'gov', 'int', 'arpa']

def dbg(s):
#  print s
  pass

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

  tld['rrs'] = []
  for line in lines:
    rr = line.split("\t")
    tld['rrs'].append(rr)

  dbg("after rr split")

  tld['ns'] = []
  for rr in tld['rrs']:
    if rr[3].lower() == 'ns':
      tld['ns'].append(rr[0].split(".")[0])

  dbg("after counting NS records")

  if len(tld['ns']) < numTestDomains:
    continue

  tld['domains'] = random.sample(tld['ns'], numTestDomains)
  for d in tld['domains']:
    dbg(d + "." + tld['name'])

  dbg(tld['name'] + ": " + str(len(tld['ns'])))
  tlds.append(tld)

tlds.sort(key=lambda tld: len(tld['ns']), reverse=True)

for tld in tlds:
  print  tld['name'] + " " + str(len(tld['ns']))
