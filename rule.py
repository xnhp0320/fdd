#!/usr/bin/python


import fileinput
import sys
import re
import os
import subprocess
import random
from trie import *

def zeros(n):
    return (0 for i in range(n))

class Range:
    def __init__(self, l=0, h=0, b=32):
        self.h = h
        self.l = l
        self.bits = b

    def __repr__(self):
        return str(self.l) + " : " + str(self.h)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.h == other.h and self.l == other.l

    def __ne__(self, other):
        return not self.__eq__(other)

    def is_large(self, fac):
        if (self.h - self.l + 1)/float(1<<self.bits) > fac:
            return True
        else:
            return False

    def match(self, v):
        if v >= self.l and v <= self.h:
            return True
        else:
            return False

    def within(self, other):
        if not isinstance(other, self.__class__):
            return False
        if other.l <= self.l and other.h >= self.h:
            return True
        else:
            return False

    def minus(self, other):
        ret = []
        if not isinstance(other, self.__class__):
            return None
        if self.l < other.l:
            ret.append(Range(l=self.l, h = min(self.h, other.l -1)))
            if self.h > other.h:
                ret.append(Range(l=other.h+1, h = self.h))
        else:
            if other.h < self.h:
                ret.append(Range(l=max(self.l, other.h+1), h= self.h))
            else:
                ret= []

        return ret

    def __cmp__(self, other):
        if self.l < other.l:
            return -1
        if self.l > other.l:
            return 1
        if self.l ==  other.l:
            return 0

    def __hash__(self):
        return hash(self.l) ^ hash(self.h)

    def insect(self, other):
        if not isinstance(other, self.__class__):
            return None
        if self.l <= other.l:
            if other.l <= self.h:
                ret = Range(l=other.l, h=min(self.h,other.h))
                return ret
            else:
                return None
        else:
            if other.h >= self.l:
                ret = Range(l=self.l, h = min(self.h, other.h))
                return ret
            else:
                return None

    @staticmethod
    def prefix_entries_r(l, h, bits, prefix_list):
        c = 1
        b = 0

        def tailzeros(l, bits):
            z = 0
            if l == 0:
                return bits

            while z < bits:
                if l & 1 == 1:
                    return z
                else:
                    z += 1
                    l >>= 1

        z = tailzeros(l, bits)
        while l+b <= h and b <= (1<<z) - 1:
            b<<=1
            b|=1
        b >>= 1

        prefix_list.append(Range(l, l+b))
        if l+b+1 <= h:
            c += Range.prefix_entries_r(l+b+1, h, bits, prefix_list)

        return c

    def prefix_entries(self):
        prefix_list = []
        c = Range.prefix_entries_r(self.l, self.h, self.bits, prefix_list)
        #print prefix_list, len(prefix_list)
        return c



class Port:
    def __init__(self):
        self.r = Range(b=16)


    def __repr__(self):
        return self.r.__repr__()

    def __eq__(self, other):
        return isinstance(other,self.__class__) and self.r.__eq__(other.r)

    def __ne__(self, other):
        return not self.__eq__(other)

    def parse(self,s):
        m = re.match(r"(\d+)\s:\s(\d+)", s)
        (self.r.l, self.r.h) = (int(m.group(1)), int(m.group(2)))
        #print self

    def random(self):
        self.r.l = random.randint(0, (1<<16) - 1)
        self.r.h = random.randint(self.r.l + 1, (1<<16)-1)

class Pro:
    def __init__(self):
        self.r = Range(b=8)

    def __repr__(self):
        if self.r.h == 255 and self.r.l == 0:
            s="0x00/0x00"
        else:
            s="0x%x/0x%x" % (self.r.l, 255)
        return s

    def __eq__(self, other):
        return isinstance(other,self.__class__) and self.r.__eq__(other.r)

    def __ne__(self, other):
        return not self.__eq__(other)

    def parse(self, s):
        m = re.match(r"(0[xX][\da-fA-F]+)/(0[xX][\da-fA-F]+)", s)
        if int(m.group(1), 16) == 0 :
            self.r.l = 0
            self.r.h = 255
        else:
            self.r.l = int(m.group(1), 16)
            self.r.h = int(m.group(1), 16)
       # print self

    def random(self):
        self.r.l = random.randint(0, (1<<8)-1)
        self.r.h = self.r.l

class Decision:
    def __init__(self,d):
        self.d = d
    def random(self,d):
        self.d = random.randint(0,d-1)
    def __repr__(self):
        return str(self.d)


class IP:
    def __init__(self):
        (self.b1, self.b2, self.b3 , self.b4) = zeros(4)
        self.prefixlen = 0
        self.r = Range(b=32)

    def __repr__(self):
        return str(self.b1)+"."+str(self.b2)+"."+str(self.b3)+"."+str(self.b4) + "/" + str(self.prefixlen)

    def __eq__(self, other):
        return isinstance(other,self.__class__) and self.r.__eq__(other.r)

    def __ne__(self, other):
        return not self.__eq__(other)

    def parse(self, s):
        #print s
        m = re.match(r"(?P<b1>\d+)\.(?P<b2>\d+)\.(?P<b3>\d+)\.(?P<b4>\d+)/(?P<len>\d+)", s)
        (self.b1, self.b2, self.b3, self.b4) = (int(m.group('b'+str(s))) for s in range(1, 5))
        self.prefixlen = int(m.group('len'))

        self.r.l = (self.b1<<24) + (self.b2 << 16) + (self.b3 << 8) + self.b4
        mask =  0xffffffff << (32 - self.prefixlen)
        self.r.l = self.r.l & mask
        #print "%x" % self.r.l
        tail = 0xffffffff >> self.prefixlen
        self.r.h = self.r.l | tail
        #print "%x" % self.r.h
        #print self

    def prefix(self):
        return self.r.l >> (32- self.prefixlen), self.prefixlen

    def random(self, prefix):
        v = random.randint(0, (1<<prefix) -1)
        self.r.l = v << (32 - prefix)
        self.r.h = self.r.l + (1<<(32-prefix)) - 1
        self.prefixlen = prefix

        self.b1 = self.r.l >> 24
        self.b2 = (self.r.l  & 0x00FF0000 ) >> 16
        self.b3 = (self.r.l & 0x0000FF00) >> 8
        self.b4 = self.r.l & 0xFF



def rule_parse(pc, line, deci):
    #print line
    m = re.match(r"@(?P<sip>\d+\.\d+\.\d+\.\d+/\d+)\t"
                    r"(?P<dip>\d+\.\d+\.\d+\.\d+/\d+)\t"
                    r"(?P<sp>\d+\s:\s\d+)\t"
                    r"(?P<dp>\d+\s:\s\d+)\t"
                    r"(?P<p>0[xX][0-9a-fA-F]+/0[xX][0-9a-fA-F]+).*", line)


    if m is None:
        print "parse error"
        print line
        return

    sip = IP()
    sip.parse(m.group('sip'))

    dip = IP()
    dip.parse(m.group('dip'))

    sp = Port()
    sp.parse(m.group('sp'))

    dp = Port()
    dp.parse(m.group('dp'))

    p = Pro()
    p.parse(m.group('p'))

    d = Decision(deci)
    #d.random(2)

    pc.append((sip, dip, sp, dp, p, d))




def classify(path):
    acl = []
    fw = []
    ipc = []

    fs = os.listdir(path)
    for f in fs:
        #print f
        m = re.match(r"(acl|ipc|fw)\d.*", f)
                #"\d_([-]*\d(\.\d+)*)_([-]*\d(\.\d+)*)_([-]*\d(\.\d+)*)_\d+K", f)
        if m:
            if m.group(1) == "acl":
                acl.append(f)
            if m.group(1) == "fw":
                fw.append(f)
            if m.group(1) == "ipc":
                ipc.append(f)

    print (acl, fw, ipc)
    return (acl, fw, ipc)


def load_ruleset(path):
    pc = []
    deci = 0
    for line in fileinput.input(path):
        #deci ^= 1
        rule_parse(pc, line, deci)
        deci += 1
    return pc

def match(pc, trace):
    l = len(pc[0])
    lt = len(trace)

    if l != lt + 1:
        print "wrong config: pc len: ", len(pc[0]), " and trace len: ", len(trace)
        raise Exception

    matched = True
    matchno = 0

    for ri in range(len(pc)):
        rule = pc[ri]
        matched = True

        for ti in range(len(rule)-1):
            ret = rule[ti].r.match(trace[ti])
            if ret == False:
                matched = False
                break

        if matched:
            matchno = ri
            return matched, matchno

    return False, -1

def load_traces(f):
    traces = []
    for line in fileinput.input(f):
        m = re.match("^(\d+)\s(\d+)\s(\d+)\s(\d+)\s(\d+).*", line)
        #print m.groups()
        traces.append([int(x) for x in m.groups()])

    return traces


def test_equal(pc1, pc2, traces):

    tuples1 = len(pc1[0]) - 1
    tuples2 = len(pc2[0]) - 1

    equal = True
    for ti in range(len(traces)):
        matched1, matchno1 = match(pc1, traces[ti])
        matched2, matchno2 = match(pc2, traces[ti])

        if matched1 == matched2:
            if matched1 == False:
                continue
            else:
                d1 = pc1[matchno1][tuples1].d
                d2 = pc2[matchno2][tuples2].d
                if d1 == d2:
                    continue
                else:
                    equal = False
                    break
        else:
            equal = False
            break

    if equal:
        print "by this trace, these two pc is equal"
    else:
        print "no equal at pc1:", matched1,
        print matchno1,pc1[matchno1][tuples1].d,
        print " pc2:", matched2, matchno2, pc2[matchno2][tuples2].d
        print " at trace: ", ti


def pc_equality(pc1, pc2, tf):
    traces = load_traces(tf)
    test_equal(pc1, pc2, traces)

def pc_uniform(ipnum, num):
    pc = []
    iplist = []
    portlist = []
    prolist= []

    for i in xrange(ipnum):
        ip = IP()
        ip.random(24)
        iplist.append(ip)

    port = Port()
    port.r.l = 0
    port.r.h = 65535

    pro = Pro()
    pro.r.l = 6
    pro.r.h = 6


    while True:
        srcip = iplist[random.randint(0, len(iplist)-1)]
        dstip = iplist[random.randint(0, len(iplist)-1)]
        sp = port
        dp = port
        pro = pro
        d = Decision(0)
        d.random(2)
        pc.append((srcip, dstip, sp, dp, pro, d))
        if len(pc) == num:
            break

    rule_parse(pc, "@0.0.0.0/0\t0.0.0.0/0\t0 : 65535\t0 : 65535\t0x00/0x00", 0)

    return pc




def pc_syn(ipnum, portnum, pronum, num):
    pc = []
    iplist = []
    portlist = []
    prolist= []

    for i in xrange(ipnum):
        ip = IP()
        ip.random(24)
        iplist.append(ip)

    for i in xrange(portnum):
        port = Port()
        port.random()
        portlist.append(port)

    for i in xrange(pronum):
        pro = Pro()
        pro.random()
        prolist.append(pro)
    try:
        for i in xrange(ipnum):
            srcip = iplist[random.randint(0, len(iplist)-1)]
            dstip = iplist[random.randint(0, len(iplist)-1)]
            for j in xrange(portnum):
                sp = portlist[random.randint(0, len(portlist) - 1)]
                dp = portlist[random.randint(0, len(portlist) - 1)]
                for k in xrange(pronum):
                    pro = prolist[random.randint(0, len(prolist) -1 )]
                    d = Decision(0)
                    d.random(2)
                    pc.append((srcip, dstip, sp, dp, pro, d))
                    if len(pc) == num:
                        raise Exception
    except Exception:
        pass

    rule_parse(pc, "@0.0.0.0/0\t0.0.0.0/0\t0 : 65535\t0 : 65535\t0x00/0x00", 0)

    return pc


def tcam_entry_raw(pc):
    total = 0
    for r in pc:
        n = 1
        for i in xrange(len(r)-1):
            n *= r[i].r.prefix_entries()
        #if n > 1:
        #    print r, n
        total += n
    return total


def split_to_range_files(pc,fname):

    f = open(fname+"_itl", "w")

    for rule in pc:
        f.write(rule[0].r.__repr__()+"\t"+
                rule[1].r.__repr__()+"\t"+
                rule[2].r.__repr__()+"\t"+
                rule[3].r.__repr__()+"\t"+
                rule[4].r.__repr__()+"\n")

    f.close()



if __name__ == "__main__":
    #pc = load_ruleset(sys.argv[1])
    #print len(pc)
    #print tcam_entry_raw(pc)

    #split_to_range_files(pc, sys.argv[1])
    print Range(1300, 1349).prefix_entries()

    #traces = load_traces("acl1_2_0.5_-0.1_1K_trace")
    #for t in traces:
    #    matched, matchno = match(pc, t)
    #    print matchno
    #r1 = Range(l=1024,h=65535)
    #p = r1.prefix_entries()
    #print p

    #r2 = Range(l=6,h=10)
    #r3 = r1.minus(r2)


    #r3 = r1.insect(r2)
    #print r3









