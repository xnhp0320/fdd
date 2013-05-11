#!/usr/bin/python


import fileinput
import sys
import re
import os
import rule



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

class FDDEdge:
    def __init__(self):
        self.rangeset = []
        self.node = None

class FDDNode:
    def __init__(self):
        self.dim = -1
        self.edgeset = []
        self.pc = []

class FDD:
    def __init__(self, order):
        self.order = order
        self.root = FDDNode()

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

    def build_node_pc(self, parent, edge):
        npc = []
        rs = [x[parent.dim].r for x in parent.pc]

        for ri in range(len(rs)):
            for er in edge.rangeset:
                if er.within(rs[ri]):
                    npc.append(parent.pc[ri])
                    break;

        return npc

    def isomorphic(self, level):
        pass

    def fdd_match(self, trace):
        pass

    def build_fdd(self, pc):
        self.root.pc = pc
        thislevel = [self.root]
        nextlevel = []
        bms = {}

        for dim in self.order:
            nodecnt = 0
            edgecnt = 0
            for node in thislevel:
                node.dim = dim
                rs = [x[dim].r for x in node.pc]
                #if dim==4:
                    #if rule.Range(l=0,h=255) not in rs:
                    #    print rs

                i = self.build_interval(rs)
                #if dim == 4:
                    #print node.pc
                    #print i
                #print len(i)
                self.build_bms(i, rs, bms)


                for equalrs in bms.values():
                    edge = FDDEdge()
                    edgecnt += 1
                    for ri in equalrs:
                        edge.rangeset.append(i[ri])
                    edge.node = FDDNode()
                    nodecnt += 1
                    edge.node.pc = self.build_node_pc(node, edge)
                    nextlevel.append(edge.node)
                    node.edgeset.append(edge)

                del node.pc
                del bms
                bms = {}


            del thislevel
            print "finish", dim
            print "nodecnt", nodecnt
            print "edgecnt", edgecnt
            thislevel = nextlevel
            nextlevel = []

        #TO: an isomorphic code here

if __name__ == "__main__":
    pc = rule.load_ruleset(sys.argv[1])
    print len(pc)

    order=[0,1,2,3,4]
    f = FDD(order)
    f.build_fdd(pc[0:len(pc)-1])

    #for i in f.root.edgeset:
    #    print i.rangeset






