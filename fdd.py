#!/usr/bin/python


import fileinput
import sys
import re
import os
import rule
import signal
import gc
from fwsched import Scheduler
from fwsched import PrepSchedData



RULE_INDEX = 2
RANGE_SIZE = 8
POINTER_SIZE = 4
NODE_SIZE = 1


class PackRange:
    def __init__(self, r):
        self.r = r
    def __repr__(self):
        return self.r.__repr__()

def pack_raw_pc(raw_pc):
    pc = []
    for pcr in raw_pc:
        prefix = []
        for r in pcr:
            pr = PackRange(r)
            prefix.append(pr)

        pc.append(prefix)
    return pc




class Bitmap:
    def __init__(self, num):
        self.num = num
        self.bits = num * [0]

    def setbit(self, num):
        self.bits[num] = 1

    def clearbit(self, num):
        self.bits[num] = 0

    def strbit(self):
        s = reduce(lambda x,y: str(x) + str(y), self.bits)
        return s

    def intbit(self):
        y = 0
        for x in self.bits:
            y |= x
            y <<= 1
        return y

def rset_minus(r, rangeset):
    ret = []
    t = rule.Range(l = r.l, h = r.h)
    for i in range(len(rangeset)):
        if t.l <= t.h:
            if t.l < rangeset[i].l:
                ret.append(rule.Range(l=t.l, h=min(rangeset[i].l-1, t.h)))
            t.l = max(t.l, rangeset[i].h + 1)
        else:
            break
    if t.l <= t.h:
        ret.append(t)
    return ret

class CMPError(Exception):
    def __init__(self):
        pass

    def __repr__(self):
        return "compare edge with no color assigned"


class FDDEdge:
    def __init__(self):
        self.rangeset = []
        self.node = None
        #self.active = True

    def __eq__(self, other):

        if self.node.color == -1 or other.node.color == -1:
            #print self.node.dim
            raise CMPError

        if self.node.color != other.node.color:
            return False
        else:
            if len(self.rangeset) != len(other.rangeset):
                return False
            else:
                for i in range(len(self.rangeset)):
                    if self.rangeset[i] == other.rangeset[i]:
                        continue
                    else:
                        return False
        return True

    def __del__(self):
        del self.rangeset

    def merge(self, other):
        other.node = self.node
        #other.active = False
        self.rangeset.extend(other.rangeset)
        self.rangeset = list(set(self.rangeset))
        self.rangeset.sort()

        nrangeset = []
        i = 0
        while i< len(self.rangeset):
            rt = self.rangeset[i]
            j = i+1
            while j< len(self.rangeset):
                if rt.h == self.rangeset[j].l - 1:
                    rt.h = self.rangeset[j].h
                    j += 1
                else:
                    break
            nrangeset.append(rt)
            i = j

        self.rangeset = nrangeset





class FDDNode:
    def __init__(self):
        self.dim = -1
        self.edgeset = []
        self.in_edgeset = []
        self.ppc = []
        self.sig = -1
        self.color = -1
        self.cost = -1

        self.compressed_edgeset = []

    def __eq__(self,other):
        if self.sig != other.sig:
            return False
        else:
            if len(self.edgeset) != len(other.edgeset):
                return False
            for i in range(len(self.edgeset)):
                if self.edgeset[i] == other.edgeset[i]:
                    continue
                else:
                    return False
        return True

    def clear(self):
        del self.edgeset
        del self.in_edgeset
        if 'ppc' in dir(self):
            del self.ppc

    def edges_reduce(self):
        ndict = {}
        for e in self.edgeset:
            if e.node.color in ndict:
                ndict[e.node.color].append(e)
            else:
                ndict[e.node.color] = [e]

        nedgeset = []

        for key in ndict.keys():
            if len(ndict[key]) == 1:
                nedgeset.extend(ndict[key])
            if len(ndict[key]) > 1:
                e = ndict[key][0]
                for oe in ndict[key][1:]:
                    e.merge(oe)
                nedgeset.append(e)

        self.edgeset = nedgeset





class FDD:
    def __init__(self, order):
        self.order = order
        self.root = FDDNode()

        self.nodecnt = 0
        self.edgecnt = 0
        self.rangecnt = 0

    def build_interval(self, rset):
        rl = list(set(rset))
        #print rl
        retl = [rl[0]]

        for r in rl[1:]:
            minus = rset_minus(r, retl)
            aux_insects = []
            #if r.h ==1358954495:
            #    print retl

            for ri in range(len(retl)):
                #print "retl", retl[ri]
                if not retl[ri].within(r):
                    insect = retl[ri].insect(r)
                    #print insect
                    if insect != None:
                        t = retl[ri].minus(r)
                        #print "t", t
                        retl[ri] = t[0]
                        if len(t) != 1:
                            aux_insects.append(t[1])
                        aux_insects.append(insect)

            if len(aux_insects) != 0:
                retl.extend(aux_insects)
            if len(minus) != 0:
                retl.extend(minus)
            retl.sort()

        return retl

    def build_bms(self, i, rset, bms):
        """ i is the interval"""
        #t = [(r.l, r.h) for r in rset]

        tnum = 0
        for atomic in i:
            bitmap = Bitmap(len(rset))
            num = 0
            for r in rset:
                if atomic.within(r):
                    bitmap.setbit(num)
                else:
                    bitmap.clearbit(num)
                num += 1

            #print bitmap.intbit()

            if bitmap.intbit() in bms:
                bms[bitmap.intbit()].append(tnum)
            else:
                bms[bitmap.intbit()] = [tnum]
            tnum += 1

    def build_node_pc(self, pc, parent, edge):
        nppc = []
        rs = [(pc[x])[parent.dim].r for x in parent.ppc]

        for ri in range(len(rs)):
            for er in edge.rangeset:
                if er.within(rs[ri]):
                    nppc.append(parent.ppc[ri])
                    break;

        return nppc

    def color_level(self, level):
        uniq = [level[0]]
        level[0].color = 0

        color = 1
        flag = 0

        for n in level[1:]:
            for nu in uniq:
                if nu == n:
                    n.color = nu.color
                    for e in n.in_edgeset:
                        e.node = nu
                    n.clear()
                    flag = 1
                    break
                else:
                    continue

            if flag == 0:
                n.color = color
                color += 1
                uniq.append(n)
            else:
                flag = 0

        print len(level), len(uniq)
        return uniq




    def fdd_reduce(self, levelnodes, leafnodes):

        self.process_leafnodes(leafnodes)
        self.sig_node(self.root)

        reducednodes = {}
        for i in range(len(self.order)-1, -1, -1):
            reducednodes[i] = self.color_level(levelnodes[i])

        for i in range(len(self.order)):
            for n in reducednodes[i]:
                n.edges_reduce()
        return reducednodes


    def fdd_match(self, trace):
        pass

    def prepare_sched(self, n):
        prepdict = {}
        for e in n.edgeset:
            for r in e.rangeset:
                prep = PrepSchedData(r, e.node.color, e.node.cost)
                if e.node.color not in prepdict:
                    prepdict[e.node.color] = [prep]
                else:
                    prepdict[e.node.color].append(prep)

        #print prepdict.values()
        preplist = reduce(lambda x,y: x+y, prepdict.values())
        #print preplist
        preplist.sort()
        color = [x.color for x in preplist]

        cost = {}
        for key in prepdict.keys():
            cost[key] = prepdict[key][0].cost

        group = {}
        index = 0
        for c in color:
            if c not in group:
                group[c] = [index]
            else:
                group[c].append(index)
            index += 1

        for key in prepdict.keys():
            prepdict[key].sort()

        return color, cost, group, preplist


    def make_compressed_edgeset(self, n, R, RC, preplist):
        rangeset = []
        color = []
        #print preplist
        #print R
        for ri in range(len(R)):
            i = R[ri].l
            while i<= R[ri].h:
                rt = preplist[i].r
                j = i+1
                while j <= R[ri].h:
                    if rt.h == preplist[j].r.l -1:
                        rt.h = preplist[j].r.h
                        j += 1
                    else:
                        break
                rangeset.append(rt)
                color.append(RC[ri])
                i = j

        for ci in range(len(color)):
            ne = FDDEdge()
            for e in n.edgeset:
                if color[ci] == e.node.color:
                    ne.node = e.node
                    ne.rangeset.append(rangeset[ci])
            n.compressed_edgeset.append(ne)

        #return rangeset
        #print rangeset
        #print R



    def compress(self, levelnodes):
        for i in range(len(self.order)-1, -1, -1):
            for n in levelnodes[i]:
                color, cost, group, preplist = self.prepare_sched(n)
                #print color, cost, group
                #print len(color)
                sched = Scheduler(color, cost, group)
                n.cost = sched.FSA_cost(0, len(color)-1)
                sched.FSA_result(0,0,len(color)-1)
                #print sched.R

                self.make_compressed_edgeset(n, sched.R, sched.RC, preplist)




    def build_fdd(self, pc):
        self.root.ppc = range(len(pc))
        thislevel = [self.root]
        nextlevel = []
        levelnodes = {}
        levelcnt = 0
        bms = {}

        for dim in self.order:
            for node in thislevel:
                node.dim = dim
                rs = [(pc[x])[dim].r for x in node.ppc]
                #if dim==4:
                    #if rule.Range(l=0,h=255) not in rs:
                    #    print rs

                i = self.build_interval(rs)
                #if dim == 4:
                #print i
                #print len(i)
                self.build_bms(i, rs, bms)


                for equalrs in bms.values():
                    edge = FDDEdge()
                    self.edgecnt += 1
                    for ri in equalrs:
                        edge.rangeset.append(i[ri])
                        self.rangecnt += 1
                    edge.node = FDDNode()
                    edge.node.in_edgeset.append(edge)
                    self.nodecnt += 1
                    edge.node.ppc = self.build_node_pc(pc, node, edge)
                    nextlevel.append(edge.node)
                    node.edgeset.append(edge)

                del node.ppc
                del bms
                bms = {}

            levelnodes[levelcnt] = thislevel
            levelcnt += 1
            print "finish", dim
            print "nodecnt", self.nodecnt
            print "edgecnt", self.edgecnt
            print "rangecnt", self.rangecnt
            thislevel = nextlevel
            nextlevel = []

        #self.process_leafnodes(thislevel)
        #self.sig_node(self.root)
        print "\n*building complete\n"
        return levelnodes, thislevel

    def output_compressed_list(self, n, prefix, raw_pc):
        if n.dim == -1:
            #print prefix
            raw_pc.append(list(prefix))
            return

        for e in n.compressed_edgeset:
            for r in e.rangeset:
                prefix[n.dim] = r
                self.output_compressed_list(e.node, prefix, raw_pc)


    def firewall_compressor(self, levelnodes, leafnodes):
        print "*compress the ruleset"
        reducednodes = self.fdd_reduce(levelnodes, leafnodes)
        self.compress(reducednodes)
        prefix = [ None for x in xrange(len(self.order)) ]
        raw_pc = []
        self.output_compressed_list(self.root, prefix, raw_pc)
        print "compress the ruleset raw:", len(raw_pc)
        return pack_raw_pc(raw_pc)

    def redund_remove(self, leafnodes, rr_output, removed_list):
        ppcdict = {}
        for ni in range(len(leafnodes)):
            for ppc in leafnodes[ni].ppc:
                if ppc in ppcdict:
                    ppcdict[ppc].append(ni)
                else:
                    ppcdict[ppc] = [ni]

        for ppc in ppcdict.keys():
            ppc_no_overlapped = False
            for ni in ppcdict[ppc]:
                if leafnodes[ni].ppc[0] == ppc:
                    ppc_no_overlapped = True
                    break
                else:
                    continue
            if ppc_no_overlapped:
                rr_output.append(ppc)
            else:
                removed_list.append(ppc)



    def process_leafnodes(self, levelnodes):

        nextlevel = []
        leafdict = {}
        leafcolor = 0
        for n in levelnodes:
            if n.sig == -1:
                if len(n.ppc) != 0:
                # n is the leaf
                    #strkey = reduce(lambda x,y: str(x)+"."+str(y), n.ppc)
                    strkey = n.ppc[0]
                    #print strkey
                    if strkey not in leafdict:
                        leafdict[strkey] = leafcolor
                        n.sig = leafcolor
                        n.color = n.sig
                        leafcolor += 1
                    else:
                        n.sig = leafdict[strkey]
                        n.color = n.sig
            n.cost = 1

    def sig_node(self, n):

        if n.sig != -1:
            return n.sig

        key = 0
        for e in n.edgeset:
            key ^= hash(self.sig_node(e.node))
            for r in e.rangeset:
                key ^= hash(r)

        n.sig = key
        #print n.sig

        #print leafdict.items()
        #print len(levelnodes), len(leafdict.items())

    def fdd_mem(self, n):
        mem = 0
        mem += len(n.edgeset) * POINTER_SIZE + NODE_SIZE

        if n.dim == -1:
            mem += len(n.ppc) * RULE_INDEX
            return mem

        for e in n.edgeset:
            mem += len(e.rangeset) * RANGE_SIZE
            mem += self.fdd_mem(e.node)

        return mem


if __name__ == "__main__":
    pc = rule.load_ruleset(sys.argv[1])

    order=[4,0,1,2,3]
    f = FDD(order)

    #the last one is a wild rule
    gc.disable()
    try:
        levelnodes,leafnodes = f.build_fdd(pc)
    except KeyboardInterrupt:
        print 'rangecnt',f.rangecnt, 'edgecnt', f.edgecnt, 'nodecnt',f.nodecnt
    gc.enable()
    print "FDD(mem):", f.fdd_mem(f.root), "bytes"

    cpc = f.firewall_compressor(levelnodes, leafnodes)
    #print cpc

    print "FDD(mem):", f.fdd_mem(f.root), "bytes"

    f3 = FDD(order)
    levelnodes, leafnodes = f3.build_fdd(cpc)
    rr_out = []
    removed_list = []
    f3.redund_remove(leafnodes, rr_out, removed_list)
    print len(removed_list)
    print len(rr_out)

    #for i in f.root.edgeset:
    #    print i.rangeset






