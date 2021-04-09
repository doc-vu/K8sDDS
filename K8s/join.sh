#!/usr/bin/env bash
num_worker=$1

for (( i = 1; i <= $num_worker; i++ )); do
    ssh pi$i "sudo $(sudo kubeadm token create --print-join-command)"
done
