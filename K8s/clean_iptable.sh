#!/bin/bash

for i in {1..10} ; do
  ssh pi$i "sudo iptables -F && sudo iptables -t nat -F && sudo iptables -t mangle -F && sudo iptables -X"
done