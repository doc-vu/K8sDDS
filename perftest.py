# encoding: utf-8
# Author: Zhuangwei Kang
import os
import time
import re
from constants import *
import pandas as pd
import subprocess
import multiprocessing
import argparse

executionTime = 120


def build_cmd(role, eid, kwargs, args):
    cmd = "./perftest_cpp -executionTime %d -cpu -nic eth0 " % executionTime
    if args.noPrint:
        cmd += "-noPrint "
    if args.transport == 'TCP':
        cmd += "-transport TCP "
    elif args.transport == 'TLS':
        cmd += "-transport TLS "
    elif args.transport == 'DTLS':
        cmd += '-transport DTLS '

    if args.latencyTest:
        cmd += "-latencyTest "
    
    if args.sleep != 0:
        cmd += '-sleep %d ' % args.sleep

    if args.encryptionLevel == 0:
        cmd += "-secureGovernanceFile ./resource/secure/signed_PerftestGovernance_RTPSSign.xml "
    if args.encryptionLevel == 1:
        cmd += "-secureGovernanceFile ./resource/secure/signed_PerftestGovernance_SignEncryptData.xml "
    elif args.encryptionLevel == 2:
        cmd += '-secureGovernanceFile ./resource/secure/signed_PerftestGovernance_SignEncryptSubmessage.xml '
    elif args.encryptionLevel == 3:
        cmd += '-secureGovernanceFile ./resource/secure/signed_PerftestGovernance_RTPSSignWithOrigAuthEncryptSubmessage.xml '
    elif args.encryptionLevel == 4:
        cmd += '-secureGovernanceFile ./resource/secure/signed_PerftestGovernance_RTPSEncrypt.xml '
    
    if args.secureSign:
        cmd += '-secureSign '

    if args.asynchronous or (kwargs['dataLen'] >= 16384 and args.transport=='DTLS'): # set dds.transport.DTLS.dtls1.parent.message_size_max = 65536
        cmd += "-asynchronous "

    if role == 'pub':
        cmd += '-pub -sendQueueSize %d ' % args.sendQueueSize
        if row['numSubscribers'] > 1:
            cmd += "-numSubscribers %d " % row['numSubscribers']
        if args.peers:
            # find all sub IP by pod name
            find_subs = "kubectl get pods -o wide | grep sub | awk ' { print $6 } '"
            all_subs = subprocess.check_output(find_subs, shell=True).decode().split('\n')[:-1]
            for i in range(row['numSubscribers']):
                cmd += '-peer %s ' % all_subs[i].strip()
    else:
        if eid > 0:
            cmd += "-numPublishers 1 -sidMultiSubTest %d " % eid

        if args.peers:
            # find all pub IP by pod name
            find_pubs = "kubectl get pods -o wide | grep pub | awk ' { print $6 } '"
            all_pubs = subprocess.check_output(find_pubs, shell=True).decode().split('\n')[:-1]
            for pub in all_pubs:
                if args.transport in ['TCP', 'TLS']:
                    cmd += '-peer %s:7400 ' % pub
                else:
                    cmd += '-peer %s ' % pub
                
    for key in kwargs:
        if type(kwargs[key]) is bool:
            if kwargs[key]:
                cmd += "-%s " % key
        else:
            if key == 'pubRate':
                # get 2 latency samples every second
                cmd += "-%s %s:sleep -latencyCount %s" % (key, str(kwargs[key]), str(int(kwargs[key]/2)))
            else:
                cmd += "-%s %s " % (key, str(kwargs[key]))
    return cmd


def monitor(log_path):
    with open(log_path, 'w') as f:
        f.write('name,cpu(cores),cpu%,memory(bytes),memory%\n')

    while True:
        cmd = 'kubectl top nodes --no-headers'
        metrics = subprocess.check_output(cmd, shell=True).decode().split('\n')
        metrics = [line.split(' ') for line in metrics if len(line)>0]
        metrics = list(map(lambda line: [item for item in line if len(item)>0], metrics))
        for i in range(len(metrics)):
            for j in range(1, len(metrics[i])):
                metrics[i][j] = re.sub("[^0-9]", "", metrics[i][j])
        metrics = pd.DataFrame(metrics)
        metrics.columns = metrics.iloc[0]
        metrics = metrics.drop(metrics.index[0])
        with open(log_path, 'a') as f:
            metrics.to_csv(f, index=None)
        time.sleep(5)


def execute(pod, perftest_cmd, test):
    retry_count = 0
    while retry_count < 5: 
        k8s_cmd = 'nohup kubectl exec -t %s -- %s > logs/%s/%s.log 2>&1 &' % (pod, perftest_cmd, test, pod)
        os.system(k8s_cmd)
        while not os.path.exists('logs/%s/%s.log' % (test, pod)):
            pass
        time.sleep(1)
        with open('logs/%s/%s.log' % (test, pod)) as f:
            if 'command terminated with exit code' in f.read():
                retry_count += 1
            else:
                break

def execute_baremetal(worker, participant, perftest_cmd, test):
    retry_count = 0
    perftest_cmd = ' '.join(perftest_cmd.split(' ')[1:]) + ' -qosFile app/perftest_qos_profiles.xml'
    cmd = 'nohup ssh %s "app/perftest_cpp %s" > logs/%s/%s.log 2>&1 &' % (worker, perftest_cmd, test, participant)
    while retry_count < 5: 
        os.system(cmd)
        while not os.path.exists('logs/%s/%s.log' % (test, participant)):
            pass
            time.sleep(1)
        with open('logs/%s/%s.log' % (test, participant)) as f:
            if 'command terminated with exit code' in f.read():
                retry_count += 1
            else:
                break


def process_monitor_data(test):
    df = pd.read_csv('logs/%s/metrics.csv' % test)
    df_mean = df.groupby(by=['name']).mean().round(2)
    df_mean.columns = [n+'(avg)' for n in df.columns[1:]]
    df_std = df.groupby(by=['name']).std().round(2)
    df_std.columns = [n+'(std)' for n in df.columns[1:]]
    df_95 = df.groupby(by=['name']).quantile(.95).round(2)
    df_95.columns = [n+'(95%)' for n in df.columns[1:]]
    df_90 = df.groupby(by=['name']).quantile(.9).round(2)
    df_90.columns = [n+'(90%)' for n in df.columns[1:]]
    df_80 = df.groupby(by=['name']).quantile(.8).round(2)
    df_80.columns = [n+'(80%)' for n in df.columns[1:]]
    df_50 = df.groupby(by=['name']).quantile(.5).round(2)
    df_50.columns = [n+'(50%)' for n in df.columns[1:]]
    df_max = df.groupby(by=['name']).max().round(2)
    df_max.columns = [n+'(max)' for n in df.columns[1:]]
    df_min = df.groupby(by=['name']).max().round(2)
    df_min.columns = [n+'(min)' for n in df.columns[1:]]
    df_mean.join(df_std).join(df_95).join(df_90).join(df_80).join(df_50).join(df_min).join(df_max).reset_index().to_csv('logs/%s/metrics.csv' % test, index=None)



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    # Benchmarking parameters
    parser.add_argument('--sch', type=str, default='schedule.csv', help='path of schedule file')
    parser.add_argument('--fromI', type=int, default=0, help='start test from specified index')
    parser.add_argument('--toI', type=int, default=100, help='end test at specified index')
    parser.add_argument('--monitor', action='store_true', help="enable node resource monitor")
    parser.add_argument('--baremetal', action='store_true', help='run perftest on baremetal')
    parser.add_argument('--pubHosts', type=str, default='', help='Publisher Host IP, seperate by comma.')
    parser.add_argument('--subHosts', type=str, default='', help='Subscriber Hosts IP, seperate by comma.')

    # RTI-Perftest parameters
    parser.add_argument('--domain', type=int, default=1, help='DDS domain ID')
    parser.add_argument('--latencyTest', action='store_true', help='run latency test')
    parser.add_argument('--noPrint', action='store_true', help='don\'t print perftest details')
    parser.add_argument('--sendQueueSize', type=int, default=50, help='publisher send queue size')
    parser.add_argument('--transport', type=str, choices=['UDP', 'TCP', 'TLS', 'DTLS'], default='UDP', help='the transport protocol will be used in the test')
    parser.add_argument('--peers', action='store_true', help='make participants find each other using peer address')
    parser.add_argument('--asynchronous', action='store_true', help='use asynchronous DataWriter')
    parser.add_argument('--encryptionLevel', choices=[0,1,2,3,4], type=int, help='encryption granularity -- 1. Encrypt topic (user) data | 2. Encrypt RTPS submessages | 3. Encrypt RTPS messages')
    parser.add_argument('--secureSign', action='store_true', help='Sign (HMAC) discovery and user data')
    parser.add_argument('--sleep', type=int, default=0, help='the length of sleep period between subsequent sends in ms')
    args = parser.parse_args()
    schedule = pd.read_csv(args.sch)

    for i, row in schedule.iterrows():
        if i < args.fromI or i > args.toI:
            continue
        start = time.time()
        print('test-%d started' % i)
        os.mkdir('logs/test-%d' % i)

        # start publisher
        perftest_cmd = build_cmd('pub', 0, row.to_dict(), args)
        participant = PERFTEST_PUB + '0'
        if args.baremetal:
            pubHost = args.pubHosts.split(',')[0]
            execute_baremetal(pubHost, participant, perftest_cmd, 'test-%d' % i)
        else:
            execute(participant, perftest_cmd, 'test-%d'%i)

        # start subscribers
        subHosts = args.subHosts.split(',')
        for j in range(row['numSubscribers']):
            perftest_cmd = build_cmd('sub', j, row.to_dict(), args)
            participant = PERFTEST_SUB + str(j)
            if args.baremetal:
                execute_baremetal(subHosts[j], participant, perftest_cmd, 'test-%d' % i)
            else:
                execute(participant, perftest_cmd, 'test-%d'%i)

        # start host cpu/memory monitor
        if args.monitor:
            monitor_proc = multiprocessing.Process(target=monitor, args=('logs/test-%d/metrics.csv' % i,))
            monitor_proc.start()
        
        time.sleep(1)
        while True:
            try:
                if args.baremetal:
                    host0 = args.pubHosts.split(',')[0]
                    pid = subprocess.check_output('ssh %s "pgrep perftest_cpp"' % host0, shell=True).decode()
                    if len(pid) == 0:
                        break
                    time.sleep(5)
                else:
                    subprocess.check_output('pgrep kubectl', shell=True)
            except:
                # test finished
                break
        
        if args.monitor:
            monitor_proc.terminate()
            process_monitor_data('test-%d' % i)
        print('test-%d end, elapsed time: %ss' % (i, time.time()-start))
        print('-------------------------')