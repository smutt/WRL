#!/usr/local/bin/python

import os
import json
import urllib2
from bs4 import BeautifulSoup

numRegs = 10

# Returns string between passed strings
def between(s, s1, s2):
  return s.split(s1)[1].split(s2)[0]

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

  reg['name'] = ''
  reg['whois_fqdn'] = ''
  reg['whois_ip'] = ''
  reg['domains'] = []
  soup = BeautifulSoup(urllib2.urlopen(cfg['url_base'] + det['href']).read(), 'html.parser')
  
  # Need code here to fill values

  for ll in soup.find_all('a'):
    if ll['href'].count('/cgi/whois?d=') == 1:
      reg['domains'].append(ll['href'].split('whois?d=')[1])
  regs.append(reg)
  
