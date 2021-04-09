#!/bin/bash

operation=$1
username=$2

init_time=()
reset_time=()
join_time=()
get_node_time=()

for i in {1..5} ; do
    if [ $operation == "init-reset" ]; then
        (time sudo kubeadm init --pod-network-cidr=10.244.0.0/16) &> timeInit-$i.tmp
        init_time+=($(grep "real" timeInit-$i.tmp))
        (time sudo kubeadm reset -f) &> timeReset-$i.tmp
        reset_time+=($(grep "real" timeReset-$i.tmp))
        docker rm $(docker ps -aq)
        docker rmi $(docker images -aq)
    elif [ $operation == "getNode" ]; then
        (time sudo kubeadm get node) &> timeGetNode-$i.tmp
        get_node_time+=($(grep "real" timeGetNode-$i.tmp))
    elif [ $operation == "join" ]; then
      join_cmd=$(sudo kubeadm token create --print-join-command)
      readarray workers < <(kubectl get nodes -o wide | awk '{print $6}' | tail -n +2)
      for worker in "${workers[@]}" ; do
        (time ssh $username@$worker "sudo $join_cmd") &> timeJoin-$worker.tmp
        join_time+=($(grep "real" timeJoin-$worker.tmp))
      done
    fi
done

printf "%s\n" "${init_time[@]}" > timeInitReset.out
printf "%s\n" "${reset_time[@]}" > timeReset.out
printf "%s\n" "${join_time[@]}" > timeJoin.out
printf "%s\n" "${get_node_time[@]}" > timeGetNode.out

rm *.tmp