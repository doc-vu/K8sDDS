#!/bin/bash

num_workers=$1
for (( i = 1; i <= $num_workers; i++ )); do
    ssh pi$i "sudo reboot"
done
