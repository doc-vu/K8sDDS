#!/usr/bin/python3
# encoding: utf-8
# Author: Zhuangwei Kang
import matplotlib.pyplot as plt
from datapsr import *
import numpy as np


# Experiments Constants
baseline = ['hostnetwork-tcp', 'hostnetwork-udp']
base_plugins = ['flannel-hostgw', 'flannel-vxlan', 'kube-router', 'weavenet']
udp_plugins = ['%s-udp' % p for p in base_plugins]
tcp_plugins = ['%s-tcp' % p for p in base_plugins]

## Application-layer security plugins
udp_dds_secure_plugins = ['%s-dds-secure-udp' % p for p in base_plugins]
tcp_dds_secure_plugins = ['%s-dds-secure-tcp' % p for p in base_plugins]

## Transport-layer security plugins
tls_plugins = ['%s-tls' % p for p in base_plugins]
dtls_plugins = ['%s-dtls' % p for p in base_plugins]

## Overlay-layer security
overlay_sec_plugins = ['weavenet-encryption-udp', 'weavenet-encryption-tcp']

## Others
reliable_config = ['UDP-Reliable', 'TCP-BestEffort']
secure_reliable_config = ['TLS-BestEffort', 'TCP-BestEffort-WeaveEncrypt', 'TCP-BestEffort-DDS-Secure', 'UDP-Reliable-DDS-Secure', 'UDP-Reliable-WeaveEncrypt']
multicast_plugins = ['weavenet-udp', 'weavenet-encryption-udp', 'weavenet-dds-secure-udp', 'hostnetwork-udp']
data_len = [64, 256, 1024, 4096, 16384, 63000]
multisub_tests = [6, 8, 9, 10]
multicast_test = [12,13,14,15]
num_subs = [1,2,4,8]

# =====================================
# Matplotlib Constants
plt.rcParams['ytick.labelsize'] = 15
plt.rcParams['figure.figsize'] = (8, 5) 
plt.rcParams['axes.axisbelow'] = True
plt.rcParams['axes.labelsize'] = 15
plt.rcParams['xtick.labelsize'] = 15
plt.rcParams['legend.fontsize'] = 12
all_colors = ['#e6194B', '#3cb44b', '#4363d8', '#f58231', '#911eb4', '#800000', '#808000', '#42d4f4', '#f032e6', '#bfef45', '#fabed4', '#469990', '#dcbeff', '#9A6324', '#fffac8', '#aaffc3', '#ffd8b1', '#000075', '#a9a9a9','#000000']
# all_colors = ['C%d' %x for x in range(10)]


# =====================================
def plotThroughput(plugins, pp_latency=False):
    # dataLen test
    throughput_perf, latency_perf = load_data(range(len(data_len)), plugins, pp_latency)

    x_vals = np.arange(len(data_len))
    total_width, n = 0.8, len(plugins)
    width = total_width / n

    plt.xticks(range(len(data_len)), data_len)
    plt.ylim(0, 100)
    cell_text = []
    for i, cni in enumerate(plugins):
        throughput = throughput_perf[throughput_perf['cni'] == cni]['mbps(ave)']
        cell_text.append(['%.1f' % thr for thr in throughput])
        plt.plot(x_vals, throughput, label=cni, marker='*', color=all_colors[i])
        # plt.scatter(x, thr, s=10, color=all_colors[i])

    # Add a table at the bottom of the axes
    the_table = plt.table(cellText=cell_text,
                        rowLabels=plugins,
                        cellLoc='center',
                        rowColours=all_colors[:len(plugins)],
                        colLabels=data_len,
                        loc='bottom')
                        
    the_table.set_fontsize(15)
    the_table.scale(1, 1.5)
    # Adjust layout to make room for the table:
    plt.subplots_adjust(left=0.2, bottom=0.2)

    # plt.legend()
    # plt.xlabel('dataLen(B)')
    plt.ylabel('throughput(Mbps)', fontsize=15)
    plt.xticks([])
    plt.grid(axis='y', linestyle=':')
    plt.show()

    def get_overhead(transport):
        baseline_perf = throughput_perf[throughput_perf['cni'] == 'hostnetwork-%s' % transport]['mbps(ave)'].to_numpy()
        overheads = []
        for i, cni in enumerate(plugins):
            if 'hostnetwork' in cni:
                continue
            if transport in cni:
                perf = throughput_perf[throughput_perf['cni'] == cni]['mbps(ave)'].to_numpy()
                overheads.append(100 * (perf - baseline_perf)/baseline_perf)
    
        overheads = pd.DataFrame(overheads, columns=[str(dl) for dl in data_len], index=base_plugins)
        return overheads
    
    return get_overhead('udp'), get_overhead('tcp')


def plotCPU(plugins):
    throughput_perf, latency_perf = load_data(range(6), plugins)
    plt.xticks(range(len(data_len)), data_len)
    for i, cni in enumerate(plugins):
        cpu = throughput_perf[throughput_perf['cni'] == cni]['cpu'] * 4
        plt.plot(np.arange(6), cpu, label=cni, marker='*', color=all_colors[i])
    plt.legend(bbox_to_anchor=(0.5, 1.2), loc='center', ncol=3)
    plt.xlabel('dataLen(B)')
    plt.ylabel('CPU utilization rate(%)')
    plt.grid(axis='y', linestyle=':')
    plt.show()


def plotLoadLatency(plugins):
    throughput_perf, latency_perf = load_data(range(len(data_len)), plugins)
    plt.xticks(range(len(data_len)), data_len, rotation=0)
    for i, cni in enumerate(plugins):
        lat = latency_perf[latency_perf['cni'] == cni]['90%']
        plt.plot(np.arange(6), lat, label=cni, marker='.', color=all_colors[i])
    plt.legend(bbox_to_anchor=(0.5, 1.2), loc='center', ncol=3)
    plt.xlabel('dataLen(B)')
    plt.ylabel('90th latency(us)')
    plt.rc('axes', axisbelow=True)
    plt.grid(axis='y', linestyle=':')
    plt.show()


# reliability test
def plotReliableThroughput(plugins):
    udp_throughput_perf, _ = load_data([6], udp_plugins)
    udp_throughput_perf['test'] = 'UDP-Reliable'

    tcp_throughput_perf, _ = load_data([7], tcp_plugins)
    tcp_throughput_perf['test'] = 'TCP-BestEffort'

    throughput_perf = pd.concat([udp_throughput_perf, tcp_throughput_perf])
    throughput_perf = throughput_perf.reset_index(drop=True)

    x = np.arange(len(base_plugins))
    plt.xticks(x, base_plugins, rotation=30, ha='center')
    total_width, n = 0.8, len(reliable_config)
    width = total_width / n
    x = x - (total_width - width) / 2

    for i, l in enumerate(reliable_config):
        plt.bar(x+i*width, throughput_perf[(throughput_perf['test'] == l)]['mbps(ave)'], label=reliable_config[i], width=width)

    plt.legend(bbox_to_anchor=(0.5, 1.1), loc='center', ncol=2)
    # plt.xlabel('cni')
    plt.ylabel('throughput(Mbps)')
    plt.grid(axis='y', linestyle=':')
    plt.show()


def plotReliableCPU(plugins):
    udp_perf, _ = load_data([6], udp_plugins)
    udp_perf['test'] = 'UDP-Reliable'

    tcp_perf, _ = load_data([7], tcp_plugins)
    tcp_perf['test'] = 'TCP-BestEffort'

    perf = pd.concat([udp_perf, tcp_perf])
    perf = perf.reset_index(drop=True)

    x = np.arange(len(base_plugins))
    plt.xticks(x, base_plugins, rotation=30, ha='right')
    total_width, n = 0.8, len(reliable_config)
    width = total_width / n
    x = x - (total_width - width) / 2

    for i, l in enumerate(reliable_config):
        plt.bar(x+i*width, 4*perf[(perf['test'] == l)]['cpu'], label=reliable_config[i], width=width)

    plt.legend(bbox_to_anchor=(0.5, 1.1), loc='center', ncol=2)
    # plt.xlabel('cni')
    plt.ylabel('CPU Rate(%)')
    plt.grid(axis='y', linestyle=':')
    plt.show()


def plotReliablePingPongLatency(plugins):
    _, udp_perf = load_data([6], udp_plugins, latencyTest=True)
    udp_perf['test'] = 'UDP-Reliable'

    _, tcp_perf = load_data([7], tcp_plugins, latencyTest=True)
    tcp_perf['test'] = 'TCP-BestEffort'

    perf = pd.concat([udp_perf, tcp_perf])
    perf = perf.reset_index(drop=True)

    x = np.arange(len(base_plugins))
    plt.xticks(x, base_plugins, rotation=30, ha='right')
    total_width, n = 0.8, len(reliable_config)
    width = total_width / n
    x = x - (total_width - width) / 2

    for i, l in enumerate(reliable_config):
        plt.bar(x+i*width, perf[(perf['test'] == l)]['90%'], label=l, width=width)

    plt.legend(bbox_to_anchor=(0.5, 1.1), loc='center', ncol=2)
    # plt.xlabel('cni')
    plt.ylabel('90th Latency(us)')
    plt.grid(axis='y', linestyle=':')
    plt.show()



def plotSecureReliableThroughput(plugins):
    x = np.arange(len(base_plugins))
    plt.xticks(x, base_plugins, rotation=0, ha='center')

    udp_reliable_plugins = [p for p in plugins if 'dds-secure-udp' in p]
    udp_reliable_perf, _ = load_data([6], udp_reliable_plugins)
    udp_reliable_perf['test'] = 'UDP-Reliable-DDS-Secure'
    plt.scatter(x, udp_reliable_perf['mbps(ave)'], label='UDP-Reliable-DDS-Secure')

    tcp_besteffort_plugins = [p for p in plugins if 'dds-secure-tcp' in p]
    tcp_besteffort_perf, _ = load_data([7], tcp_besteffort_plugins)
    tcp_besteffort_perf['test'] = 'TCP-BestEffort-DDS-Secure'
    plt.scatter(x, tcp_besteffort_perf['mbps(ave)'], label='TCP-BestEffort-DDS-Secure')

    tls_besteffort_plugins = [p for p in plugins if 'tls' in p]
    tls_perf, _ = load_data([7], tls_besteffort_plugins)
    tls_perf['test'] = 'TLS-BestEffort'
    plt.scatter(x, tls_perf['mbps(ave)'], label='TLS-BestEffort')
    
    udp_reliable_weave = [p for p in plugins if 'encryption-udp' in p]
    udp_weave_perf, _ = load_data([6], udp_reliable_weave)
    udp_weave_perf['test'] = 'UDP-Reliable-WeaveEncrypt'
    plt.scatter([3], udp_weave_perf['mbps(ave)'], label='UDP-Reliable-WeaveEncrypt')

    tcp_besteffort_weave = [p for p in plugins if 'encryption-tcp' in p]
    tcp_weave_perf, _ = load_data([7], tcp_besteffort_weave)
    tcp_weave_perf['test'] = 'TCP-BestEffort-WeaveEncrypt'
    plt.scatter([3], tcp_weave_perf['mbps(ave)'], label='TCP-BestEffort-WeaveEncrypt')  

    plt.legend(bbox_to_anchor=(0.5, 1.15), loc='center', ncol=2)
    # plt.rcParams['lines.markersize'] = 15
    plt.ylabel('throughput(Mbps)')
    plt.grid(axis='y', linestyle=':')
    plt.show()


def plotSecureReliableCPU(plugins):
    x = np.arange(len(base_plugins))
    plt.xticks(x, base_plugins, rotation=0, ha='center')

    udp_reliable_plugins = [p for p in plugins if 'dds-secure-udp' in p]
    udp_reliable_perf, _ = load_data([6], udp_reliable_plugins)
    udp_reliable_perf['test'] = 'UDP-Reliable-DDS-Secure'
    plt.scatter(x, 4*udp_reliable_perf['cpu'], label='UDP-Reliable-DDS-Secure')

    tcp_besteffort_plugins = [p for p in plugins if 'dds-secure-tcp' in p]
    tcp_besteffort_perf, _ = load_data([7], tcp_besteffort_plugins)
    tcp_besteffort_perf['test'] = 'TCP-BestEffort-DDS-Secure'
    plt.scatter(x, 4*tcp_besteffort_perf['cpu'], label='TCP-BestEffort-DDS-Secure')

    tls_besteffort_plugins = [p for p in plugins if 'tls' in p]
    tls_perf, _ = load_data([7], tls_besteffort_plugins)
    tls_perf['test'] = 'TLS-BestEffort'
    plt.scatter(x, 4*tls_perf['cpu'], label='TLS-BestEffort')
    
    udp_reliable_weave = [p for p in plugins if 'encryption-udp' in p]
    udp_weave_perf, _ = load_data([6], udp_reliable_weave)
    udp_weave_perf['test'] = 'UDP-Reliable-WeaveEncrypt'
    plt.scatter([3], 4*udp_weave_perf['cpu'], label='UDP-Reliable-WeaveEncrypt')

    tcp_besteffort_weave = [p for p in plugins if 'encryption-tcp' in p]
    tcp_weave_perf, _ = load_data([7], tcp_besteffort_weave)
    tcp_weave_perf['test'] = 'TCP-BestEffort-WeaveEncrypt'
    plt.scatter([3], 4*tcp_weave_perf['cpu'], label='TCP-BestEffort-WeaveEncrypt')  

    plt.legend(bbox_to_anchor=(0.5, 1.15), loc='center', ncol=2)
    # plt.rcParams['lines.markersize'] = 15
    plt.ylabel('CPU Rate(%)')
    plt.grid(axis='y', linestyle=':')
    plt.show()


def plotSecureReliablePingPongLatency(plugins):
    x = np.arange(len(base_plugins))
    plt.xticks(x, base_plugins, rotation=0, ha='center')

    udp_reliable_plugins = [p for p in plugins if 'dds-secure-udp' in p]
    _, udp_reliable_perf = load_data([6], udp_reliable_plugins, latencyTest=True)
    udp_reliable_perf['test'] = 'UDP-Reliable-DDS-Secure'
    plt.scatter(x, udp_reliable_perf['90%'], label='UDP-Reliable-DDS-Secure')

    tcp_besteffort_plugins = [p for p in plugins if 'dds-secure-tcp' in p]
    _, tcp_besteffort_perf = load_data([7], tcp_besteffort_plugins, latencyTest=True)
    tcp_besteffort_perf['test'] = 'TCP-BestEffort-DDS-Secure'
    plt.scatter(x, tcp_besteffort_perf['90%'], label='TCP-BestEffort-DDS-Secure')

    tls_besteffort_plugins = [p for p in plugins if 'tls' in p]
    _, tls_perf = load_data([7], tls_besteffort_plugins, latencyTest=True)
    tls_perf['test'] = 'TLS-BestEffort'
    plt.scatter(x, tls_perf['90%'], label='TLS-BestEffort')
    
    udp_reliable_weave = [p for p in plugins if 'encryption-udp' in p]
    _, udp_weave_perf = load_data([6], udp_reliable_weave, latencyTest=True)
    udp_weave_perf['test'] = 'UDP-Reliable-WeaveEncrypt'
    plt.scatter([3], udp_weave_perf['90%'], label='UDP-Reliable-WeaveEncrypt')

    tcp_besteffort_weave = [p for p in plugins if 'encryption-tcp' in p]
    _, tcp_weave_perf = load_data([7], tcp_besteffort_weave, latencyTest=True)
    tcp_weave_perf['test'] = 'TCP-BestEffort-WeaveEncrypt'
    plt.scatter([3], tcp_weave_perf['90%'], label='TCP-BestEffort-WeaveEncrypt')  

    plt.legend(bbox_to_anchor=(0.5, 1.15), loc='center', ncol=2)
    # plt.rcParams['lines.markersize'] = 15
    plt.ylabel('90th Latency(us)')
    plt.grid(axis='y', linestyle=':')
    plt.show()


def plotBestEffortThroughput(plugins):
    throughput_perf, _ = load_data([7], plugins)

    # reliability test
    x = np.arange(len(base_plugins))
    total_width, n = 0.8, 2
    width = total_width / n
    plt.xticks(x, base_plugins, rotation=30, ha='right')
    x = x - (total_width - width) / 2

    udp_perf = throughput_perf[throughput_perf['cni'].str.contains('udp')]['mbps(ave)']
    tcp_perf = throughput_perf[throughput_perf['cni'].str.contains('tcp')]['mbps(ave)']

    plt.bar(x, udp_perf, label='UDP', width=width)
    plt.bar(x+width, tcp_perf, label='TCP', width=width)

    plt.legend()
    plt.ylabel('mbps(ave)')
    plt.grid(axis='y', linestyle=':')
    plt.show()


def plotBestEffortSecureThroughput(plugins):
    throughput_perf, _ = load_data([7], plugins)

    # reliability test
    x = np.arange(len(base_plugins)+1)
    plt.xticks(x, base_plugins+['WeaveEncrypt'], rotation=30, ha='center')

    udp_perf = throughput_perf[throughput_perf['cni'].str.contains('udp')]['mbps(ave)']
    plt.scatter(x, udp_perf, label='UDP')

    tcp_perf = throughput_perf[throughput_perf['cni'].str.contains('tcp')]['mbps(ave)']
    plt.scatter(x, tcp_perf, label='TCP')

    tls_perf = throughput_perf[throughput_perf['cni'].str.contains('tls')]['mbps(ave)']
    plt.scatter(x[:-1], tls_perf, label='TLS')

    plt.legend()
    plt.ylabel('mbps(ave)')
    plt.grid(axis='y', linestyle=':')
    plt.show()


def plotMultiSubThroughput(plugins):
    # numSubscriber unicast test
    throughput_perf, _ = load_data(multisub_tests, plugins)
    x = np.arange(4)
    plt.xticks(x, num_subs, rotation=0)
    for i, cni in enumerate(plugins):
        thr = throughput_perf[throughput_perf['cni'] == cni]['mbps(ave)']
        plt.plot(x, thr, label=cni, marker='.', color=all_colors[i])
    plt.legend(bbox_to_anchor=(0.5, 1.15), loc='center', ncol=3)
    plt.xlabel('numSubscribers')
    plt.ylabel('unicast throughput(Mbps)')
    plt.rc('axes', axisbelow=True)
    plt.grid(axis='y', linestyle=':')
    plt.show()


def plotMultiSubLatency(plugins):
    # numSubscriber unicast test
    _, latency_perf = load_data(multisub_tests, plugins)
    x = np.arange(4)
    plt.xticks(x, num_subs, rotation=0)
    for i, cni in enumerate(plugins):
        lat = latency_perf[latency_perf['cni'] == cni]['90%']
        plt.plot(x, lat, label=cni, marker='.', color=all_colors[i])
    plt.legend(bbox_to_anchor=(0.5, 1.15), loc='center', ncol=3)
    plt.xlabel('numSubscribers')
    plt.ylabel('90th latency(us)')
    plt.grid(axis='y', linestyle=':')
    plt.show()


def plotBatchingThroughput(plugins):
    # batching test
    udp_throughput_perf, _ = load_data([11], udp_plugins + udp_dds_secure_plugins)
    to_raw_cni = lambda my_cnis: ['-'.join(c.split('-')[:-1]) for c in my_cnis]
    udp_throughput_perf['cni'] = to_raw_cni(udp_throughput_perf['cni'])
    udp_throughput_perf['test'] = 'UDP'

    tcp_throughput_perf, _ = load_data([11], tcp_plugins + tcp_dds_secure_plugins)
    tcp_throughput_perf['cni'] = to_raw_cni(tcp_throughput_perf['cni'])
    tcp_throughput_perf['test'] = 'TCP'

    tls_perf, _ = load_data([11], tls_plugins)
    tls_perf['cni'] = to_raw_cni(tls_perf['cni'])
    tls_perf['test'] = 'TLS'

    throughput_perf = pd.concat([udp_throughput_perf, tcp_throughput_perf, tls_perf])
    throughput_perf = throughput_perf.reset_index()

    x = np.arange(len(raw_cnis))
    total_width, n = 0.8, 2
    width = total_width / n
    x = x - (total_width - width) / 2

    labels = ['UDP', 'TCP', 'TLS']
    plt.xticks(range(len(plugins)), raw_cnis, rotation=30, ha='right')
    plt.ylim(0, 100)
    for i, l in enumerate(labels):
        thr = []
        for cni in raw_cnis:
            tmp = throughput_perf[(throughput_perf['test'] == l) & (throughput_perf['cni'] == cni)]['mbps(ave)']
            if len(tmp) == 0:
                thr.append(0)
            else:
                thr.extend(tmp)
        plt.bar(x+i*width, thr, label=labels[i], width=width)

    plt.grid(axis='y')
    plt.legend()
    plt.ylabel('throughput(Mbps)')
    plt.grid(axis='y', linestyle=':')
    plt.show()


def plotMulticastThroughput(plugins):
    # multicast test
    throughput_perf, _ = load_data(multicast_test,  plugins)

    x = np.arange(4)
    total_width, n = 0.8, len(plugins)
    width = total_width / n
    # x = x - (total_width - width) / 2

    plt.xticks(x, num_subs, rotation=0)
    for i, cni in enumerate(plugins):
        thr = throughput_perf[throughput_perf['cni'] == cni]['mbps(ave)']
        plt.plot(x, thr, label=cni, marker='*', color=all_colors[i])
    plt.legend(bbox_to_anchor=(0.5, 1.12), loc='center', ncol=2)
    plt.xlabel('numSubscribers')
    plt.ylabel('multicast throughput(Mbps)')
    plt.rc('axes', axisbelow=True)
    plt.grid(axis='y', linestyle=':')
    plt.show()


def plotMulticastLoadLatency(plugins):
    # multicast test
    _, latency_perf = load_data(multicast_test,  plugins)
    x = np.arange(4)
    total_width, n = 0.8, len(plugins)
    width = total_width / n

    plt.xticks(x, num_subs, rotation=0)
    for i, cni in enumerate(plugins):
        thr = latency_perf[latency_perf['cni'] == cni]['90%']
        plt.plot(x, thr, label=cni, marker='.', color=all_colors[i])
    plt.legend(bbox_to_anchor=(0.5, 1.12), loc='center', ncol=2)
    plt.xlabel('numSubscribers')
    plt.ylabel('90th latency(us)')
    plt.rc('axes', axisbelow=True)
    plt.grid(axis='y', linestyle=':')
    plt.show()


def plotPingPongLatency(plugins):
    _, latency_perf = load_data(range(6), plugins, latencyTest=True)

    plt.xticks(range(len(data_len)), data_len)
    cell_text = []
    # plt.xticks(range(len(data_len)), data_len, rotation=0)
    for i, cni in enumerate(plugins):
        lat = latency_perf[latency_perf['cni'] == cni]['90%']
        cell_text.append(['%.1f' % thr for thr in lat])
        plt.plot(np.arange(6), lat, label=cni, marker='*', color=all_colors[i])
    
    # Add a table at the bottom of the axes
    the_table = plt.table(cellText=cell_text,
                        rowLabels=plugins,
                        cellLoc='center',
                        rowColours=all_colors[:len(plugins)],
                        colLabels=data_len,
                        loc='bottom')

    the_table.set_fontsize(15)
    the_table.scale(1, 1.5)
    # Adjust layout to make room for the table:
    plt.subplots_adjust(left=0.2, bottom=0.2)

    # plt.legend()
    # plt.xlabel('dataLen(B)')
    plt.ylabel('90th latency(us)', fontsize=15)
    plt.grid(axis='y', linestyle=':')
    plt.xticks([])
    plt.show()


# reliability test
def plotReliableLatency(plugins):
    _udp_plugins = [x for x in plugins if 'udp' in x]
    _, udp_latency_perf = load_data([6, 7], udp_plugins + udp_dds_secure_plugins, latencyTest=True)
    udp_tests = udp_latency_perf['test'].tolist()
    cnis = udp_latency_perf['cni'].tolist()
    to_raw_cni = lambda my_cnis: ['-'.join(c.split('-')[:-1]) for c in my_cnis]
    cnis = to_raw_cni(cnis)
    udp_latency_perf['cni'] = cnis
    for i, t in enumerate(udp_tests[:]):
        if t == 6:
            udp_tests[i] = 'UDP-Reliable'
        else:
            udp_tests[i] = 'UDP-BestEffort'
    udp_latency_perf['test'] = udp_tests

    _tcp_plugins = [x for x in plugins if 'tcp' in x]
    _, tcp_latency_perf = load_data([6, 7], tcp_plugins + tcp_dds_secure_plugins, latencyTest=True)
    tcp_tests = tcp_latency_perf['test'].tolist()
    cnis = tcp_latency_perf['cni'].tolist()
    cnis = to_raw_cni(cnis)
    tcp_latency_perf['cni'] = cnis
    for i, t in enumerate(tcp_tests[:]):
        if t == 6:
            tcp_tests[i] = 'TCP-Reliable'
        else:
            tcp_tests[i] = 'TCP-BestEffort'
    tcp_latency_perf['test'] = tcp_tests

    _tls_plugins = [x for x in plugins if 'tls' in x]
    _, tls_latency_perf = load_data([6, 7], tls_plugins, latencyTest=True)
    tls_tests = tls_latency_perf['test'].tolist()
    cnis = tls_latency_perf['cni'].tolist()
    cnis = to_raw_cni(cnis)
    tls_latency_perf['cni'] = cnis
    for i, t in enumerate(tls_tests[:]):
        if t == 6:
            tls_tests[i] = 'TLS-Reliable'
        else:
            tls_tests[i] = 'TLS-BestEffort'
    tls_latency_perf['test'] = tls_tests

    latency_perf = pd.concat([udp_latency_perf, tcp_latency_perf, tls_latency_perf])
    latency_perf = latency_perf.reset_index(drop=True)
    
    x = np.arange(len(raw_cnis))
    plt.xticks(x, raw_cnis, rotation=30, ha='right')
    total_width, n = 0.8, len(reliable_config)
    width = total_width / n
    x = x - (total_width - width) / 2

    for i, l in enumerate(reliable_config):
        thr = []
        std = []
        for cni in raw_cnis:
            tmp1 = latency_perf[(latency_perf['test'] == l) & (latency_perf['cni'] == cni)]['latencyave']
            tmp2 = latency_perf[(latency_perf['test'] == l) & (latency_perf['cni'] == cni)]['std'].tolist()
            if len(tmp1) == 0:
                thr.append(0)
                std.append(0)
            else:
                thr.extend(tmp1)
                std.append(tmp2)
  
        plt.bar(x+i*width, thr, label=reliable_config[i], width=width, yerr=std, capsize=5)

    plt.legend(bbox_to_anchor=(0.5, 1.1), loc='center', ncol=4)
    # plt.xlabel('cni')
    plt.ylabel('Ave latency(ns)')
    plt.grid(axis='y', linestyle=':')
    plt.show()


def plotMulticastPingPongLatency(plugins):
    # multicast test
    _, latency_perf = load_data(multicast_test,  plugins, latencyTest=True)

    plt.xticks(np.arange(4), num_subs, rotation=0)
    for i, cni in enumerate(plugins):
        thr = latency_perf[latency_perf['cni'] == cni]['90%']
        plt.plot(np.arange(4), thr, label=cni, marker='*', color=all_colors[i])
    plt.legend(bbox_to_anchor=(0.5, 1.1), loc='center', ncol=2)
    plt.xlabel('numSubscribers')
    plt.ylabel('90th latency(us)')
    plt.grid(axis='y', linestyle=':')
    plt.show()