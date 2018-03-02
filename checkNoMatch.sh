#!/usr/bin/bash

for LL in `ls dbg_thi*_2017*.txt`; do echo $LL; grep PASS_no_match $LL |cut -c 2- |cut -d P -f 1|sh|grep -i "no match" ; done
