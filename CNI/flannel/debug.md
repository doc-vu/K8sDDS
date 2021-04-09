# IPSec backend
[link](https://github.com/coreos/flannel/issues/966)

I've run into this issue too. I too don't have a flannel.1 interface, but having studied the code and compared it to the vxlan backend code, it's clear that's deliberate. So I'm treating this issue as a generic "flannel ipsec doesn't work out of the box with Kubernetes" bug report, as per its title, which matches my experience.

In my case, everything comes up just fine and reports as healthy, but I can't connect to any services I deploy. Pod-to-pod networking works just fine, but node-to-pod networking does not.

I didn't find adding overlay IPs (as proposed above) to help. What worked for me was to add a route on masters:

```shell
route add -net 10.244.0.0 netmask 255.255.0.0 cni0
```

The resulting route table:

Kernel IP routing table
```shell
Kernel IP routing table
Destination     Gateway         Genmask         Flags Metric Ref    Use Iface
default         _gateway        0.0.0.0         UG    100    0        0 enp0s3
10.244.0.0      0.0.0.0         255.255.255.0   U     0      0        0 cni0
10.244.0.0      0.0.0.0         255.255.0.0     U     0      0        0 cni0
link-local      0.0.0.0         255.255.0.0     U     1000   0        0 enp0s3
172.17.0.0      0.0.0.0         255.255.0.0     U     0      0        0 docker0
192.168.88.0    0.0.0.0         255.255.255.0   U     100    0        0 enp0s3
```

Setup:

1. created a cluster via kubeadm init with the --pod-network-cidr=10.244.0.0/16 argument as per kubernetes docs for flannel
2. modified the kube-flannel.yaml manifest:
added --iface=enp0s8 to the kube-flannel container arguments
3. changed image to a locally built image since the quay.io image doesn't seem to have ipsec included
changed the kube-flannel-cfg configmap (PSK generated using dd as descibed in backends):
    ```shell
    dd if=/dev/urandom count=48 bs=1 status=none | xxd -p -c 48
    ```
    ```yaml
    net-conf.json: |
        {
        "Network": "10.244.0.0/16",
        "Backend": {
            "Type": "ipsec",
            "PSK": "ee9b0c24c5d015f4ed23e84fb1473314a8baa8bee65fcefd659981d59423c6ee718eee681f579cccf18fd5d7f759f736"
        }
        }
    ```