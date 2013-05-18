#!/usr/bin/python


import fileinput
import sys
import re
import os
import rule

RULE_INDEX = 2
RANGE_SIZE = 8
POINTER_SIZE = 4
NODE_SIZE = 1


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


class FDDNode:
    def __init__(self):
        self.dim = -1
        self.edgeset = []
        self.ppc = []
        self.sig = -1
        self.color = -1

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
                if not retl[ri].within(r):
                    insect = retl[ri].insect(r)
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
        print color

    def fdd_reduce(self):
        level_dict = {}
        level_dict[0] = [self.root]

        for i in range(len(self.order)-1):
            level_dict[i+1] = []
            for n in level_dict[i]:
                for e in n.edgeset:
                    level_dict[i+1].append(e.node)

        for i in range(len(self.order)-1, -1, -1):
            self.color_level(level_dict[i])
            print len(level_dict[i]), i



    def fdd_match(self, trace):
        pass

    def build_fdd(self, pc):
        self.root.ppc = range(len(pc))
        thislevel = [self.root]
        nextlevel = []
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
                #    print i
                #print len(i)
                self.build_bms(i, rs, bms)


                for equalrs in bms.values():
                    edge = FDDEdge()
                    self.edgecnt += 1
                    for ri in equalrs:
                        edge.rangeset.append(i[ri])
                        self.rangecnt += 1
                    edge.node = FDDNode()
                    self.nodecnt += 1
                    edge.node.ppc = self.build_node_pc(pc, node, edge)
                    nextlevel.append(edge.node)
                    node.edgeset.append(edge)

                del node.ppc
                del bms
                bms = {}


            del thislevel
            print "finish", dim
            print "nodecnt", self.nodecnt
            print "edgecnt", self.edgecnt
            print "rangecnt", self.rangecnt
            thislevel = nextlevel
            nextlevel = []

        self.sigleafnode(thislevel)
        self.sig_node(self.root)
        self.fdd_reduce()

    def sigleafnode(self, levelnodes):

        nextlevel = []
        leafdict = {}
        leafcolor = 0
        for n in levelnodes:
            if n.sig == -1:
                if len(n.ppc) != 0:
                # n is the leaf
                    strkey = reduce(lambda x,y: str(x)+"."+str(y), n.ppc)
                    #print strkey
                    if strkey not in leafdict:
                        leafdict[strkey] = leafcolor
                        n.sig = leafcolor
                        n.color = n.sig
                        leafcolor += 1
                    else:
                        n.sig = leafdict[strkey]
                        n.color = n.sig

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




        #TO: an isomorphic code here

if __name__ == "__main__":
    pc = rule.load_ruleset(sys.argv[1])

    order=[4,0,1,2,3]
    f = FDD(order)
    #the last one is a wild rule

    f.build_fdd(pc[1:len(pc)-1])
    print "FDD(mem):", f.fdd_mem(f.root), "bytes"

    #for i in f.root.edgeset:
    #    print i.rangeset






