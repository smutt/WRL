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
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt

# Takes CSV data and an offset
# Returns percentages as a list of floats
def percs(data, offset):
  rv = {}
  for line in data[1:]:
    rv[line[0]] = []
    for ii in xrange(9):
      rv[line[0]].append(100 * (float(line[ii * 3 + offset]) / (int(line[ii * 3 + 1]) + int(line[ii * 3 + 2]) + int(line[ii * 3 + 3]))))
  return rv


if(len(sys.argv) < 2):
  print("Too few arguments")
  exit(1)
elif(len(sys.argv) > 2):
  print("Too many arguments")
  exit(1)
else:
  data = []
  with open(sys.argv[1], 'r') as f:
    for line in f.read().split('\n'):
      if len(line) > 0:
        data.append(line.strip('\n').split(','))
  f.closed

  percsPass = percs(data, 1)
  percsFail = percs(data, 2)
  percsNoma = percs(data, 3)

  xTicks = [1, 2, 4, 8, 12, 30, 60, 120, 240] # Queries per-hour
  legend = []
  fig, ax = plt.subplots()
  ax.set_xticks(xTicks)
  plt.figure(figsize=(15,10))
  for k,v in percs.iteritems():
    plt.plot(xTicks, v)
    legend.append(k)

  plt.legend(legend, loc=2, bbox_to_anchor=(1, 1))
  plt.savefig('wrl_1.png', pad_inches=0.1, bbox_inches='tight')
