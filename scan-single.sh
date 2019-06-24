#!/bin/bash

for x in `seq 1 3`;do
	python `pwd`/main.py $1 $x 2>/dev/null;
done
