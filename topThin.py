#!/usr/local/bin/python

import os
import json
import urllib2
from bs4 import BeautifulSoup

numRegs = 10
numDomains = 60

# Returns string between passed strings
def between(s, s1, s2):
  return s.split(s1)[1].split(s2)[0].strip()

cfgFile = open("config.json", "r")
cfg = json.load(cfgFile)
cfgFile.close()

sFile = open(cfg['data_file'], 'r')
soup = BeautifulSoup(sFile.read(), 'html.parser')
sFile.close()

details = []
ii = 0
for ll in soup.find_all('a'):
  if ll['href'].count('wsa/wsa_details_clean') == 0:
    continue

  ii += 1
  details.append(ll)
  if ii == numRegs:
    break

regs = []
for det in details:
  reg = {}
  reg['id'] = between(det['href'], 'wsa_details_clean/', '.html')
  soup = BeautifulSoup(urllib2.urlopen(cfg['url_base'] + det['href']).read(), 'html.parser')
  
  pre = soup.find('pre')
  reg['date'] = between(pre.text, "\nDate:", "\n").strip()
  reg['name'] = between(pre.text, "\nIANAID,name:", "\n").split(reg['id'])[1].strip()
  whois = between(pre.text, "\nWhoisServer:", ";\n").strip()
  reg['whois_fqdn'] = whois.split(" ")[0].strip()
  reg['whois_ip'] = between(pre.text, "(", ")").strip()

  reg['domains'] = []
  for ll in soup.find_all('a'):
    if ll['href'].count('/cgi/whois?d=') == 1:
      reg['domains'].append(ll['href'].split('whois?d=')[1])
  regs.append(reg)


# Just for debugging
#for reg in regs:
#  print "\n"
#  print "IANA ID:" + reg['id']
#  print "date:" + reg['date']
#  print "name:" + reg['name']
#  print "whois_fqdn:" + reg['whois_fqdn']
#  print "whois_ip:" + reg['whois_ip']
#  print "\nDOMAINS:"
#  for dom in reg['domains']:
#    print dom

# CSV = whois_fqdn, domain[0], domain[1], ...
for reg in regs:
  s = reg['whois_fqdn'] + ','
  for ii in xrange(min(len(reg['domains']), numDomains)):
    s += reg['domains'][ii] + ','
  print s.strip(',')
