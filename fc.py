#!/usr/bin/python


import sys
from fdd import *
import rule
import copy
import itertools
from guppy import hpy
import kset
import signal
import subprocess
import time


def redund_remove(pc, order):
    f = FDD(order)
    gc.disable()
    try:
        levelnodes,leafnodes = f.build_fdd(pc)
    except KeyboardInterrupt:
        print 'rangecnt',f.rangecnt, 'edgecnt', f.edgecnt, 'nodecnt',f.nodecnt
        sys.exit(-1)
    gc.enable()
    mem = f.fdd_mem(f.root)
    print "FDD(mem):", mem, "bytes", mem/1024., "KB", mem/(1024.*1024), "MB"
    rr_out = []
    removed_list = []
    f.redund_remove_semantic(leafnodes, rr_out, removed_list, pc)

    print len(removed_list)
    print len(rr_out)
    #print removed_list
    print "original: ", len(pc)
    print "compression :", len(rr_out)/float(len(pc)) * 100, "%"
    return [pc[x] for x in rr_out]


def tcam_split(pc, order):
    if len(pc) == 0:
        return

    f = FDD(order)

    gc.disable()
    try:
        levelnodes,leafnodes = f.build_fdd(pc)
    except KeyboardInterrupt:
        print 'rangecnt',f.rangecnt, 'edgecnt', f.edgecnt, 'nodecnt',f.nodecnt
    gc.enable()
    mem = f.fdd_mem(f.root)
    print "FDD(mem):", mem, "bytes", mem/1024., "KB", mem/(1024.*1024), "MB"

    #cpc = f.firewall_compressor(pc, levelnodes, leafnodes)
    return f.tcam_split(pc, levelnodes, leafnodes)

def tcam_split_match_one(pc, order, sort_table_list, t):
    next_id = 0
    for x in xrange(MAXDIM):
        d = order[x]
        #print "d", d
        tv = t[d]
        #print "tv", tv
        table_matched = False
        for entry in sort_table_list[d]:
            if entry[0] == next_id:
                if entry[1].match(tv):
                    #print entry[1], "check", tv
                    next_id = entry[2]
                    table_matched = True
                    #print "next_id", next_id
                    break
        if table_matched == False:
            next_id = -1
            break

    return table_matched, next_id


def tcam_split_match(pc, order, sort_table_list, traces):

    for ti in xrange(len(traces)):
        t = traces[ti]
        #next_id = 0
        #for x in xrange(MAXDIM):
        #    d = order[x]
        #    #print "d", d
        #    tv = t[d]
        #    #print "tv", tv
        #    table_matched = False
        #    for entry in sort_table_list[d]:
        #        if entry[0] == next_id:
        #            if entry[1].match(tv):
        #                #print entry[1], "check", tv
        #                next_id = entry[2]
        #                table_matched = True
        #                #print "next_id", next_id
        #                break
        #    if table_matched == False:
        #        next_id = -1
        #        break
        table_matched, next_id = tcam_split_match_one(pc, order, sort_table_list, t)

        d = rule.match(pc, t)
        if d[0] == table_matched and d[1] == next_id:
            pass
        else:
            print ti
            print t
            print d[0], d[1]
            print table_matched, next_id
            sys.exit(0)

def multi_tcam_split_match(pc, order, tcam, traces):
    for ti in xrange(len(traces)):
        t = traces[ti]
        min_id = len(pc)

        for tables in tcam:
            table_matched, nextid = tcam_split_match_one(pc, order, tables, t)
            if nextid != -1 and nextid < min_id:
                min_id = nextid

        if min_id == len(pc):
            min_id = -1

        d = rule.match(pc, t)
        if d[0] == (min_id!=-1) and d[1] == min_id:
            pass
        else:
            print ti
            print t
            print "should be",  d[0], d[1]
            print "but be", (min_id!=-1), min_id
            sys.exit(0)





def tcam_split_entries(pc, tcam, tcam_raw):
    tcam_entries = 0

    for d in xrange(MAXDIM):
        for entry in tcam[d]:
            tcam_entries += entry[1].prefix_entries()

    print "tcam split entries: ", tcam_entries
    print "compression: ", float(tcam_entries)/(4*tcam_raw)

def default_entry(tcam):
    dentry = [rule.Range(0, 4294967295),
            rule.Range(0, 4294967295),
            rule.Range(0, 65535),
            rule.Range(0, 65535),
            rule.Range(0,255)]

    dcount = 0
    for d in xrange(MAXDIM):
        for entry in tcam[d]:
            if entry[1] == dentry[d]:
                #print entry
                dcount += 1

    return dcount

def multi_tcam_split(pc, d, order):
    #range-rule dict
    print "[*] Multi TCAMSplit begins"
    rr_dict = {}

    for rule in pc:
        if rule[d].r in rr_dict:
            rr_dict[rule[d].r].append(rule[len(rule)-1].d)
        else:
            rr_dict[rule[d].r] = [rule[len(rule)-1].d]

    k_set = []
    kset.split_kset(rr_dict.keys(), k_set)
    print "[*]There are",len(k_set), "sets"

    split_pc_id = [ [] for i in xrange(len(k_set))]

    set_id = 0
    for rset in k_set:
        for r in rset:
            split_pc_id[set_id].extend(rr_dict[r])
        set_id += 1

    split_pc_ref = [ [ pc[x] for x in pcids] for pcids in split_pc_id]
    tcam = []

    for spc in split_pc_ref:
        tcam.append(tcam_split(spc, order))

    tcam_entries = 0
    default_entries = 0

    for tables in tcam:
        default_entries += default_entry(tables)
        for t in tables:
            tcam_entries += reduce(lambda x,y: x+y, map(lambda x: x[1].prefix_entries(), t))

    print "Multi Split TCAM:", tcam_entries
    print "Default Entries:", default_entries
    return tcam

def firewall_compressor_algo(pc, order):

    f = FDD(order)
    gc.disable()
    try:
        levelnodes,leafnodes = f.build_fdd(pc)
    except KeyboardInterrupt:
        print 'rangecnt',f.rangecnt, 'edgecnt', f.edgecnt, 'nodecnt',f.nodecnt
        raise KeyboardInterrupt

    gc.enable()
    mem = f.fdd_mem(f.root)
    print "FDD(mem):", mem, "bytes", mem/1024., "KB", mem/(1024.*1024), "MB"
    cpc = f.firewall_compressor(pc, levelnodes, leafnodes)

    f3 = FDD(order)
    levelnodes, leafnodes = f3.build_fdd(cpc)
    rr_out = []
    removed_list = []
    f3.redund_remove_semantic(leafnodes, rr_out, removed_list, cpc)

    print len(removed_list)
    print len(rr_out)
    print "original: ", len(pc)
    print "compression :", len(rr_out)/float(len(pc)) * 100, "%"
    return [cpc[x] for x in rr_out]

def permutations(dl):

    ret = []
    if len(dl) == 1:
        ret.append(copy.copy(dl))
        return ret

    for i in xrange(len(dl)):
        t = dl[0]
        dl[0] = dl[i]
        dl[i] = t
        rret = permutations(dl[1:])
        for x in rret:
            x.insert(0, dl[0])
        for x in rret:
            ret.append(x)

    return ret

def find_optimal_permutations(fields):
    order_list = permutations(fields)
    print len(order_list)

    try:
        cr_list = []
        for order in order_list:
            lst = firewall_compressor_algo(pc, order)
            print rule.tcam_entry_raw(lst)
            print rule.tcam_entry_raw(pc)
            cr = float(len(lst))/len(pc)
            cr_list.append(cr)
    except KeyboardInterrupt:
        pass

    crmin = min(cr_list)
    index = cr_list.index(crmin)
    print order_list[index], crmin

def alarm_handler(signum, frame):
    proc = subprocess.Popen("./check_mem.sh", shell=True, stdout=subprocess.PIPE)
    mem=float(proc.communicate()[0].strip())
    if mem > 70.0:
        subprocess.call("./kill_fdd.sh", shell=True)
    signal.alarm(30)

def test_fdd():
    order_list = permutations([0,1,2,3,4])
    out = open("fdd_test_"+sys.argv[1], "w")
    signal.signal(signal.SIGALRM, alarm_handler)
    signal.alarm(30)

    for order in order_list:
        command = reduce(lambda x,y:x+y, map(lambda x: str(x) + " ", order))
        #print command
        #print "test ", order
        #print command+" "+sys.argv[1]
        subprocess.call("./fdd.py " + command + sys.argv[1], stdout=out, shell=True)

def analyze_test_fdd():
    new_record = False
    mem_list = []
    cr_list = []

    for line in fileinput.input("fdd_test_"+sys.argv[1]):
        if re.match(r"input", line):
            new_record = True
        elif re.match(r"FDD\(mem\):", line) and new_record:
            m = re.match(r"FDD\(mem\): (\d+)", line)
            mem = int(m.group(1))
            mem_list.append(mem)
            #print "mem", mem
        elif re.match(r"compression ratio: (.*)", line) and new_record:
            m = re.match(r"compression ratio: (.*)", line)
            cr = float(m.group(1))
            cr_list.append(cr)
            #print cr
            new_record = False

    print "CR"
    for cr in cr_list:
        print cr

    print "mem"
    for mem in mem_list:
        print mem





if __name__ == "__main__":

    sys.setrecursionlimit(10000)

    start = time.time()
    test_fdd()
    stop = time.time() - start
    print stop
    analyze_test_fdd()
    #pc = rule.load_ruleset(sys.argv[1])
    #pc = rule.pc_syn(700,38,10, 2000)
    #pc = rule.pc_uniform(1000, 2000)
    #print "laod rulset: ", len(pc)
    #print pc

    #tcam_raw = rule.tcam_entry_raw(pc)
    #print "tcam raw", tcam_raw

    #order = [1,4,0,2,3]
    #order = [0,1,4,2,3]

    #pc = redund_remove(pc, order)
    #new_pc = firewall_compressor_algo(pc, order)
    #tcam = tcam_split(pc, order)
    #traces = rule.load_traces("acl1_2_0.5_-0.1_1K_trace")
    #tcam_split_match(pc, order, tcam, traces)
    #tcam_split_entries(pc, tcam, tcam_raw)

    #tcam = multi_tcam_split(pc, 1, order)
    #multi_tcam_split_match(pc, order, tcam, traces)


    #print default_entries(tcam), reduce(lambda x,y: x+y, map(lambda x: len(x), tcam))


    #ww = filter(lambda x: x[0].r.is_large(0.05) and x[1].r.is_large(0.05), pc)
    #wx = filter(lambda x: x[0].r.is_large(0.05) and not x[1].r.is_large(0.05), pc)
    ###rule.rule_parse(wx, "@0.0.0.0/0\t0.0.0.0/0\t0 : 65535\t0 : 65535\t0x00/0x00", 0)
    #xw = filter(lambda x: not x[0].r.is_large(0.05) and x[1].r.is_large(0.05), pc)
    ###rule.rule_parse(xw, "@0.0.0.0/0\t0.0.0.0/0\t0 : 65535\t0 : 65535\t0x00/0x00", 0)
    #xx = filter(lambda x: not x[0].r.is_large(0.05) and not x[1].r.is_large(0.05), pc)
    ###rule.rule_parse(xx, "@0.0.0.0/0\t0.0.0.0/0\t0 : 65535\t0 : 65535\t0x00/0x00", 0)

    #wwc = firewall_compressor_algo(ww, order)
    #wxc = firewall_compressor_algo(wx, order)
    #xwc = firewall_compressor_algo(xw, order)
    #xxc = firewall_compressor_algo(xx, order)
    #tcam_entries = 0
    #t1 = tcam_split(ww, order)
    #t2 = tcam_split(wx, order)
    #t3 = tcam_split(xw, order)
    #t4 = tcam_split(xx, order)

    #for t in t1:
    #    tcam_entries += reduce(lambda x,y: x+y, map(lambda x: x[1].prefix_entries(), t))
    #for t in t2:
    #    tcam_entries += reduce(lambda x,y: x+y, map(lambda x: x[1].prefix_entries(), t))
    #for t in t3:
    #    tcam_entries += reduce(lambda x,y: x+y, map(lambda x: x[1].prefix_entries(), t))
    #for t in t4:
    #    tcam_entries += reduce(lambda x,y: x+y, map(lambda x: x[1].prefix_entries(), t))

    #print tcam_entries


    h = hpy()
    print h.heap()
    #print float(len(wwc)+len(wxc)+len(xwc)+len(xxc)) / len(pc)

