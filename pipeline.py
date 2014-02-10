#!/usr/bin/python


import fdd
import rule
import sys
import gc
import fc
import math
import time


def level_stats(levelnodes):
    ls = [ [] for x in xrange(fdd.MAXDIM)]
    i = 0
    for level in levelnodes:
        dim = {}
        for n in level:
            if n.dim in dim:
                dim[n.dim] += 1
            else:
                dim[n.dim] = 1

        def show_infos(d):
            if d in dim:
                ls[i].append(dim[d])
            else:
                ls[i].append(0)

        show_infos(0)
        show_infos(1)
        show_infos(2)
        show_infos(3)
        show_infos(4)
        i+= 1

    print ls
    return ls

def hash_offload(tcam):
    for d in xrange(len(tcam)):
        prelen_dict = {}
        for entry in tcam[d]:
            plist = entry[2].get_prefix_entries()
            for p in plist:
                l = p.h - p.l +1
                plen = int(math.log(l, 2))
                #print plen

                if plen in prelen_dict:
                    prelen_dict[plen] +=1
                else:
                    prelen_dict[plen] = 1

        print prelen_dict
        print sum(prelen_dict.values())

def deduce_order(ls):
    avail_dim_set = [0,1,2,3,4]
    order = []
    for l in ls[::-1]:
        index = 0
        maxv = 0
        for v in xrange(len(avail_dim_set)):
            if maxv < l[avail_dim_set[v]]:
                maxv = l[avail_dim_set[v]]
                index = avail_dim_set[v]

        avail_dim_set.remove(index)
        order.append(index)
    print order[::-1]





if __name__ == "__main__":

    sys.setrecursionlimit(10000)

    pc = rule.load_ruleset(sys.argv[1])
    print "original set length:", len(pc)
    tcam_raw = rule.tcam_entry_raw(pc)
    ##print "prefix entries:", tcam_raw
    ##ur = len(list(set([r[0].r for r in pc])))
    ##print "uniq ranges",ur
    ##iv = fdd.FDD.build_interval_fast([r[0].r for r in pc])
    ##print "fragment ranges", len(iv)
    ###print "fraglist", iv
    ##c = reduce(lambda x,y: x+y, [x.prefix_entries() for x in iv])
    ##print "prefix fragment ranges", c
    ##print "required", c * 32/(1024.), "Kbits"

    ##print "required", tcam_raw * 144/(1024.), "Kbits"
    #start = time.time()
    #f = fdd.FDD([0,1,2,3,4])
    #gc.disable()
    #try:
    #    levelnodes,leafnodes = f.build_pdd(pc)
    #except KeyboardInterrupt:
    #    print 'rangecnt',f.rangecnt, 'edgecnt', f.edgecnt, 'nodecnt',f.nodecnt
    #gc.enable()
    #mem = f.fdd_mem(f.root)
    #print "FDD(mem):", mem, "bytes", mem/1024., "KB", mem/(1024.*1024), "MB"
    #stop = time.time()- start
    #print "stop", stop


    ###ls = level_stats(levelnodes)
    ###deduce_order(ls)
    #reducednodes = f.fdd_reduce(pc, levelnodes, leafnodes)
    #f.compress(reducednodes)
    ##tcam = f.output_pdd_list(pc, reducednodes)
    ##fc.pdd_entries(pc, tcam, tcam_raw)
    ##fc.compress_pdd_edges(tcam)


    #traces = rule.load_traces(sys.argv[2])
    #for ti in range(len(traces)):
    #    d1 = f.fdd_compressed_match(pc, traces[ti])
    #    d2 = rule.match(pc, traces[ti])

    #    #if d1 == d2[1]:
    #    #    pass
    #    #else:
    #    #    print t, d1, d2
    #    #if ti == 779:
    #    #    v = True
    #    #    f.fdd_match(traces[ti],v)

    #    if d1[0] == d2[0] and pc[d1[1]][fdd.MAXDIM].d == pc[d2[1]][fdd.MAXDIM].d:
    #    #if d1[0] == d2[0] and d1[1] == pc[d2[1]][len(f.order)].d:
    #        #print "pass", ti
    #        pass
    #    else:
    #        print traces[ti], ti, d2[1], pc[d1[1]][len(f.order)].d, pc[d2[1]][len(f.order)].d
    #        #print traces[ti], ti, d2[1], d1[1], pc[d2[1]][len(f.order)].d
    #        #d1 = f.fdd_match(traces[ti], v)


    #f1 = fdd.FDD([4,1,2,3,0])
    #gc.disable()
    #try:
    #    levelnodes,leafnodes = f1.build_fdd(pc)
    #except KeyboardInterrupt:
    #    print 'rangecnt',f.rangecnt, 'edgecnt', f.edgecnt, 'nodecnt',f.nodecnt
    #gc.enable()
    #mem = f1.fdd_mem(f1.root)
    #print "FDD(mem):", mem, "bytes", mem/1024., "KB", mem/(1024.*1024), "MB"
    #tcam = fc.pdd_split(pc)
    #hash_offload(tcam)
    #fc.pdd_entries(pc, tcam, tcam_raw)
    fc.multi_pdd_split(pc, 0, tcam_raw, 3)







