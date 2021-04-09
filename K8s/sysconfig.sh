#!/bin/bash

num_workers=$1
for (( i = 1; i <= $num_workers; i++ )); do
    ssh pi$i "sudo swapoff -a"
    ssh pi$i "sudo mkdir /run/systemd/resolve/ && sudo ln -s /etc/resolv.conf /run/systemd/resolve/"
    ssh pi$i "sudo systemctl daemon-reload"
done
