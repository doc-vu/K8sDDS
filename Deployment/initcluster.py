# encoding: utf-8
# Author: Zhuangwei Kang
import sys
from constants import *
from kubernetes import client, config
import argparse

# Kubernetes API
config.load_kube_config(config_file='~/.kube/config')
apps_v1_api = client.AppsV1Api()
core_v1_api = client.CoreV1Api()


def list_nodes_name():
    master = []
    workers = []
    for node in core_v1_api.list_node().items:
        flag = False
        for label in node.metadata.labels:
            if 'master' in label:
                master.append(node.metadata.name)
                flag = True
                break
        if not flag:
            workers.append(node.metadata.name)
    return master, workers


def create_pod(node_selector, containers, pid=0, host_network=False):
    pod_name = list(node_selector.values())[0]
    if "pub" in pod_name:
        name = PERFTEST_PUB + str(pid)
    else:
        name = PERFTEST_SUB + str(pid)

    core_v1_api.create_namespaced_pod(
        namespace="default",
        body=client.V1Pod(
            api_version="v1",
            kind="Pod",
            metadata=client.V1ObjectMeta(
                name=name,
                namespace="default"
            ),
            spec=client.V1PodSpec(
                containers=containers,
                restart_policy="Never",
                node_selector=node_selector,
                volumes=[client.V1Volume(name="license-volume", config_map=client.V1ConfigMapVolumeSource(name=RTI_LICENSE))],
                host_network=host_network
            )
        ))

    print("Pod %s is created." % name)


class InitCluster(object):
    def __init__(self, num_pubs, num_subs):
        self.num_pubs = num_pubs
        self.num_subs = num_subs

    def main(self, cds, hostnetwork, secure, cosub, copub):
        master, workers = list_nodes_name()
        assert len(workers) >= self.num_pubs + self.num_subs/cosub

        # label pub nodes
        for i in range(min(len(workers), self.num_pubs)):
            core_v1_api.patch_node(name=workers[i], body={
                "metadata": {
                    "labels": {"perftest": "pub%d" % i}
                }
            })
        
        # environment variable
        env = [client.V1EnvVar(name="LD_LIBRARY_PATH", value="/app/lib")]
        if cds:
            cds_address = "rtps@%s:7400" % PERFTEST_CDS
            env.append(client.V1EnvVar(name="NDDS_DISCOVERY_PEERS", value=cds_address))
        
        # volume
        volume = [client.V1VolumeMount(name="license-volume", mount_path="/app/license")]

        if secure:
            image = PERFTEST_IMAGE.split(':')[0] + '-secure:latest'
        else:
            image = PERFTEST_IMAGE

        # create pub pods
        for i in range(self.num_pubs):
            containers = [
                client.V1Container(name=PERFTEST_PUB + str(i), image=image, image_pull_policy='Always',
                                   tty=True,
                                   env=env,
                                   volume_mounts=volume,
                                   command=['bash'])]
            create_pod(dict(perftest="pub%d" % i), containers, i, hostnetwork)

        if len(workers) < self.num_subs/cosub + self.num_pubs:
            print("There are %d nodes in your cluster, but %d pub and %d sub is going to be run, so some "
                  "pub and sub may run in the same node." %
                  (len(workers), self.num_subs, self.num_pubs))

        # label sub nodes
        for i in range(self.num_subs):
            core_v1_api.patch_node(name=workers[int(i/cosub) + self.num_pubs], body={
                "metadata": {
                    "labels": {"perftest": "sub%d" % int(i/cosub)}
                }
            })
        
        # create sub pods
        for i in range(self.num_subs):
            containers = [
                client.V1Container(name=PERFTEST_SUB + str(i), image=image, image_pull_policy='Always',
                                   tty=True,
                                   env=env,
                                   volume_mounts=volume,
                                   command=['bash'])]
            create_pod(dict(perftest="sub%d" % int(i/cosub)), containers, i, hostnetwork)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--cds', action='store_true', help='Set DDS CDS environment variable')
    parser.add_argument('--hostnetwork', action='store_true', help='Use hostnetwork')
    parser.add_argument('--secure', action='store_true', help='enable DDS security plugin')
    parser.add_argument('--cosub', type=int, default=1, help='consolidation ratio of subscribers')
    parser.add_argument('--copub', type=int, default=1, help='consolidation ratio of publishers')
    parser.add_argument('--numSubs', type=int, default=1, help='the number of subscribers')
    args = parser.parse_args()
    ic = InitCluster(1, args.numSubs)
    ic.main(args.cds, args.hostnetwork, args.secure, args.cosub, args.copub)

