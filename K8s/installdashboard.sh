#!/bin/bash
kubectl create ns kubernetes-dashboard
kubectl create secret generic kubernetes-dashboard-certs --from-file=certs -n kubernetes-dashboard
kubectl apply -f deploy/
kubectl apply -f access/
