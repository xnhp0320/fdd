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
#stating points are lower than ending points
            if self.s > other.s:
                return -1
            if self.s < other.s:
                return 1
            if self.s == other.s:
                #return 0
                if self.s == -1:
                    return 0
                else:
#end points compares, if end points are ``far'', it should be put to the right.
                    if self.end.x > other.end.x:
                        return 1
                    if self.end.x < other.end.x:
                        return -1
                    else:
                        raise Exception

    def __repr__(self):
        return (self.x, self.s).__repr__()

class RectPoints:
    def __init__(self, xP, yP):
        self.xP = xP
        self.yP = yP

    def __repr__(self):
        return self.xP.__repr__() + self.yP.__repr__()

def build_line(rl):

    pl = []
    for ri in xrange(len(rl)):
        rp1 = RangePoints(rl[ri].l,  1)
        rp2 = RangePoints(rl[ri].h, -1)
        RangePoints.set_end(rp1, rp2)
        RangePoints.set_end(rp2, rp1)
        pl.append(rp1)
        pl.append(rp2)

    pl.sort()

    return pl


def check_collide(event, xd, new_e, rl2d, pset):
    check_set = []
    for r in event:
        check_set.extend(xd[r])

    yrange_dict = {}
    for r2i in check_set:
        if rl2d[r2i][1] in yrange_dict:
            yrange_dict[rl2d[r2i][1]].append(r2i)
        else:
            yrange_dict[rl2d[r2i][1]] = [r2i]


    pl = build_line(yrange_dict.keys())

    prev = pl[0]
    l = len(pl)
    i = 1
    stack = prev.s
    yrect = yrange_dict[rule.Range(prev.x, prev.end.x)]
    if len(yrect) > 1:
        pset.extend(yrect[1:])
        for y in yrect[1:]:
            xd[rl2d[y][0]].remove(y)

    while i < l:
        if stack > 0:
            if pl[i].s > 0:
                yrect = yrange_dict[rule.Range(pl[i].x, pl[i].end.x)]
                #print yrect
                #if len(yrect) > 1:
                #    print "here"
                #pset.append(yrect[0])
                pset.extend(yrect)

                #xd[rl2d[yrect[0]][0]].remove(yrect[0])
                for y in yrect:
                    xd[rl2d[y][0]].remove(y)

                pl[i].s = 0
                pl[i].end.s = 0
        #when stack is zero which means that the we are at a begin point
        if stack == 0 and pl[i].s > 0:
            #print pl[i].s
            yrect = yrange_dict[rule.Range(pl[i].x, pl[i].end.x)]
            if len(yrect) > 1:
                pset.extend(yrect[1:])
                for y in yrect[1:]:
                    xd[rl2d[y][0]].remove(y)

        stack += pl[i].s
        prev = pl[i]
        i+=1

    pset.sort()




def split_kset_2d(rl2d, kset):
    if len(rl2d) == 0:
        return

    #first do it in X axis
    xrange_dict = {}
    for r2i in xrange(len(rl2d)):
        if rl2d[r2i][0] in xrange_dict:
            xrange_dict[rl2d[r2i][0]].append(r2i)
        else:
            xrange_dict[rl2d[r2i][0]] = [r2i]


    pl = build_line(xrange_dict.keys())

    prev = pl[0]
    l = len(pl)
    i = 1
    prune_set = []

    new_event = rule.Range(prev.x, prev.end.x)
    event = [new_event]
    check_collide(event, xrange_dict, new_event, rl2d, prune_set)

    while i < l:
        if len(event) > 0:
            if pl[i].s > 0:
                new_event = rule.Range(pl[i].x, pl[i].end.x)
                event.append(new_event)
                check_collide(event, xrange_dict, new_event, rl2d, prune_set)
                #pl[i].s = 0
                #pl[i].end.s = 0
            else:
                event.remove(rule.Range(pl[i].end.x, pl[i].x))

        prev = pl[i]
        i+=1

    left_set = []
    curr_set = []
    for k in prune_set:
        left_set.append(rl2d[k])
    for x in xrange(len(rl2d)):
        if x not in prune_set:
            curr_set.append(rl2d[x])

    kset.append(curr_set)
    split_kset_2d(left_set, kset)

def split_kset_optimal(rl, kset):
    if len(rl) == 0:
        return

    rl_sort = sorted(rl, key=lambda r:r.h)
    prune_set = []

    end = rl_sort[0].h
    tmp = []
    tmp.append(rl_sort[0])
    for r in rl_sort[1:]:
        if r.l <= end:
            prune_set.append(r)
        else:
            tmp.append(r)
            end = r.h
    kset.append(tmp)

    split_kset_optimal(prune_set, kset)



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
    #split_kset_2d([a,b,c,d,e,f],kset)
    #split_kset_2d([(a,b),(c,d),(e,f)],kset)

    #print kset

    pc = rule.load_ruleset(sys.argv[1])

    rl = [ x[0].r for x in pc]
    #rl2d = [(x[4].r, x[1].r) for x in pc]
    #rl2d = [(rule.Range(0, 4294967295), rule.Range(0,4294967295)), (rule.Range(930852624, 930852625), rule.Range(0,4294967295)), (rule.Range(0,2147483647), rule.Range(0, 4294967295)), (rule.Range(0,1073741823), rule.Range(0, 4294967295))]

    #rset = list(set(rl2d))
    rset = list(set(rl))

    split_kset(rset, kset)
    #split_kset_2d(rset, kset)
    #print kset
    print len(kset)
    print map(len, kset)
    #for x in kset:
    #    print ""
    #    print x





