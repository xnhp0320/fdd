#!/usr/bin/python

import fileinput
import sys
import re
import os
import signal
import copy
import gc
import pdb
import math

from fdd import *
from collections import deque
from itertools import ifilter


def sharing_edges(ni, nj):
    a = [edge.node.color for edge in ni.edgeset]
    b = [edge.node.color for edge in nj.edgeset]
    c = list(set(a) & set(b))

    if len(c) == 0:
        return 0

    num = 0

    for ie in ni.edgeset:
        for je in nj.edgeset:
            if ie == je:
                num += 1

    #if num/len(ni.compressed_edgeset) >= 0.5:
    #    return num
    #elif num/len(nj.compressed_edgeset) >= 0.5:
    #    return -num
    #else:
    #    #print num
    #    #print "ni", len(ni.compressed_edgeset)
    #    #print "nj", len(nj.compressed_edgeset)
    #    return 0
    return num

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


def bfs(wm, r, n):
    q = deque()
    q.append(r)
    ns = {r:1}

    while len(q) != 0:
        c = q.popleft()
        for y in xrange(n):
            if wm[c*n+y] != 0:
                if y not in ns:
                    ns[y] = 1
                    q.append(y)
    return ns.keys()

def get_all_graphs(wm):
    n = int(math.sqrt(len(wm)))
    fset = [0]*n
    gset = []
    k = sum(fset)

    while k != n:
        r = fset.index(0)
        bset = bfs(wm, r, n)
        for i in bset:
            fset[i] = 1
        k = sum(fset)
        gset.append(bset)

    return gset

def diff_edges(ni, nj):
#ni.edges - nj.edges
    diff_eset = []
    #ceset = []
    flag = True

    #if ni.no == 1852 and nj.no == 1866:
    #    print "here"
    #if ni.no == 1866 and nj.no == 1852:
    #    print "here"

    for ie in ni.edgeset:
        flag = True
        for je in nj.edgeset:
            if ie == je:
                flag = False
                break
        if flag:
            diff_eset.append(ie)
        #else:
        #    ceset.append(ie)

    #return diff_eset, ceset
    return diff_eset

dentry = [rule.Range(0, 4294967295),
            rule.Range(0, 4294967295),
            rule.Range(0, 65535),
            rule.Range(0, 65535),
            rule.Range(0,255)]

def share_edge_compress(tn, nset, levelnodes, table):
    max_degree = 0
    root = None
    for n in tn:
        if len(nset[n]) > max_degree:
            max_degree = len(nset[n])
            root = n

#(G, L, Weight) G,L =(Code, len)
    def bfs_tree(r, nset):
#ln = levelnodes
#(node, parent)
        ln = [[(r,-1)], []]
        q = deque()
        q.append(r)

        nextl = 1
        currln = 1
        nextln = 0

        while len(q) != 0:
            n = q.popleft()

            for c in nset[n]:
                q.append(c)
                ln[nextl].append((c,n))
                nset[c].remove(n)

            nextln += len(nset[n])
            currln -= 1

            if currln == 0 and nextln != 0:
                ln.append([])
                currln = nextln
                nextln = 0

        return ln

    ln = bfs_tree(root, nset)

    for li in xrange(len(ln)-2, -1, -1):
        if li != 0:
            for lns in ln[li]:
                diff_eset = diff_edges(levelnodes[lns[0]], levelnodes[lns[1]])
                table[lns[0]] = (diff_eset, dentry[levelnodes[lns[0]].dim], levelnodes[lns[1]])

    table[root] = (levelnodes[root].edgeset, None, None)

    return table



    #print len(ln)
    #print ln



def get_edges(levelnodes):
    edges = []
    for i in xrange(len(levelnodes)):
        for j in xrange(i+1, len(levelnodes)):
            #print i,j
            #if (levelnodes[i].no == 1852 and levelnodes[j].no == 1866) or (levelnodes[j].no == 1852 and levelnodes[i].no == 1866):
            #    print "here"
            weight = sharing_edges(levelnodes[i], levelnodes[j])
            if weight > 0:
                edges.append((i,j,weight))
    return edges


def kruskal(edges):

    if len(edges) == 0:
        return [], dict()

    edges.sort(key=lambda x:x[2], reverse=True)
    reduced_edges = 0

    nset = {}
    eset = []
    for e in edges:
        if nset.get(e[0]) == None or nset.get(e[1]) == None:
            eset.append((e[0],e[1]))
            reduced_edges += e[2]

            if e[0] in nset:
                nset[e[0]].append(e[1])
            else:
                nset[e[0]]=[e[1]]

            if e[1] in nset:
                nset[e[1]].append(e[0])
            else:
                nset[e[1]]=[e[0]]

    print "reduced edges", reduced_edges
#is it a tree or a forset?
    node_set = set(nset.keys())
#bfs
    def bfs(r, nset):
        q = deque()
        q.append(r)
        ns = set()
        ns.add(r)

        while len(q) != 0:
            c = q.popleft()
            for y in nset[c]:
                if y not in ns:
                    ns.add(y)
                    q.append(y)

        return ns

    tree_node = []

    while len(node_set) != 0:
        r = node_set.pop()
        ns = bfs(r, nset)
        tree_node.append(list(ns))
        ns.remove(r)
        node_set = node_set - ns

    print "tree num", len(tree_node)
    return tree_node, nset


def similarity(levelnodes):
#wm weight matrix
    wm = [0] * (len(levelnodes)*len(levelnodes))

    msharing = 0
    for i in xrange(len(levelnodes)):
        for j in xrange(i+1, len(levelnodes)):
            #print i,j
            weight = sharing_edges(levelnodes[i], levelnodes[j])
            #weight = sharing_length(levelnodes[i], levelnodes[j])
            wm[i*len(levelnodes) + j] = weight
            wm[j*len(levelnodes) + i] = weight
            #wm[i*len(levelnodes) + j] = sharing_length(levelnodes[i], levelnodes[j])
            if abs(weight) > msharing:
                msharing = abs(weight)

    print "this level", msharing
    #print wm
    #gset = get_all_graphs(wm)
    #print len(gset)
    #print len(levelnodes)

    #print filter(lambda x:x>0, wm)

def print_lvl(levelnodes):
    for n in levelnodes:
        print [(e.rangeset, e.node.color) for e in n.compressed_edgeset]

def sharing_match(root, trace, table, check):
    n = root
    t = trace[n.dim]
    d = -1
    ti = 0

    while n.dim != -1:
        eset = table[ti][n.color]
        t = trace[n.dim]
        for ei in xrange(len(eset)):
            rmatched = False
            for r in eset[ei].rangeset:
                if r.match(t):
                    if check[ti][n.color] == 1:
                        if ei != len(eset) - 1:
                            ti += 1
                        n = eset[ei].node
                    else:
                        n = eset[ei].node
                        ti += 1

                    rmatched = True
                    break
            if rmatched:
                break
    if rmatched:
        d = n.ppc[0]

    return (d!=-1), d


def compressed_entries(check, table):
    tcam_entries = 0
    original = 0
    for ti in xrange(len(table)):
        for color in table[ti].keys():
            eset = table[ti][color]
            if check[ti][color] == 0:
                for e in eset:
                    for r in e.rangeset:
                        tcam_entries += r.prefix_entries()
                        original += 1
            else:
                for ei in xrange(len(eset) - 1):
                    for r in eset[ei].rangeset:
                        tcam_entries += r.prefix_entries()
                        original += 1
    print "original", original, "tcam", tcam_entries
    return original, tcam_entries

if __name__ == "__main__":
    #pc = rule.pc_syn(700,38,10, 2000)
    #print "tcam raw", rule.tcam_entry_raw(pc)

    #order=[4,1,2,3,0]
    #print sys.argv
    order =map(int, sys.argv[1:6])
    print "input ", reduce(lambda x,y:x+y, map(str, order))

    pc = rule.load_ruleset(sys.argv[6])
    print "laod rulset: ", len(pc)
    tcam_raw = rule.tcam_entry_raw(pc)
    print "tcam raw", tcam_raw

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
    #f.compress(reducednodes)
    #print_lvl(reducednodes[4])


    multi_compressed_table = []
    multi_check = []
    for x in xrange(len(reducednodes)):
        #similarity(reducednodes[x])
        edges = get_edges(reducednodes[x])
        #print edges
        print "level", x, "dim", order[x]
        tree_node, nset = kruskal(edges)
        compressed_table = {}
        table = {}
        check = {}
        left_nodes = set(range(len(reducednodes[x]))) - set(nset.keys())

        for no in left_nodes:
            n = reducednodes[x][no]
            compressed_table[n.color] = FDD.compress_eset(n.edgeset, None, None)
            #compressed_table[n.color] = FDD.razor_compress_eset(n.edgeset, n.dim, None, None)
            check[n.color] = 0

        for tn in tree_node:
            table = share_edge_compress(tn, nset, reducednodes[x], table)
            for n in tn:
                #if x == 3:
                #    print "here"
                compressed_table[reducednodes[x][n].color] = FDD.compress_eset(table[n][0], table[n][1], table[n][2])
                #compressed_table[reducednodes[x][n].color] = FDD.razor_compress_eset(table[n][0],
                #        reducednodes[x][n].dim, table[n][1], table[n][2])
                #print compressed_table[n]
                if table[n][1] != None:
                    check[reducednodes[x][n].color] = 1
                else:
                    check[reducednodes[x][n].color] = 0


        multi_compressed_table.append(compressed_table)
        multi_check.append(check)

    #for t in multi_compressed_table:
    #    for en in t.keys():
    #        for e in t[en]:
    #            print e.rangeset, e.node.color

    compressed_entries(multi_check, multi_compressed_table)

    traces = rule.load_traces("acl1_2_0.5_-0.1_1K_trace")
    for ti in range(len(traces)):
        #if ti == 345:
        #    print "here"
        d1 = sharing_match(f.root, traces[ti], \
                multi_compressed_table, multi_check)
        d2 = rule.match(pc, traces[ti])

        #if d1 == d2[1]:
        #    pass
        #else:
        #    print t, d1, d2
        #if ti == 779:
        #    v = True
        #    f.fdd_match(traces[ti],v)

        if d1[0] == d2[0] and pc[d1[1]][len(f.order)].d == pc[d2[1]][len(f.order)].d:
        #if d1[0] == d2[0] and d1[1] == pc[d2[1]][len(f.order)].d:
            pass
        else:
            print traces[ti], ti, d2[1], pc[d1[1]][len(f.order)].d, pc[d2[1]][len(f.order)].d
            #print traces[ti], ti, d2[1], d1[1], pc[d2[1]][len(f.order)].d
            #d1 = f.fdd_match(traces[ti], v)










