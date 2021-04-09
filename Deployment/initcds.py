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


def list_deploys():
    deploys = []
    for deploy in apps_v1_api.list_namespaced_deployment(namespace="default").items:
        deploys.append(deploy.metadata.name)
    return deploys


def create_deployment(deployment):
    if deployment.metadata.name not in list_deploys():
        # Create deployment if not existing
        apps_v1_api.create_namespaced_deployment(body=deployment, namespace="default")
        print("Deployment %s created." % deployment.metadata.name)
    else:
        # otherwise patch the deployment
        apps_v1_api.patch_namespaced_deployment(name=deployment.metadata.name, namespace="default", body=deployment)
        print("Deployment %s patched." % deployment.metadata.name)


def list_services():
    services = []
    for svc in core_v1_api.list_namespaced_service(namespace="default").items:
        services.append(svc.metadata.name)
    return services


def create_cds_service(protocol):
    if PERFTEST_CDS not in list_services():
        body = client.V1Service(
            api_version="v1",
            kind="Service",
            metadata=client.V1ObjectMeta(name=PERFTEST_CDS, labels={"run": PERFTEST_CDS}),
            spec=client.V1ServiceSpec(
                selector={"run": PERFTEST_CDS},
                ports=[client.V1ServicePort(port=CDS_PORT, protocol=protocol)]))
        core_v1_api.create_namespaced_service(namespace="default", body=body)


def init_cds_deploy(transport='UDP', hostnetwork=False):
    cmd = ['./rticlouddiscoveryservice']
    if transport == 'TCP':
        cmd.extend(['-transport', 'tcpv4_lan:7400'])
    cds = client.V1Container(
        name="deployment",
        image=RTI_CDS_IMAGE,
        image_pull_policy="Always",
        tty=True,
        volume_mounts=[client.V1VolumeMount(name="license-volume", mount_path="/app/license")],
        ports=[client.V1ContainerPort(container_port=CDS_PORT, protocol=transport)],
        env=[client.V1EnvVar(name="ARGS", value="-verbosity 6"), 
             client.V1EnvVar(name='LD_LIBRARY_PATH', value='/app/lib')],
        command=cmd
    )

    # Template
    template = client.V1PodTemplateSpec(
        metadata=client.V1ObjectMeta(labels={"run": PERFTEST_CDS}),
        spec=client.V1PodSpec(
            containers=[cds],
            node_selector=dict(perftest="cds"),
            host_network=hostnetwork,
            volumes=[client.V1Volume(name="license-volume", config_map=client.V1ConfigMapVolumeSource(name=RTI_LICENSE))]))

    # Spec
    spec = client.V1DeploymentSpec(
        selector=client.V1LabelSelector(
            match_labels={"run": PERFTEST_CDS}), 
            replicas=1, template=template)

    # Deployment
    deployment = client.V1Deployment(
        api_version="apps/v1",
        kind="Deployment",
        metadata=client.V1ObjectMeta(name=PERFTEST_CDS),
        spec=spec)

    return deployment


def create_cds(transport='UDP', hostnetwork=False):
    master, _ = list_nodes_name()
    # label cds node (k8s master)
    core_v1_api.patch_node(name=master[0], body={
        "metadata": {
            "labels": {"perftest": "cds"}
        }
    })

    # create CDS deployment & config map for cds if not existing
    config_map_names = []
    for config_map in core_v1_api.list_namespaced_config_map(namespace="default").items:
        config_map_names.append(config_map.metadata.name)
    if RTI_LICENSE not in config_map_names:
        with open(RTI_LICENSE_FILE, "r") as f:
            license_data = f.read()
        config_map = client.V1ConfigMap(
            api_version="v1",
            kind="ConfigMap",
            data=dict(rti_license=license_data),
            metadata=client.V1ObjectMeta(name=RTI_LICENSE))
        core_v1_api.create_namespaced_config_map(namespace="default", body=config_map)

    create_deployment(init_cds_deploy(transport, hostnetwork))
    create_cds_service(transport)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--transport', choices=['UDP', 'TCP'], default='UDP', help='transport protocol')
    parser.add_argument('--hostnetwork', action='store_true', help='use hostnetwork')
    args = parser.parse_args()
    create_cds(args.transport, args.hostnetwork)
