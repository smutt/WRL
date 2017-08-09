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


# Prints error and usage then exits
def usage(s):
  print(s)
  print("prepResults.py FILES")
  exit(0)


if(len(sys.argv) < 2):
  usage("Too few arguments")
else:
  servers = {}
  servers['header'] = ['server', '0-pass', '0-fail', '0-noma',
                         '1-pass', '1-fail', '1-noma',
                         '2-pass', '2-fail', '2-noma',
                         '3-pass', '3-fail', '3-noma',
                         '4-pass', '4-fail', '4-noma',
                         '5-pass', '5-fail', '5-noma',
                         '6-pass', '6-fail', '6-noma',
                         '7-pass', '7-fail', '7-noma',
                         '8-pass', '8-fail', '8-noma']

  for arg in sys.argv[1:]:
    with open(arg, 'r') as f:
     for line in f.read().split('\n'):
       if len(line) > 0:
         if line.find('ActiveTestThreads') == -1:
           toks =line.split(' ')
           if toks[2] not in servers:
             servers[toks[2]] = []
             for ii in range(len(servers['header']) - 1):
               servers[toks[2]].append(0)

           case = int(toks[4].split('case-')[1].split('.')[0])
           if toks[1] == 'PASS':
             servers[toks[2]][(case * 3) + 0] += 1
           elif toks[1] == 'NOMA':
             servers[toks[2]][(case * 3) + 2] += 1
           else:
             servers[toks[2]][(case * 3) + 1] += 1

  rv = ''
  for h in servers['header']:
    rv += h + ','
  print(rv.strip(','))

  for s in servers.iteritems():
    if s[0] == 'header':
      continue
    rv = s[0] + ','
    for c in s[1]:
      rv += str(c) + ','
    print(rv.strip(','))

  
