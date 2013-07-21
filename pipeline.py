#!/usr/bin/python


import fdd
import rule
import sys
import gc



if __name__ == "__main__":
    pc = rule.load_ruleset(sys.argv[1])
    print "original set length:", len(pc)
    #tcam_raw = rule.tcam_entry_raw(pc)
    #print "prefix entries:", tcam_raw
    #ur = len(list(set([r[0].r for r in pc])))
    #print "uniq ranges",ur
    #iv = fdd.FDD.build_interval_fast([r[0].r for r in pc])
    #print "fragment ranges", len(iv)
    ##print "fraglist", iv
    #c = reduce(lambda x,y: x+y, [x.prefix_entries() for x in iv])
    #print "prefix fragment ranges", c
    #print "required", c * 32/(1024.), "Kbits"

    #print "required", tcam_raw * 144/(1024.), "Kbits"
    f = fdd.FDD(None)
    gc.disable()
    try:
        levelnodes,leafnodes = f.build_pdd(pc)
    except KeyboardInterrupt:
        print 'rangecnt',f.rangecnt, 'edgecnt', f.edgecnt, 'nodecnt',f.nodecnt
    gc.enable()
    mem = f.fdd_mem(f.root)
    print "FDD(mem):", mem, "bytes", mem/1024., "KB", mem/(1024.*1024), "MB"



    f1 = fdd.FDD([0,1,2,3,4])
    gc.disable()
    try:
        levelnodes,leafnodes = f1.build_fdd(pc)
    except KeyboardInterrupt:
        print 'rangecnt',f.rangecnt, 'edgecnt', f.edgecnt, 'nodecnt',f.nodecnt
    gc.enable()
    mem = f1.fdd_mem(f1.root)
    print "FDD(mem):", mem, "bytes", mem/1024., "KB", mem/(1024.*1024), "MB"







