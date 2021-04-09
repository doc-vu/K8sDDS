#!/bin/bash

# shellcheck disable=SC2034
cni=$1

# reset master
sudo kubeadm reset -f
sudo rm -r /etc/cni/net.d/* 
sudo rm -r $HOME/.kube/*

# reset workers
for i in {1..10} ; do
  ssh pi$i "sudo kubeadm reset -f"
  ssh pi$i "sudo rm -r /etc/cni/net.d/*"
  ssh pi$i "sudo rm -r $HOME/.kube/*"
  # clear perftest_cpp process
  ssh pi$i "pgrep perftest | sudo xargs kill"

  # clean remained ip interfaces
  if [ $cni == "flannel" ]; then
      ssh pi$i "sudo ip link delete cni0"
      ssh pi$i "sudo ip link delete flannel.1"
  elif [ $cni == "kube-router" ]; then
      ssh pi$i "sudo ip link delete kube-bridge"
      ssh pi$i "sudo ip link delete kube-ipvs0" 
      ssh pi$i "sudo ip link delete dummy0"
  elif [ $cni == "weavenet" ]; then
      ssh pi$i "sudo weave reset --force" 
      ssh pi$i "sudo ip link delete weave" 
      ssh pi$i "sudo rm /opt/cni/bin/weave-*"
  fi
done

if [ $cni == "flannel" ]; then
  sudo ip link delete cni0 
  sudo ip link delete flannel.1
elif [ $cni == "kube-router" ]; then
  sudo ip link delete kube-bridge
  sudo ip link delete kube-ipvs0
elif [ $cni == "weavenet" ]; then
  sudo weave reset --force 
  sudo ip link delete weave 
  sudo rm /opt/cni/bin/weave-*
fi
