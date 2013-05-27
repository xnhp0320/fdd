#!/usr/bin/python


import sys
from fdd import *
import rule
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



def firewall_compressor_algo(pc, order):

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
    return len(rr_out)



if __name__ == "__main__":

    sys.setrecursionlimit(10000)
    pc = rule.load_ruleset(sys.argv[1])
    #pc = rule.pc_syn(700,38,10, 2000)
    print "laod rulset: ", len(pc)
    #print "tcam raw", rule.tcam_entry_raw(pc)

    order=[4,0,1,2,3]
    #firewall_compressor_algo(pc, order)
    redund_remove(pc, order)

    #ww = filter(lambda x: x[0].r.is_large(0.05) and x[1].r.is_large(0.05), pc)
    #wx = filter(lambda x: x[0].r.is_large(0.05) and not x[1].r.is_large(0.05), pc)
    ##rule.rule_parse(wx, "@0.0.0.0/0\t0.0.0.0/0\t0 : 65535\t0 : 65535\t0x00/0x00", 0)
    #xw = filter(lambda x: not x[0].r.is_large(0.05) and x[1].r.is_large(0.05), pc)
    ##rule.rule_parse(xw, "@0.0.0.0/0\t0.0.0.0/0\t0 : 65535\t0 : 65535\t0x00/0x00", 0)
    #xx = filter(lambda x: not x[0].r.is_large(0.05) and not x[1].r.is_large(0.05), pc)
    ##rule.rule_parse(xx, "@0.0.0.0/0\t0.0.0.0/0\t0 : 65535\t0 : 65535\t0x00/0x00", 0)

    #wwc = firewall_compressor_algo(ww, order)
    #wxc = firewall_compressor_algo(wx, order)
    #xwc = firewall_compressor_algo(xw, order)
    #xxc = firewall_compressor_algo(xx, order)

    #print float(wwc+wxc+xwc+xxc) / len(pc)

