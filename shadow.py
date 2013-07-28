#!/usr/bin/python

import fileinput
import sys
import re
import os
import signal
import copy
import gc
import pdb

from fdd import *


def sharing_edges(ni, nj):
    a = [edge.node.color for edge in ni.compressed_edgeset]
    b = [edge.node.color for edge in nj.compressed_edgeset]
    c = list(set(a) & set(b))

    if len(c) == 0:
        return 0

    num = 0

    for ie in ni.compressed_edgeset:
        for je in nj.compressed_edgeset:
            if ie == je:
                num += 1

    if num/len(ni.compressed_edgeset) > 0.5 \
        and num/len(nj.compressed_edgeset) > 0.5:
        return num
    else:
        print num
        print "ni", len(ni.compressed_edgeset)
        print "nj", len(nj.compressed_edgeset)
        return 0

length = [2**32, 2**32, 2**16, 2**16, 2**8]
def share_edge_length(ie, je, length):
    r = 0.0
    for ir in ie.rangeset:
        for jr in je.rangeset:
            inct = ir.insect(jr)
            if inct != None:
                r += float(inct.h - inct.l+1)/length
    return r


def sharing_length(ni, nj):
    a = [edge.node.color for edge in ni.edgeset]
    b = [edge.node.color for edge in nj.edgeset]
    c = list(set(a) & set(b))

    if len(c) == 0:
        return 0

    r = 0.0
    for ie in ni.edgeset:
        for je in nj.edgeset:
            if ie.node.color == je.node.color:
                r += share_edge_length(ie, je, length[ni.dim])
    return r



def similarity(levelnodes):
#wm weight matrix
    wm = [0] * (len(levelnodes)*len(levelnodes))

    msharing = 0
    for i in xrange(len(levelnodes)):
        for j in xrange(i+1, len(levelnodes)):
            #print i,j
            wm[i*len(levelnodes) + j] = sharing_edges(levelnodes[i], levelnodes[j])
            #wm[i*len(levelnodes) + j] = sharing_length(levelnodes[i], levelnodes[j])
            if wm[i*len(levelnodes) +j] > msharing:
                msharing = wm[i*len(levelnodes) + j]

    print "this level", msharing
    #print filter(lambda x:x>0, wm)

def print_lvl(levelnodes):
    for n in levelnodes:
        print [(e.rangeset, e.node.color) for e in n.compressed_edgeset]

if __name__ == "__main__":
    #pc = rule.pc_syn(700,38,10, 2000)
    #print "tcam raw", rule.tcam_entry_raw(pc)

    #order=[4,1,2,3,0]
    #print sys.argv
    order =map(int, sys.argv[1:6])
    print "input ", reduce(lambda x,y:x+y, map(str, order))

    pc = rule.load_ruleset(sys.argv[6])
    print "laod rulset: ", len(pc)

    #order=[2,4,3,0,1]
    #order=[2,4,0,1,3]
    #order=[4,2,3,0,1]
    f = FDD(order)

    ##the last one is a wild rule
    #gc.disable()
    try:
        levelnodes,leafnodes = f.build_fdd(pc)
    except KeyboardInterrupt:
        print ""
        mem = f.fdd_mem(f.root)
        print 'rangecnt',f.rangecnt, 'edgecnt', f.edgecnt, 'nodecnt',f.nodecnt
        print "FDD(mem):", mem, "bytes", mem/1024., "KB", mem/(1024.*1024), "MB"
        print "FDD: ", f.nodecnt, f.edgecnt, f.rangecnt
        print "killed"
        sys.exit(-1)
    #gc.enable()

    mem = f.fdd_mem(f.root)
    print "FDD(mem):", mem, "bytes", mem/1024., "KB", mem/(1024.*1024), "MB"
    print "FDD: ", f.nodecnt, f.edgecnt, f.rangecnt

    reducednodes = f.fdd_reduce(pc, levelnodes, leafnodes)
    f.compress(reducednodes)
    #print_lvl(reducednodes[4])


    for x in xrange(len(reducednodes)):
        similarity(reducednodes[x])









