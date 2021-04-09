# Constants
PERFTEST_PUB = "rtiperftest-pub"
PERFTEST_SUB = "rtiperftest-sub"

RTI_LICENSE = "rti-license"
RTI_LICENSE_FILE = "rti_license.dat"
PERFTEST_CDS = "rti-clouddiscoveryservice"
CDS_PORT = 7400

PERFTEST_IMAGE = "zhuangweikang/rtiperftest-rp-plus:latest"
RTI_CDS_IMAGE = "zhuangweikang/rti-clouddiscoveryservice-plus:latest"

plugins = ['flannel-hostgw-udp', 'flannel-hostgw-dds-secure-udp', 'flannel-vxlan-udp', 'kube-router-udp', 'weavenet-udp', 'weavenet-udp-encryption', 'weavenet-udp-dds-secure', 'hostnetwork-udp']
# plugins = ['flannel-hostgw-tcp', 'flannel-vxlan-tcp', 'kube-router-tcp', 'weavenet-tcp', 'weavenet-tcp-encryption', 'hostnetwork-tcp']
# plugins = ['flannel-hostgw-udp', 'flannel-hostgw-tcp', 'flannel-vxlan-udp', 'flannel-vxlan-tcp', 'kube-router-udp', 'kube-router-tcp', \
#            'weavenet-udp', 'weavenet-tcp', 'weavenet-udp-encryption', 'hostnetwork-udp',  'hostnetwork-tcp']