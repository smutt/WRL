#!/usr/local/bin/python

import os
import sys

numTestDomains = 10
numTopTLDs = 10
ignoreDomains = ['com', 'net', 'jobs', 'cat', 'mil', 'edu', 'gov', 'int', 'arpa']

zFiles = os.listdir('zonefiles/')

tlds = []
for zf in zFiles:
  print zf
  tld = {}
  if zf.find(".txt") == -1:
    print "This should not happen"
    continue

  zfh = open('zonefiles/' + zf, 'r')
  lines = zfh.read().splitlines()
  zfh.close()

  tld['name'] = lines[0].split(".")[0].strip()
  if tld['name'] in ignoreDomains:
    print "Ignoring:" + tld['name']
    continue

  tld['rrs'] = []
  for line in lines:
    rr = line.split("\t")
    tld['rrs'].append(rr)
  
  tld['count'] = 0
  for rr in tld['rrs']:
    if rr[3].lower() == 'a' or rr[3].lower() == 'aaaa':
      tld['count'] += 1

  if tld['count'] == 0:
    continue
      
  print tld['name'] + ": " + str(tld['count'])
