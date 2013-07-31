#!/usr/bin/python


import fileinput
import sys
import re
import os
import rule
import signal
import copy
import gc
import pdb
import razor
from guppy import hpy
from fwsched import Scheduler
from fwsched import PrepSchedData
from collections import deque


RULE_INDEX = 2
RANGE_SIZE = 8
POINTER_SIZE = 4
NODE_SIZE = 12
MAXDIM = 5


class PackRange:
    def __init__(self, r):
        self.r = r
    def __repr__(self):
        return self.r.__repr__()

def pack_raw_pc(raw_pc):
    pc = []
    for pcr in raw_pc:
        prefix = []
        for r in pcr[:len(pcr)-1]:
            pr = PackRange(r)
            prefix.append(pr)

        prefix.append(pcr[len(pcr)-1])

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
    def compress(self):
        i = 0
        label = ""

        while i < len(self.bits):
            j = i+1
            cnt = 1
            while j < len(self.bits):
                if self.bits[i] ^ self.bits[j] == 0:
                    cnt += 1
                    j += 1
                else:
                    break
            label += str(cnt) + "_" + str(self.bits[i]) +"."
            i = j
        return label


    def intbit(self):
        y = 0
        for x in self.bits:
            y |= x
            y <<= 1
        return y

def rset_minus(r, rangeset):
    ret = []
    t = rule.Range(l = r.l, h = r.h)
    for i in xrange(len(rangeset)):
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
        self.no = -1
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
                for i in xrange(len(self.rangeset)):
                    if self.rangeset[i] == other.rangeset[i]:
                        continue
                    else:
                        return False
        return True

    def __del__(self):
        del self.rangeset

    def __repr__(self):
        return self.rangeset.__repr__()

    def __cmp__(self, other):
        return self.rangeset[0].__cmp__(other.rangeset[0])

    @staticmethod
    def merge_edges(edges):
        rangeset = []
        node = edges[0].node

        for e in edges:
            rangeset.extend(e.rangeset)
            #if node != e.node:
            #    raise Exception
        #if v:
        #    print "merge", mark
        rangeset = list(set(rangeset))
        rangeset.sort()

        #if v:
        #    print "merge", mark
        #    print rangeset

        nrangeset=[]
        i = 0
        while i< len(rangeset):
            rt = rangeset[i]
            j = i+1
            while j< len(rangeset):
                if rt.h == rangeset[j].l - 1:
                    rt.h = rangeset[j].h
                    j += 1
                else:
                    break
            nrangeset.append(rt)
            i = j

        rangeset = nrangeset
        e = FDDEdge()
        e.node = node
        e.rangeset = nrangeset
        return e


    def merge(self, other):
        #other.node = self.node
        #other.active = False
        if self.node != other.node:
            raise Exception

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
        self.no = -1

        self.dimavail = None
        self.compressed_edgeset = []

    def __eq__(self,other):
        if self.sig != other.sig:
            return False
        else:
            if self.dim != other.dim:
                return False
            if len(self.edgeset) != len(other.edgeset):
                return False
            for i in xrange(len(self.edgeset)):
                if self.edgeset[i] == other.edgeset[i]:
                    continue
                else:
                    return False
        return True

    def clear(self):
        self.cost = -1
        self.sig = -1
        self.color = -1
        del self.edgeset
        del self.in_edgeset
        if 'ppc' in dir(self):
            del self.ppc

    def edges_check(self):
        rangeset = []
        for e in self.edgeset:
            rangeset.extend(e.rangeset)

        i = 0
        while i < len(rangeset):
            j = i+1
            while j < len(rangeset):
                ret = rangeset[i].insect(rangeset[j])
                if ret != None:
                    print "exp"
                    print rangeset
                    print self.no
                    for e in self.edgeset:
                        print e.no
                    print self.edgeset
                    raise Exception
                j += 1
            i += 1


    def edges_reduce(self):
        #v = False
        #vv = False
        #if self.dim == 1:
        #    for e in self.edgeset:
        #        for r in e.rangeset:
        #            if r.l == 1834040094:
        #                v = True
        #    for e in self.in_edgeset:
        #        for r in e.rangeset:
        #            if r.l == 3919972310:
        #                vv = True

        ndict = {}
        for e in self.edgeset:
            if e.node.color in ndict:
                ndict[e.node.color].append(e)
            else:
                ndict[e.node.color] = [e]
            #if v:
            #    print "e.node.no", e.no

        nedgeset = []
        #if v:
        #    print ndict
        #    print [x.no for x in ndict[0]]

        for key in ndict.keys():
            if len(ndict[key]) == 1:
                #if v and vv:
                #    print "sig"
                #    print key
                #    print ndict[key]
                nedgeset.extend(ndict[key])
            if len(ndict[key]) > 1:
                #if v:
                #    print ndict[key]
                #    print mark
                #if v and vv:
                #    print "mul"
                #    print key
                #    print ndict[key]
                e = FDDEdge.merge_edges(ndict[key])
                nedgeset.append(e)
                #if v and vv:
                #    print "after"
                #    print e



        self.edgeset = nedgeset
        self.edgeset.sort()
        #self.edges_check()
        #if v and vv:
        #    print "bye"

class LinePoints:
    def __init__(self, cord, flag):
        self.x = cord
        #self.i = ri
        self.s = flag

    def __cmp__(self, other):
        if self.x < other.x:
            return -1
        if self.x > other.x:
            return 1
        if self.x == other.x:
#stating points are higher than ending points
            if self.s > other.s:
                return -1
            if self.s < other.s:
                return 1
            if self.s == other.s:
                return 0

    def __repr__(self):
        return (self.x, self.s).__repr__()

def build_line_points(rset):
    rl = list(set(rset))
    pl = []

    for ri in xrange(len(rl)):
        pl.append(LinePoints(rl[ri].l,  1))
        pl.append(LinePoints(rl[ri].h, -1))

    pl.sort()

    prev = pl[0]
    l = len(pl)
    i = 1
    while i < l:
        if pl[i].x == prev.x:
            if (pl[i].s>0) == (prev.s>0):
                if prev.s > 0:
                    prev.s += 1
                else:
                    prev.s -= 1
                del pl[i]
                i -= 1
                l -= 1
        #print prev
        prev = pl[i]
        i+=1

    #print pl
    return pl


class FDD:
    def __init__(self, order):
        self.order = order
        self.root = FDDNode()

        self.nodecnt = 0
        self.edgecnt = 0
        self.rangecnt = 0

    @staticmethod
    def build_interval_fast(rset):
        pl = build_line_points(rset)
        iv = []
        events = {}

        stack = pl[0].s
        prev = pl[0].x
        prev_p = pl[0]

        for p in pl[1:]:

            if p.s > 0:
                if stack != 0:
                    if prev_p.s < 0 and prev == p.x:
                        pass
                    else:
                        iv.append(rule.Range(prev, p.x-1))
                prev = p.x
                stack += p.s
            else:
                iv.append(rule.Range(prev, p.x))
                prev = p.x+1
                stack += p.s

            prev_p = p

        return iv


    @staticmethod
    def build_interval(rset):
#YOU HAVE TO MAKE SURE EVERY RANGE IS NEW!!!
#NOT A REFERENCE!!!
        rl = list(set(rset))
        #print rl
        retl = []
        retl.append(copy.copy(rl[0]))
        #retl = [rl[0]]

        for r in rl[1:]:
            minus = rset_minus(r, retl)
            aux_insects = []
            #if r.h ==1358954495:
            #    print retl

            for ri in xrange(len(retl)):
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
            #bits = bitmap.intbit()
            label = bitmap.compress()

            if label in bms:
                bms[label].append(tnum)
            else:
                bms[label] = [tnum]
            tnum += 1

    def build_node_pc(self, pc, parent, edge):
        nppc = []
        rs = [(pc[x])[parent.dim].r for x in parent.ppc]

        for ri in xrange(len(rs)):
            for er in edge.rangeset:
                if er.within(rs[ri]):
                    nppc.append(parent.ppc[ri])
                    break

        return nppc

    def color_level(self, level):
        sigdict = {}
        for n in level:
            if n.sig in sigdict:
                sigdict[n.sig].append(n)
            else:
                sigdict[n.sig] = [n]

        uniq = []
        color = 0
        for key in sigdict.keys():
            siguniq = []
            siguniq.append(sigdict[key][0])
            sigdict[key][0].color = color
            color += 1
            for n in sigdict[key][1:]:
                uniqflag = True
                for nu in siguniq:
                    if nu == n:
                        for e in n.in_edgeset:
                            e.node = nu
                            nu.in_edgeset.append(e)
                        n.clear()
                        uniqflag = False
                        break
                    else:
                        continue
                if uniqflag:
                    n.color = color
                    color += 1
                    siguniq.append(n)
            uniq.extend(siguniq)

        print len(level), color
        for ni in xrange(len(uniq)):
            uniq[ni].sig = uniq[ni].color

        return uniq

        #level[0].color = 0
        #color = 1
        #uniq = [level[0]]
        #flag = 0

        #for n in level[1:]:
        #    for nu in uniq:
        #        if nu == n:
        #            n.color = nu.color
        #            #n.sig = n.color
        #            for e in n.in_edgeset:
        #                e.node = nu
        #            n.clear()
        #            flag = 1
        #            break
        #        else:
        #            continue

        #    if flag == 0:
        #        n.color = color
        #        #n.sig = color
        #        color += 1
        #        uniq.append(n)
        #    else:
        #        flag = 0

        #for ni in xrange(len(uniq)):
        #    uniq[ni].sig = uniq[ni].color

        #print len(level), len(uniq)
        #return uniq


    def fdd_reduce(self, pc, levelnodes, leafnodes):
        self.process_leafnodes(pc, leafnodes)

        reducednodes = [None for x in xrange(MAXDIM)]
        #mark = None
        #nodemark = None
        for i in xrange(MAXDIM-1, -1, -1):
            #for n in levelnodes[2]:
            #    for e in n.edgeset:
            #        if e.no == 1302:
            #            mark = e
            #            nodemark = e.node
            #            print "epre", n.dim, n.no
            #            print "nodemark", nodemark.no
            #    if n.no== 133:
            #        print "prein", n.edgeset, i

            for n in levelnodes[i]:
                #v = False
                #if n.no == 100:
                #    print "100", n.edgeset, n.dim
                #    v = True

                n.edges_reduce()
                #if mark.rangeset[0].h == 1834040095:
                #    print n.no

                self.sig_node(n)
            reducednodes[i] = self.color_level(levelnodes[i])

        return reducednodes

    def fdd_match(self, trace):

        n = self.root
        t = trace[n.dim]
        d = -1

        while n.dim != -1:
            for e in n.edgeset:
                rmatched = False
                for r in e.rangeset:
                    if r.match(t):
                        ##if v:
                        ##    print r
                        ##    print e
                        n = e.node
                        t = trace[n.dim]
                        rmatched = True
                        break
                if rmatched:
                    break
        if rmatched:
            d = n.ppc[0]

        return (d!=-1), d

    def fdd_compressed_match(self, pc, trace):

        n = self.root
        t = trace[n.dim]
        d = -1

        while n.dim != -1:
            for e in n.compressed_edgeset:
                rmatched = False
                for r in e.rangeset:
                    if r.match(t):
                        n = e.node
                        t = trace[n.dim]
                        rmatched = True
                        break
                if rmatched:
                    break

        if rmatched:
            d = pc[n.ppc[0]][len(self.order)].d

        return (d!=-1), d


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
        #if n.dim ==2 and n.color ==1:
        #    print R
        #    print preplist

        for ri in xrange(len(R)):
            i = R[ri].l
            while i<= R[ri].h:
                rt = copy.copy(preplist[i].r)
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

        #if n.dim ==2 and n.color ==1:
        #    print rangeset
        #    print color


        #print "rangeset", rangeset

        for ci in xrange(len(color)):
            ne = FDDEdge()
            for e in n.edgeset:
                if color[ci] == e.node.color:
                    ne.node = e.node
                    ne.rangeset.append(rangeset[ci])
            n.compressed_edgeset.append(ne)

        #if n.dim ==2 and n.color ==1:
        #    print n.compressed_edgeset


        #pdb.set_trace()

        #return rangeset
        #print rangeset
        #print R



    def compress(self, levelnodes):
        print "firewall compressor"
        for i in xrange(MAXDIM-1, -1, -1):
            for n in levelnodes[i]:
                color, cost, group, preplist = self.prepare_sched(n)
                if n.no == 3:
                    print color
                    print cost
                    print group
                #print color, cost, group
                #print len(color)
                sched = Scheduler(color, cost, group)
                n.cost = sched.FSA_cost(0, len(color)-1)
                sched.FSA_result(0,0,len(color)-1)
                #print sched.R

                self.make_compressed_edgeset(n, sched.R, sched.RC, preplist)

    @staticmethod
    def make_prep(eset):
        prepdict = {}

        for e in eset:
            for r in e.rangeset:
                prep = PrepSchedData(r, e.node.color, 1)
                if e.node.color not in prepdict:
                    prepdict[e.node.color] = [prep]
                else:
                    prepdict[e.node.color].append(prep)

        #print prepdict.values()
        preplist = reduce(lambda x,y: x+y, prepdict.values())
        #print preplist
        preplist.sort()


        seg = []
        i= 0
        while i < len(preplist):
            j = i+1
            while j < len(preplist):
                if preplist[j-1].r.h == preplist[j].r.l -1:
                    j += 1
                else:
                    break
            seg.append((i,j))
            i = j

        color = []
        cost  = {}
        group = []

        for key in prepdict.keys():
            cost[key] = 1
        i=0
        for s in seg:
            color.append([preplist[x].color for x in xrange(s[0], s[1])])

            sgroup = {}
            index = 0
            for c in color[i]:
                if c not in sgroup:
                    sgroup[c] = [index]
                else:
                    sgroup[c].append(index)
                index += 1

            group.append(sgroup)
            i+=1

        #for key in prepdict.keys():
        #    prepdict[key].sort()

        return color, cost, group, preplist, seg

    @staticmethod
    def compress_edgeset(R, RC, preplist, eset, compressed_edgeset):
        rangeset = []
        color = []
        #print preplist
        #print R

        for ri in xrange(len(R)):
            i = R[ri].l
            while i<= R[ri].h:
                rt = copy.copy(preplist[i].r)
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

        #print "rangeset", rangeset

        for ci in xrange(len(color)):
            ne = FDDEdge()
            for e in eset:
                if color[ci] == e.node.color:
                    ne.node = e.node
                    ne.rangeset.append(rangeset[ci])
            compressed_edgeset.append(ne)
                #print "default", rangeset[ci]
        #print "done"


    @staticmethod
    def compress_eset(eset, default_range, default_node):
        color, cost, group, preplist, seg = FDD.make_prep(eset)
        compressed_edgeset = []
        for x in xrange(len(seg)):
            sched = Scheduler(color[x], cost, group[x])
            sched.FSA_cost(0, len(color[x])-1)
            sched.FSA_result(0,0,len(color[x])-1)
            FDD.compress_edgeset(sched.R, sched.RC, preplist[seg[x][0]:seg[x][1]], eset, compressed_edgeset)

        if default_range != None:
            ne = FDDEdge()
            ne.node = default_node
            ne.rangeset.append(default_range)
            compressed_edgeset.append(ne)
        return compressed_edgeset


    def make_razor_compressed_edgeset(self, n, cl):
        color = []
        rangeset = []

        for en in cl:
            if isinstance(en[0], list):
                for r in en[0]:
                    rangeset.append(rule.Range(r[0], r[1]))
                color.append(en[1])
            else:
                rangeset.append(rule.Range(en[0][0], en[0][1]))
                color.append(en[1])

        for ci in xrange(len(color)):
        #to note that this color may contain the same entry
            ne = FDDEdge()
            for e in n.edgeset:
            #this is reduced edgeset, so every edge points to a unique color
                if e.node.color == color[ci]:
                    ne.node = e.node
                    ne.rangeset.append(rangeset[ci])
            n.compressed_edgeset.append(ne)



    def razor_compress(self, levelnodes):
        print "using TCAM Razor"
        for i in xrange(len(self.order)-1, -1, -1):
            for n in levelnodes[i]:
                if n.no == 4:
                    print "here"
                cl, n.cost = razor.compress_node(n)
                #if len(cl)> 1:
                #    print cl
                self.make_razor_compressed_edgeset(n, cl)

    @staticmethod
    def build_bms_fast(i, rset, bms, nppc):
        rset_ppcdict = {}

        for ppc in xrange(len(rset)):
            if rset[ppc] in rset_ppcdict:
                rset_ppcdict[rset[ppc]].append(nppc[ppc])
            else:
                rset_ppcdict[rset[ppc]] = [nppc[ppc]]

        intl_list = [[] for x in xrange(len(i))]
        uniq_rset = rset_ppcdict.keys()

        for ari in xrange(len(i)):
            for r in uniq_rset:
                if i[ari].within(r):
                    intl_list[ari].append(r)

        for ari in xrange(len(i)):
            rtuple = tuple(intl_list[ari])
            if rtuple in bms:
                bms[rtuple].append(ari)
            else:
                bms[rtuple] = [ari]

        return intl_list, rset_ppcdict

    def build_node_pc_fast(self, intl_list, rset_ppcdict, ari_list):
        nppc = []
        for r in intl_list[ari_list[0]]:
            nppc.extend(rset_ppcdict[r])

        nppc = list(set(nppc))
        nppc.sort()

        return nppc

    @staticmethod
    def choose_dim(node, pc):

        d = node.dimavail[0]
        chd = d
        chdi = 0
        rs = [(pc[x])[d].r for x in node.ppc]
        i = FDD.build_interval_fast(rs)

        inum = 0

        for xr in rs:
            for itl in i:
                if itl.within(xr):
                    inum += 1

        chi = i

        for di in xrange(len(node.dimavail)):
            j = 0
            rs = [(pc[x])[node.dimavail[di]].r for x in node.ppc]
            i = FDD.build_interval_fast(rs)

            for xr in rs:
               for itl in i:
                   if itl.within(xr):
                       j+=1

            if j < inum:
                chd = node.dimavail[di]
                chdi = di
                inum = j
                chi = i

        del node.dimavail[chdi]
        #print "avail", node.dimavail
        return chd, chi



    def build_pdd(self, pc):

        print "*building pipeline begins"
        self.root.ppc = xrange(len(pc))
        self.root.no = 0
        self.root.dimavail = range(0,MAXDIM)
        thislevel = [self.root]
        nextlevel = []
        levelnodes = []
        bms = {}

        for t in xrange(MAXDIM):
            for node in thislevel:
                node.dim, i = FDD.choose_dim(node, pc)
                #print node.dim
                rs = [(pc[x])[node.dim].r for x in node.ppc]
                intl_list, rset_ppcdict = FDD.build_bms_fast(i, rs, bms, node.ppc)
                #print len(bms.values())
                #sys.exit(0)
                for equalrs in bms.values():
                    edge = FDDEdge()
                    edge.no = self.edgecnt
                    self.edgecnt += 1
                    for ri in equalrs:
                        edge.rangeset.append(i[ri])
                        self.rangecnt += 1
                    edge.node = FDDNode()
                    edge.node.in_edgeset.append(edge)
                    self.nodecnt += 1
                    edge.node.no = self.nodecnt
                    #edge.node.ppc = self.build_node_pc(pc, node, edge)
                    edge.node.ppc = self.build_node_pc_fast(intl_list, rset_ppcdict, equalrs)
                    #print edge.node.ppc
                    edge.node.dimavail = copy.copy(node.dimavail)

                    nextlevel.append(edge.node)
                    node.edgeset.append(edge)
                #node.edges_check()


                del node.ppc
                del bms
                bms = {}
                #if node.no == 133:
                #    print node.edgeset
                #for e in node.edgeset:
                #    for r in e.rangeset:
                #        if r.l == 1834040094:
                #            print e

            levelnodes.append(thislevel)
            print "finish level"
            print "nodecnt", self.nodecnt
            print "edgecnt", self.edgecnt
            print "rangecnt", self.rangecnt
            thislevel = nextlevel
            nextlevel = []

        print "\n*building complete\n"
        return levelnodes, thislevel


    def build_fdd(self, pc):
        print "*building FDD begins"
        self.root.ppc = xrange(len(pc))
        self.root.no = 0
        thislevel = [self.root]
        nextlevel = []
        levelnodes = []
        bms = {}

        for dim in self.order:
            for node in thislevel:
                node.dim = dim
                rs = [(pc[x])[dim].r for x in node.ppc]
                #if dim==4:
                    #if rule.Range(l=0,h=255) not in rs:
                    #    print rs

                i = FDD.build_interval_fast(rs)
                #if dim == 4:
                #print i
                #print len(i)
                #self.build_bms(i, rs, bms)
                intl_list, rset_ppcdict = FDD.build_bms_fast(i, rs, bms, node.ppc)
                #print len(bms.values())
                #sys.exit(0)


                for equalrs in bms.values():
                    edge = FDDEdge()
                    edge.no = self.edgecnt
                    self.edgecnt += 1
                    for ri in equalrs:
                        edge.rangeset.append(i[ri])
                        self.rangecnt += 1
                    edge.node = FDDNode()
                    edge.node.in_edgeset.append(edge)
                    self.nodecnt += 1
                    edge.node.no = self.nodecnt
                    #edge.node.ppc = self.build_node_pc(pc, node, edge)
                    edge.node.ppc = self.build_node_pc_fast(intl_list, rset_ppcdict, equalrs)
                    nextlevel.append(edge.node)
                    node.edgeset.append(edge)
                #node.edges_check()


                del node.ppc
                del bms
                bms = {}
                #if node.no == 133:
                #    print node.edgeset
                #for e in node.edgeset:
                #    for r in e.rangeset:
                #        if r.l == 1834040094:
                #            print e

            levelnodes.append(thislevel)
            #levelcnt += 1
            #print "finish", dim
            #print "nodecnt", self.nodecnt
            #print "edgecnt", self.edgecnt
            #print "rangecnt", self.rangecnt
            thislevel = nextlevel
            nextlevel = []

        print "\n*building FDD complete\n"
        return levelnodes, thislevel

    def output_compressed_list(self, pc, n, prefix, raw_pc):
        if n.dim == -1:
            #print prefix
            prefix[len(self.order)] = rule.Decision(pc[n.ppc[0]][len(self.order)].d)
            raw_pc.append(list(prefix))
            return

        for e in n.compressed_edgeset:
            for r in e.rangeset:
                prefix[n.dim] = r
                self.output_compressed_list(pc, e.node, prefix, raw_pc)


    def firewall_compressor(self, pc, levelnodes, leafnodes):
        print "*compress the ruleset using Firewall Compressor"
        reducednodes = self.fdd_reduce(pc, levelnodes, leafnodes)
        self.compress(reducednodes)
        prefix = [ None for x in xrange(len(self.order)+1) ]
        raw_pc = []
        self.output_compressed_list(pc,self.root, prefix, raw_pc)
        print "compress the ruleset raw:", len(raw_pc)
        #print raw_pc
        return pack_raw_pc(raw_pc)

    def output_pdd_list(self, pc, reducednodes):
        levellist = [[] for x in xrange(MAXDIM+1)]

        for d in xrange(MAXDIM):
            for n in reducednodes[d]:
                for e in n.compressed_edgeset:
                    for r in e.rangeset:
                        if d != MAXDIM - 1:
                            levellist[d].append((n.dim, n.color,r,e.node.color))
                        else:
                            levellist[d].append((n.dim, n.color,r,pc[e.node.ppc[0]][MAXDIM].d))
        return levellist


    def output_tcamsplit(self, pc, reducednodes):
        levellist = [[] for x in xrange(MAXDIM)]

        for d in xrange(MAXDIM):
            for n in reducednodes[d]:
                for e in n.compressed_edgeset:
                    for r in e.rangeset:
                        if d != MAXDIM - 1:
                            levellist[n.dim].append((n.color,r,e.node.color))
                        else:
                            levellist[n.dim].append((n.color,r,pc[e.node.ppc[0]][MAXDIM].d))

        #print "0", len(levellist[0])

        #sort_table_list = [ [] for x in xrange(MAXDIM)]

        #for d in self.order:
        #    table_dict = {}
        #    for entry in levellist[d]:
        #        if entry[0] in table_dict:
        #            table_dict[entry[0]].append((entry[1], entry[2]))
        #        else:
        #            table_dict[entry[0]] = []
        #            table_dict[entry[0]].append((entry[1], entry[2]))


        #    for key in table_dict.keys():
        #        for x in table_dict[key]:
        #            sort_table_list[d].append((key, x[0], x[1]))

        #print "0", len(sort_table_list[0])

        #i = 0
        #for d in self.order:
        #    #print ""
        #    #print "tcam", i, "dim", d
        #    tcam_entries = 0
        #    for entry in sort_table_list[d]:
        #        tcam_entries += entry[1].prefix_entries()
        #        #print entry
        #    #print len(sort_table_list[d])
        #    #print tcam_entries
        #    i+=1


        return levellist


    def tcam_split(self, pc, levelnodes, leafnodes):
        print "*compress the ruleset TCAM SPLIT"
        reducednodes = self.fdd_reduce(pc, levelnodes, leafnodes)
        self.compress(reducednodes)
        #self.razor_compress(reducednodes)
        gc.collect()
        return self.output_tcamsplit(pc, reducednodes)


    def redund_remove_semantic(self, leafnodes, rr_output, removed_list, pc):
        ppcdict = {}
        conlist = [n.ppc for n in leafnodes]
        for ni in xrange(len(conlist)):
            for ppc in conlist[ni]:
                if ppc in ppcdict:
                    ppcdict[ppc].append(ni)
                else:
                    ppcdict[ppc] = [ni]

        rules = sorted(ppcdict.keys(), reverse = True)
        for ppc in rules:
            redund = True
            for ni in ppcdict[ppc]:
                if len(conlist[ni]) == 1:
                    redund = False
                    break
                if conlist[ni][0] == ppc:
                    j = conlist[ni][1]
                    #print j
                    #print pc[j]
                    #print pc[ppc][len(self.order)]
                    if pc[j][len(self.order)].d != pc[ppc][len(self.order)].d:
                        redund = False
                        break

            if redund:
                removed_list.append(ppc)
                for ni in ppcdict[ppc]:
                    conlist[ni].remove(ppc)
            else:
                rr_output.append(ppc)

        rr_output.sort()


    def redund_remove(self, leafnodes, rr_output, removed_list):
        ppcdict = {}
        for ni in xrange(len(leafnodes)):
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



    def process_leafnodes(self, pc, levelnodes):
        nextlevel = []
        leafdict = {}
        leafcolor = 0
        uniq = {}
        for n in levelnodes:
            if n.sig == -1:
                if len(n.ppc) != 0:
                # n is the leaf
                    #strkey = reduce(lambda x,y: str(x)+"."+str(y), n.ppc)
                    #strkey = n.ppc[0]
                    strkey = pc[n.ppc[0]][MAXDIM].d
                    #print strkey
                    if strkey not in leafdict:
                        leafdict[strkey] = leafcolor
                        uniq[strkey] = n
                        n.sig = leafcolor
                        n.color = n.sig
                        leafcolor += 1
                    else:
                        n.sig = leafdict[strkey]
                        n.color = n.sig
                        for e in n.in_edgeset:
                            e.node = uniq[strkey]
                            uniq[strkey].in_edgeset.append(e)
                        n.clear()
                else:
                    raise Exception
            else:
                raise Exception

        for n in uniq.values():
            n.cost = 1

        #print "leafcolor", leafcolor
        print len(levelnodes), leafcolor

    def sig_node(self, n):

        if n.sig != -1:
            return n.sig

        key = 0
        key ^= n.dim
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


    #cpc = f.firewall_compressor(pc, levelnodes, leafnodes)
    tcam_entries = 0
    tcam = f.tcam_split(pc, levelnodes, leafnodes)
    for t in tcam:
        tcam_entries += reduce(lambda x,y: x+y, map(lambda x: x[1].prefix_entries(), t))

    tcam_raw = rule.tcam_entry_raw(pc)
    print "tcam raw: ", tcam_raw
    print "tcam split entries: ", tcam_entries
    print "compression ratio: ", float(tcam_entries)/(4*tcam_raw)

    h = hpy()
    print h.heap()



    #f.fdd_reduce(pc, levelnodes, leafnodes)

    #traces = rule.load_traces("acl1_2_0.5_-0.1_1K_trace")
    #for ti in range(len(traces)):
    #    d1 = f.fdd_match( traces[ti])
    #    d2 = rule.match(pc, traces[ti])

    #    #if d1 == d2[1]:
    #    #    pass
    #    #else:
    #    #    print t, d1, d2
    #    #if ti == 779:
    #    #    v = True
    #    #    f.fdd_match(traces[ti],v)

    #    if d1[0] == d2[0] and pc[d1[1]][len(f.order)].d == pc[d2[1]][len(f.order)].d:
    #    #if d1[0] == d2[0] and d1[1] == pc[d2[1]][len(f.order)].d:
    #        pass
    #    else:
    #        print traces[ti], ti, d2[1], pc[d1[1]][len(f.order)].d, pc[d2[1]][len(f.order)].d
    #        #print traces[ti], ti, d2[1], d1[1], pc[d2[1]][len(f.order)].d
    #        #d1 = f.fdd_match(traces[ti], v)


    #print cpc

    #print "FDD(mem):", f.fdd_mem(f.root), "bytes"

    #f3 = FDD(order)
    #levelnodes, leafnodes = f3.build_fdd(cpc)
    ##levelnodes, leafnodes = f3.build_fdd(pc)
    #rr_out = []
    #removed_list = []
    #f3.redund_remove_semantic(leafnodes, rr_out, removed_list, cpc)
    ##f3.redund_remove(leafnodes, rr_out, removed_list)

    #print len(removed_list)
    #print len(rr_out)
    ##print removed_list
    #print "compression :", len(rr_out)/float(len(pc)) * 100, "%"

    #final_list = [cpc[x] for x in rr_out]
    #print "tcam raw", rule.tcam_entry_raw(cpc)

    ##print final_list
    #rule.pc_equality(pc, final_list, "fw1_2_0.5_-0.1_1K_trace")

    #for i in f.root.edgeset:
    #    print i.rangeset






