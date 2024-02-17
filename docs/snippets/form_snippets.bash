#!/bin/bash

# # choose your python flavor
# exe="python"
exe="python3"

# # list here your example snippets
codes="ping.py ping2.py ping_pong.py shm1.py shm2.py main1.py" 

for i in $codes
do
    echo $i
    $exe pyeval.py $i > $i"_"
done
