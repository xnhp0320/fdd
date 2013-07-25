#!/bin/bash 


fdd_ps=`ps aux | grep fdd.py | grep -v grep`
mem=`echo $fdd_ps | gawk '{print $4}' `
echo $mem


