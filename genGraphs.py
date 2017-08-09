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

import sys
import datetime
import argparse
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt


# Order of tuples in CSV input
PASS = 1
FAIL = 2
NOMA = 3


# Takes CSV data and an offset
# Returns percentages as a list of floats
def calcPercs(data, offset):
  rv = {}
  for line in data[1:]:
    rv[line[0]] = []
    for ii in xrange(9):
      rv[line[0]].append(100 * (float(line[ii * 3 + offset]) / (int(line[ii * 3 + 1]) + int(line[ii * 3 + 2]) + int(line[ii * 3 + 3]))))
  return rv


ap = argparse.ArgumentParser(description='Generate graphs from CSV files.')
ap.add_argument('-p', '--prefix', nargs=1, metavar='prefix', dest='prefix',
                  type=str, default=None, required=False, help='Output filename prefix')
ap.add_argument('-f', '--file', nargs=1, metavar='file', dest='infile',
                  type=argparse.FileType('r'), default=sys.stdin, required=False, help='CSV input file if not using stdin')
ap.add_argument('graph', choices=['pass', 'fail', 'noma'], help='Values to graph')
args = ap.parse_args()

if args.prefix == None:
  outFilePref = ''
else:
  outFilePref = args.prefix[0].strip('_').strip()
  
data = []
for line in args.infile.read().split('\n'):
  if len(line) > 0:
    data.append(line.strip('\n').split(','))
args.infile.closed

percs = {}
percs['pass'] = calcPercs(data, PASS)
percs['fail'] = calcPercs(data, FAIL)
percs['noma'] = calcPercs(data, NOMA)
#print("%_FAIL:" + repr(percs['fail']))

xTicks = [1.0, 2.0, 4.0, 8.0, 15.0, 30.0, 60.0, 120.0, 240.0] # Queries per-hour
legend = []
fig, ax = plt.subplots()
ax.set_xscale('log')
ax.set_xticks(xTicks)
ax.get_xaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
ax.set_xlabel("Queries / Hour (logN)")
ax.set_ylabel("% " + args.graph)

for k,v in percs[args.graph].iteritems():
  if sum(v) > 0:
    if min(v) != 100:
      ax.plot(xTicks, v)
      legend.append(k)
    else:
      print("100% " + args.graph + ":" + k)

ax.legend(legend, loc=2, bbox_to_anchor=(1, 1))
date = datetime.datetime.now().strftime("%Y_%m_%d")
fig.savefig(outFilePref + '_' + args.graph + '_' + date + '.png', pad_inches=0.1, bbox_inches='tight')
