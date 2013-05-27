#!/usr/bin/python
from fc import *


if __name__ == "__main__":
    #pc = []
    #pr1 = PackRange(rule.Range(20,40))
    #pr2 = PackRange(rule.Range(30,50))
    #d = rule.Decision(0)
    #pc.append([pr1,pr2,d])

    #pr1 = PackRange(rule.Range(30,60))
    #pr2 = PackRange(rule.Range(40,80))
    #d = rule.Decision(1)
    #pc.append([pr1,pr2,d])

    #pr1 = PackRange(rule.Range(1,100))
    #pr2 = PackRange(rule.Range(1,100))
    #d = rule.Decision(0)
    #pc.append([pr1,pr2,d])

    #print pc

    pc = []
    pr1 = PackRange(rule.Range(0,1))
    pr2 = PackRange(rule.Range(12,13))
    d = rule.Decision(1)
    pc.append([pr1,pr2,d])

    pr1 = PackRange(rule.Range(2,3))
    pr2 = PackRange(rule.Range(2,3))
    d = rule.Decision(1)
    pc.append([pr1,pr2,d])

    pr1 = PackRange(rule.Range(12,13))
    pr2 = PackRange(rule.Range(12,13))
    d = rule.Decision(1)
    pc.append([pr1,pr2,d])

    pr1 = PackRange(rule.Range(12,13))
    pr2 = PackRange(rule.Range(2,3))
    d = rule.Decision(1)
    pc.append([pr1,pr2,d])

    pr1 = PackRange(rule.Range(0,15))
    pr2 = PackRange(rule.Range(0,15))
    d = rule.Decision(0)
    pc.append([pr1,pr2,d])
    #print pc


    order = [1,0]
    final_list = firewall_compressor_algo(pc, order)
    print final_list

    #f = FDD(order)
    #levelnodes, leafnodes = f.build_fdd(pc)
    #cpc = f.firewall_compressor(pc, levelnodes, leafnodes)

    #print cpc

    #f3 = FDD(order)
    #levelnodes, leafnodes = f3.build_fdd(cpc)
    #rr_out = []
    #removed_list = []
    #f3.redund_remove_semantic(leafnodes, rr_out, removed_list, cpc)

    #print sorted(rr_out)






