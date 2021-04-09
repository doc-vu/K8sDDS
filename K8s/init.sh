#!/usr/bin/env bash

if [ "$1" = "weavenet" ]; then
    sudo kubeadm init
else
  sudo kubeadm init --pod-network-cidr=10.244.0.0/16
fi
