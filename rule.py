#!/usr/bin/python


import fileinput
import sys
import re
import os
import subprocess
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

def rule_parse(pc, line):
    #print line
    m = re.match(r"@(?P<sip>\d+\.\d+\.\d+\.\d+/\d+)\t"
                    r"(?P<dip>\d+\.\d+\.\d+\.\d+/\d+)\t"
                    r"(?P<sp>\d+\s:\s\d+)\t"
                    r"(?P<dp>\d+\s:\s\d+)\t"
                    r"(?P<p>0[xX][0-9a-fA-F]+/0[xX][0-9a-fA-F]+).*", line)


    if m is None:
        print line

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

    pc.append((sip, dip, sp, dp, p))




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
    for line in fileinput.input(path):
        rule_parse(pc, line)
    return pc




if __name__ == "__main__":
    pc = load_ruleset(sys.argv[1])
    #r1 = Range(l=6,h=11)
    #r2 = Range(l=6,h=10)
    #r3 = r1.minus(r2)


    #r3 = r1.insect(r2)
    #print r3









