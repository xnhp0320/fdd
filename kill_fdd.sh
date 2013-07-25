#!/bin/bash

fdd_ps=`ps aux | grep fdd.py | grep -v grep`
pid=`echo $fdd_ps | gawk '{print $2}' `
echo $pid
kill $pid




