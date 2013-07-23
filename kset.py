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


class RangePoints:
    def __init__(self, cord, flag):
        self.x = cord
        #self.i = ri
        self.s = flag
        self.end = None

    @staticmethod
    def set_end(x, y):
        x.end = y

    def __cmp__(self, other):
        if not isinstance(other, RangePoints):
            return -1

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

def split_kset(rl, kset):
    """make sure rlist is a unique range set"""

    if len(rl) == 0:
        return

    pl = []
    for ri in xrange(len(rl)):
        rp1 = RangePoints(rl[ri].l,  1)
        rp2 = RangePoints(rl[ri].h, -1)
        RangePoints.set_end(rp1, rp2)
        pl.append(rp1)
        pl.append(rp2)

    pl.sort()

    prev = pl[0]
    l = len(pl)
    i = 1
    stack = prev.s

    prune_set = []

    while i < l:
        if stack > 0:
            if pl[i].s > 0:
                prune_set.append(pl[i])
                prune_set.append(pl[i].end)
                pl[i].s = 0
                pl[i].end.s = 0

        stack += pl[i].s
        prev = pl[i]
        i+=1

    curr_rl = []
    for p in pl:
        if p.s != 0 and p.end != None:
            curr_rl.append(rule.Range(p.x, p.end.x))

    kset.append(curr_rl)

    left_rl = []
    for p in prune_set:
        if p.end != None:
            left_rl.append(rule.Range(p.x, p.end.x))

    split_kset(left_rl, kset)



if __name__ == "__main__":
    a = rule.Range(1,2)
    b = rule.Range(5,6)
    c = rule.Range(1,9)
    d = rule.Range(2,10)
    e = rule.Range(1,10)
    f = rule.Range(9,10)

    kset = []
    #split_kset([a,b,c,d,e,f],kset)

    #print kset

    pc = rule.load_ruleset(sys.argv[1])

    rl = [ x[0].r for x in pc]
    rset = list(set(rl))

    split_kset(rset, kset)
    print kset
    print len(kset)





