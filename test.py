#!/usr/bin/python
from fdd import *


if __name__ == "__main__":
    pc = []
    pr1 = PackRange(rule.Range(20,40))
    pr2 = PackRange(rule.Range(30,50))
    d = rule.Decision(0)
    pc.append([pr1,pr2,d])

    pr1 = PackRange(rule.Range(30,60))
    pr2 = PackRange(rule.Range(40,80))
    d = rule.Decision(1)
    pc.append([pr1,pr2,d])

    pr1 = PackRange(rule.Range(1,100))
    pr2 = PackRange(rule.Range(1,100))
    d = rule.Decision(0)
    pc.append([pr1,pr2,d])

    print pc

    order = [0,1]
    f = FDD(order)
    levelnodes, leafnodes = f.build_fdd(pc)
    cpc = f.firewall_compressor(pc, levelnodes, leafnodes)

    print cpc

    f3 = FDD(order)
    levelnodes, leafnodes = f3.build_fdd(cpc)
    rr_out = []
    removed_list = []
    f3.redund_remove_semantic(leafnodes, rr_out, removed_list, cpc)

    print sorted(rr_out)






