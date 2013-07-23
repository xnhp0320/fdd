#!/usr/bin/python


import sys
from fdd import *
import rule
import copy
import itertools


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

def tcam_split_match(pc, order, sort_table_list, traces):

    for ti in xrange(len(traces)):
        t = traces[ti]
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

        d = rule.match(pc, t)
        if d[0] == table_matched and d[1] == next_id:
            pass
        else:
            print ti
            print t
            print d[0], d[1]
            print table_matched, next_id
            sys.exit(0)

def tcam_split_entries(pc, tcam):
    tcam_entries = 0

    for d in xrange(MAXDIM):
        for entry in tcam[d]:
            tcam_entries += entry[1].prefix_entries()

    tcam_raw = rule.tcam_entry_raw(pc)
    print "tcam split entries: ", tcam_entries
    print "tcam raw entries: ", tcam_raw
    print "compression: ", float(tcam_entries)/(4*tcam_raw)

def default_entries(tcam):
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



if __name__ == "__main__":

    sys.setrecursionlimit(10000)
    pc = rule.load_ruleset(sys.argv[1])
    #pc = rule.pc_syn(700,38,10, 2000)
    #pc = rule.pc_uniform(1000, 2000)
    print "laod rulset: ", len(pc)
    #print pc
    #print "tcam raw", rule.tcam_entry_raw(pc)

    order = [4,1,2,3,0]
    #order = [0,1,2,3,4]

    #pc = redund_remove(pc, order)
    #new_pc = firewall_compressor_algo(pc, order)
    tcam = tcam_split(pc, order)
    #traces = rule.load_traces("fw1_2_0.5_-0.1_1K_trace")
    #tcam_split_match(pc, order, tcam, traces)
    tcam_split_entries(pc, tcam)
    print default_entries(tcam), reduce(lambda x,y: x+y, map(lambda x: len(x), tcam))


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
    #tcam_split(ww, order)
    #tcam_split(wx, order)
    #tcam_split(xw, order)
    #tcam_split(xx, order)

    #print float(len(wwc)+len(wxc)+len(xwc)+len(xxc)) / len(pc)

