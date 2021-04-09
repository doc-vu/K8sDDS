#!/bin/bash

for i in {1..10}; do
ssh pi$i 'docker rmi -f $(docker images -aq)'
done