# encoding: utf-8
# Author: Zhuangwei Kang

import os
import pandas as pd


def parse_output(output, fields):
    # print(output)
    data = {}
    for fld in fields:
        val = output.split(fld)[1].strip('\n').strip()
        avoid = [' ', '', '\n', 'us', '%']
        for x in avoid:
            val = val.replace(x, '')

        key = fld.lower().replace(' ', '')
        if '.' in key:
            key = key.replace('.', '_')
        if ':' in key:
            key = key.replace(':', '')

        try:
            data.update({key: float(val)})
        except ValueError:
            if fld == 'Lost:':
                val = float(val.split('(')[1].split(')')[0])
            data.update({key: val})
        output = output.split(fld)[0]
    return data


def parse_latency(perftest_output, format2=False):
    '''
    Example perftest_output
    # if dds_secure is True
    Length (Bytes), Ave (us), Std (us), Min (us), Max (us), 50% (us), 90% (us), 99% (us), 99.99% (us), 99.9999% (us), CPU (%)
            64,     4616,   3699.6,     1619,    14934,     2588,     9689,    14934,       14934,         14934,   25.01


    # otherwise
    Length:    64  Latency: Ave   3274 us  Std 1079.1 us  Min    616 us  Max   8661 us  50%   3002 us  90%   4638 us 99%   8661 us  99.99%   8661 us  99.9999%   8661 us CPU: 28.58%
    '''
    
    fields = ['CPU:', '99.9999%', '99.99%', '99%', '90%', '50%', 'Max', 'Min', 'Std', 'Latency: Ave', 'Length:']
    if not format2:
        latency_perf = parse_output(perftest_output, fields)
    else:
        latency_perf = {}
        perftest_output = perftest_output.split(',')
        perftest_output = [float(x.strip()) for x in perftest_output]
        perftest_output.reverse()
        for i in range(len(fields)):
            latency_perf.update({fields[i].lower().replace(':', '').replace(' ', '').replace('.', '_'): perftest_output[i]})
    return latency_perf


def parse_throughput(perftest_output, format2=False):
    '''
    Example perftest_output
    # if dds_secure is True
    Length (Bytes), Total Samples, Ave Samples/s,    Ave Mbps, Lost Samples, Lost Samples (%), CPU (%)
            64,        280537,          2337,         1.2,            0,             0.00,   14.61

    # otherwise
    Length:    64  Packets:   756371  Packets/s(ave):    6302  Mbps(ave):     3.2  Lost:     0 (0.00%) CPU: 22.30%
    '''

    fields = ['CPU:', 'Lost:', 'Mbps(ave):', 'Packets/s(ave):', 'Packets:', 'Length:']
    if not format2:
        throughput_perf = parse_output(perftest_output, fields)
    else:
        throughput_perf = {}
        perftest_output = perftest_output.split(',')
        perftest_output = [float(x.strip()) for x in perftest_output]
        del perftest_output[-3]
        perftest_output.reverse()
        for i in range(len(fields)):
            throughput_perf.update({fields[i].lower().replace(':', '').replace(' ', '').replace('.', '_'): perftest_output[i]})
    return throughput_perf


# DDS Secure has different output format with others
def find_line(fname, format2=False):
    with open(fname, encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
        for i, l in enumerate(lines):
            if 'Length' in l:
                if not format2:
                    return l
                else:
                    return lines[i+1]


def load_data(subtests, plugins, latencyTest=False, path='./', pubID = 0):
    throughput_perf = []
    latency_perf = []
    if latencyTest:
        test = 'latencyTest'
    else:
        test = 'throughputTest'
    for cni in plugins:
        for t in subtests:
            perfs = []
            subs = [sub for sub in os.listdir('%s/%s/%s/test-%d/' % (path, test, cni, t)) if 'sub' in sub]
            for sub in subs:
                try:
                    perftest_output = find_line('%s/%s/%s/test-%d/%s' % (path, test, cni, t, sub), True)
                    tperf = parse_throughput(perftest_output, True)
                except:
                    perftest_output = find_line('%s/%s/%s/test-%d/%s' % (path, test, cni, t, sub), False)
                    tperf = parse_throughput(perftest_output, False)
                perfs.append(tperf)
            avg_perf = {}
            for fld in perfs[0]:
                avg_perf.update({fld: 0})
            for fld in perfs[0]:
                for perf in perfs:
                    avg_perf[fld] += perf[fld]
            for fld in avg_perf:
                avg_perf[fld] /= len(subs)
            avg_perf.update({'test': t, 'cni': cni})
            throughput_perf.append(avg_perf)

            try:
                perftest_output = find_line('%s/%s/%s/test-%d/rtiperftest-pub%d.log' % (path, test, cni, t, pubID), True)
                lperf = parse_latency(perftest_output, True)
            except:
                perftest_output = find_line('%s/%s/%s/test-%d/rtiperftest-pub%d.log' % (path, test, cni, t, pubID), False)
                lperf = parse_latency(perftest_output, False)
            lperf.update({'test': t, 'cni': cni})
            latency_perf.append(lperf)
    return pd.DataFrame(throughput_perf), pd.DataFrame(latency_perf)      