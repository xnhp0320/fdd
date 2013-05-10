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


class FDDNode:
    def __init__(self, dim):
        self.dim = dim
        self.edge = []

class Edge:
    def __init__(self):
        self.rangeset = []

class FDD:
    def __init__(self, order):
        self.order = order
        self.bms = {}
        self.root = FDDNode(self.order[0])

    def build_interval(self, rset):
        l = []
        for r in rset:
            l.append(r.l)
            l.append(r.h)
        s = set(l)
        l = list(s)
        l.sort()

        i = []

        for x in range(0, len(l)-1):
            i.append((l[x], l[x+1]))

        return i

    def build_bms(self, i, rset):
        """ i is the interval"""
        t = [(r.l, r.h) for r in rset]

        tnum = 0
        for atomic in i:
            bitmap = Bitmap(len(rset))
            num = 0
            for r in t:
                if r[0] <= atomic[0] and r[1] >= atomic[1]:
                    bitmap.setbit(num)
                else:
                    bitmap.clearbit(num)
                num += 1

            #print bitmap.intbit()

            if bitmap.intbit() in self.bms:
                self.bms[bitmap.intbit()].append(tnum)
            else:
                self.bms[bitmap.intbit()] = [tnum]
            tnum += 1



    def build_fdd(self, pc):
        rs = [x[self.order[0]].r for x in pc]
        i = self.build_interval(rs)
        self.build_bms(i, rs)








if __name__ == "__main__":
    pc = rule.load_ruleset(sys.argv[1])

    f = FDD()
    f.build_fdd(pc)






