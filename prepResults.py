#!/usr/bin/env python

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
import argparse
import datetime
import re


ap = argparse.ArgumentParser(description='Process results files into CSV')
ap.add_argument(nargs='+', metavar='file', dest='infile', type=argparse.FileType('r'),
                  default=sys.stdin, help='Results input file if not using stdin')
ap.add_argument('-nf', '--total-nf', action='store_true', dest='nf', help='Total not FAILs')
ap.add_argument('-bt', '--by-tld', action='store_true', dest='byTLD', help='Register PASS/FAIL by TLD instead of WHOIS server')
ap.add_argument('-q', '--qh', action='store_true', dest='qh', help='Append queries/hour to output')
ap.add_argument('-p', '--period', nargs=1, metavar='period', dest='period',
                  type=int, default=None, required=False, help='Hardset time period in hours for all test cases')
args = ap.parse_args()


if args.nf:
  nf = {}
ts = {}
servers = {}
servers['header'] = ['tld_server', '0-pass', '0-fail', '0-noma',
                       '1-pass', '1-fail', '1-noma',
                       '2-pass', '2-fail', '2-noma',
                       '3-pass', '3-fail', '3-noma',
                       '4-pass', '4-fail', '4-noma',
                       '5-pass', '5-fail', '5-noma',
                       '6-pass', '6-fail', '6-noma',
                       '7-pass', '7-fail', '7-noma',
                       '8-pass', '8-fail', '8-noma']

for f in args.infile:
  for line in f.read().split('\n'):
    if len(line) > 0:
      if line.find('ActiveTestThreads') == -1:
        toks = line.split(' ')
        if args.byTLD:
          tld_server = toks[3].split('.')[1] + '_' + toks[2]
        else:
          tld_server = toks[2]

        if args.nf:
          if tld_server not in nf:
            nf[tld_server] = 0
          if toks[1].find('FAIL') == -1:
            nf[tld_server] += 1

        if tld_server not in servers:
          servers[tld_server] = []
          ts[tld_server] = []
          ts[tld_server].append(None)
          for ii in range(len(servers['header']) - 1):
            servers[tld_server].append(0)
            if not ii % 3:
              ts[tld_server].append(None)

        case = int(toks[4].split('case-')[1].split('.')[0])
        if not ts[tld_server][case]:
          ts[tld_server][case] = toks[0]
        if len(ts[tld_server]) == case + 2:
          ts[tld_server][case+1] = toks[0]

        if toks[1] == 'PASS':
          servers[tld_server][(case * 3) + 0] += 1
        elif toks[1] == 'NOMA':
          servers[tld_server][(case * 3) + 2] += 1
        else:
          servers[tld_server][(case * 3) + 1] += 1

rv = ''
for h in servers['header']:
  rv += h + ','
if args.qh:
  for ii in range((len(servers['header']) - 1) / 3):
    rv += str(ii) + '-q/h,'
if args.nf:
  rv += 'not-fails'
print(rv.strip(','))

p = re.compile('\d+') # Regex to split timestamps
for s in servers.iteritems():
  if s[0] == 'header':
    continue
  rv = s[0] + ','
  for c in s[1]:
    rv += str(c) + ','
  if args.qh:
    for ii in range(len(ts[s[0]]) - 1): # Handle query/hour calculations
      queries = int(sum(s[1][ii * 3: (ii * 3) + 3]) / len(args.infile))
      if args.period:
        qh = int(queries / args.period[0])
      else:
        if ts[s[0]][ii].find('/') == -1: # Old style dates, %H:%M:%S.%f
          fHour, fMinute, fSecond, fMs = map(int, p.findall(ts[s[0]][ii]))
          lHour, lMinute, lSecond, lMs = map(int, p.findall(ts[s[0]][ii+1]))
          first = datetime.datetime(2017, 01, 15, fHour, fMinute, fSecond, fMs)
          last = datetime.datetime(2017, 01, 15, lHour, lMinute, lSecond, lMs)
          if last > first:
            qh = int(queries / int((last - first).total_seconds() / 3600))
          else:
            qh = int(queries / int((86400 - (first - last).total_seconds()) / 3600))
        else: # New style dates, %m/%d/%H:%M:%S.%f
          fMonth, fDay, fHour, fMinute, fSecond, fMs = map(int, p.findall(ts[s[0]][ii]))
          lMonth, lDay, lHour, lMinute, lSecond, lMs = map(int, p.findall(ts[s[0]][ii+1]))

          first = datetime.datetime(2017, fMonth, fDay, fHour, fMinute, fSecond, fMs)
          last = datetime.datetime(2017, lMonth, lDay, lHour, lMinute, lSecond, lMs)
          qh = int(queries / (last - first).total_seconds() * 3600)
      rv += str(qh) + ','

  if args.nf:
    rv += str(nf[s[0]])
  print(rv.strip(','))
