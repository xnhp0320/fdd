#!/usr/bin/python
from guppy import hpy
import gc

"copyrighted by Chad R. Meiners all rights reserved.  Contact: chad.rmeiners@gmail.com "

def Intersection(left, right):
    "returns the intersection of left and right"
    if isinstance(left[0], int) or isinstance(left[0], long):
        low = max(left[0],right[0])
        high = min(left[1],right[1])
        return (low,high)
    else:
        return [ Intersection(left[i],right[i]) for i in xrange(len(left))]

def split(prefix):
    " Returns a pair of prefixes that cover prefix"
    size = (1 + abs(prefix[1] - prefix[0]))/2
    low = (prefix[0], prefix[0]+size-1)
    high = (prefix[0]+size, prefix[1])
    return (low, high)


def Get_Prefixes(Interval, test = (long(0), long((2**32) - 1))):
    " Returns the list of prefix interval inside Interval."
    i = Intersection(Interval,test)

    if (i[1]-i[0]) < 0:
        return []
    elif i == test:
        return [test]
    else:
        size = long(1 + abs(test[1] - test[0]))/2
        low = (test[0], test[0]+size-1)
        high = (test[0]+size, test[1])
        return Get_Prefixes(Interval,low) + Get_Prefixes(Interval,high)

def bin(number,size = 32):
    "return the binary string of a number padded to size"
    l = []
    while number > 0:
        number, rem = divmod(number,2)
        l.append(str(rem))

    t = "".join(l[::-1])

    return "0"* (size-len(t)) + t

def Int2Prefix(interval,size=32):
    "returns the prefix representation of the interval."
    def Prefix(br,bl):
        if len(br) == 0:
            return ''
        else:
            if br[0] == bl[0]:
                return br[0] + Prefix(br[1:],bl[1:])
            else:
                return '*'  + Prefix(br[1:],bl[1:])

    return Prefix(bin(interval[0],size), bin(interval[1],size))

def Color(Universe, At):
    " Returns a color number if contigious.  Otherwise returns False. Returns None is no rules match"
    for rule in Universe:

        i = Intersection(rule[0],At)

        if not (i[1] < i[0]):
            if (i[1] - i[0]) < (At[1] - At[0]):
                return False
            else:
                return rule[1]

    return None

def Weighted_Suris(Universe, Prefix, Color_Weights):
    "Returns a dictionary of all prefixes with all solution weights.   Keys are (prefix,color) = mincost."

    p = Get_Prefixes(Prefix)

    Colors = Color_Weights.keys()

    # Do the right thing with no a prefix
    if len(p) == 0:
        return dict()
    elif len(p) > 1:
        r = []
        for i in [Weighted_Suris(Universe, pi, Color_Weights) for pi in p]:
            r += i.items()
        else:
            return dict(r)

    # Find the color value for Prefix

    c = Color(Universe,Prefix)

    # Let handle the atomic case

    if not (c is False):
        # Atomic case
        answer = dict()
        for color in Colors:
            if color != c:
                answer[(Prefix,color)] = Color_Weights[c] + Color_Weights[color]
            else:
                answer[(Prefix,color)] = Color_Weights[c]
    else:
        # Non-atomic case

        # Get subsolutions
        lowPrefix, highPrefix = split(Prefix)

        answer = dict(Weighted_Suris(Universe,lowPrefix, Color_Weights).items() +
                      Weighted_Suris(Universe,highPrefix, Color_Weights).items())

        # Find solutions at this level
        for color in Colors:
            solutions = [ answer[(lowPrefix,cc)] + answer[(highPrefix,cc)] - Color_Weights[cc] if color == cc
                          else answer[(lowPrefix,cc)] + answer[(highPrefix,cc)] - Color_Weights[cc] + Color_Weights[color]
                          for cc in Colors ]

            mincost = min(solutions)
            for si in xrange(len(solutions)):
                if solutions[si] == mincost:
                    mincolor = Colors[si]
                    break

            answer[(Prefix,color)] = mincost


    return answer

def Merge_Lists(ls1, ls2, prefix, bck_color):
    "Creates a cross product of solutions from a list of comparible sub-solutions."
    r = []
    for i in ls1:
        for j in ls2:
            assert i[-1][1] == j[-1][1]

            if i[-1][1] == bck_color:
                r.append(i[:-1] + j[:-1] + [(prefix, bck_color)])
            else:
                r.append(i[:-1] + j[:-1] + [(prefix,i[-1][1])] + [(prefix, bck_color)])

    else:
        return r

def MergeList(ls1, ls2, prefix, bck_color):
    assert ls1[-1][1] == ls2[-1][1]
    if ls1[-1][1] == bck_color:
        return ls1[:-1] + ls2[:-1] + [(prefix, bck_color)]
    else:
        return ls1[:-1] + ls2[:-1] + [(prefix,ls1[-1][1])] + [(prefix, bck_color)]

def optimal_solutions(Universe, Prefix, Color_Weights, Colors, Answers, OPTColor):

    p = Get_Prefixes(Prefix)

    # Do the right thing with no a prefix
    if len(p) == 0:
        return dict()
    elif len(p) > 1:
        raise Exception

        #r = []
        #for i in [Find_Solutions(Universe, pi, Color_Weights,Answers) for pi in p]:
        #    r += i.items()
        #else:
        #    return dict(r)

    # Find the color value for Prefix

    c = Color(Universe,Prefix)

    # Let handle the atomic case

    if not (c is False):
        # Atomic case
        if OPTColor != c:
            return [ (Prefix,c), (Prefix,OPTColor) ]
        else:
            return [ (Prefix, OPTColor) ]
    else:
        # Non-atomic case

        # Get subsolutions
        lowPrefix, highPrefix = split(Prefix)

        solutions = [ Answers[(lowPrefix,cc)] + Answers[(highPrefix,cc)] - Color_Weights[cc] if OPTColor == cc
                      else Answers[(lowPrefix,cc)] + Answers[(highPrefix,cc)] - Color_Weights[cc] + Color_Weights[OPTColor]
                      for cc in Colors ]
        goal = min(solutions)

        for i in xrange(len(Colors)):
            if solutions[i] == goal:
                ChildColor = Colors[i]
                break
        #ChildColor = Answers[(Prefix, OPTColor)][1]

        return MergeList(optimal_solutions(Universe,lowPrefix, Color_Weights, Colors, Answers, ChildColor),
                      optimal_solutions(Universe,highPrefix, Color_Weights, Colors, Answers, ChildColor), Prefix, OPTColor)



def Find_Solutions(Universe, Prefix, Color_Weights, Answers):
    "Returns a dictionary of all minimal sub-solutions.   Keys are (prefix,color) = list of subsolution(which is a list)."

    p = Get_Prefixes(Prefix)

    Colors = Color_Weights.keys()

    # Do the right thing with no a prefix
    if len(p) == 0:
        return dict()
    elif len(p) > 1:
        r = []
        for i in [Find_Solutions(Universe, pi, Color_Weights,Answers) for pi in p]:
            r += i.items()
        else:
            return dict(r)

    # Find the color value for Prefix

    c = Color(Universe,Prefix)

    # Let handle the atomic case

    if not (c is False):
        # Atomic case
        answer = dict()
        for color in Colors:
            if color != c:
                answer[(Prefix,color)] = [ [ (Prefix,c), (Prefix,color) ] ]
            else:
                answer[(Prefix,color)] = [ [ (Prefix,color) ] ]
    else:
        # Non-atomic case

        # Get subsolutions
        lowPrefix, highPrefix = split(Prefix)

        answer = dict(Find_Solutions(Universe,lowPrefix, Color_Weights, Answers).items() +
                      Find_Solutions(Universe,highPrefix, Color_Weights, Answers).items())

        # Find solutions at this level
        for color in Colors:
            solutions = [ Answers[(lowPrefix,cc)] + Answers[(highPrefix,cc)] - Color_Weights[cc] if color == cc
                          else Answers[(lowPrefix,cc)] + Answers[(highPrefix,cc)] - Color_Weights[cc] + Color_Weights[color]
                          for cc in Colors ]
            goal = min(solutions)

            answer[(Prefix,color)] =  [ f for y in [ Merge_Lists(answer[(lowPrefix,Colors[i])], answer[(highPrefix,Colors[i])], p, color)
                                        for i in range(len(Colors)) if solutions[i] == goal ] for f in y ]


    return answer


dim_bound = [(0,long(2**32-1)),
            (0, long(2**32-1)),
            (0, 2**16-1),
            (0, 2**16-1),
            (0, 2**8-1)]

def compress_incomplete_eset(eset, dim, default_range, default_color):
    range_color = []
    for e in eset:
        for r in e.rangeset:
            range_color.append(((r.l, r.h), e.node.color))
    range_color.append(((default_range.l, default_range.h), default_color))

    #print range_color

    color_weight = {}

    for e in eset:
        color_weight[e.node.color] = 1
    color_weight[default_color] = 65535

    x = Weighted_Suris(range_color, dim_bound[dim], color_weight)
    #gc.collect()
    #y = Find_Solutions(range_color,dim_bound[n.dim],color_weight, x)
    OPTCost = x[(dim_bound[dim],default_color)]
    OPTColor = default_color

    #gc.collect()
    opt_list = optimal_solutions(range_color, dim_bound[dim], color_weight, color_weight.keys(), x, OPTColor)

    #e0 = n.edgeset[0]
    #return y[(dim_bound[n.dim],e0.node.color)][0], x[(dim_bound[n.dim], e0.node.color)]
    return opt_list[:-1], OPTCost

def compress_complete_eset(eset, dim):
    range_color = []
    for e in eset:
        for r in e.rangeset:
            range_color.append(((r.l, r.h), e.node.color))
    #print range_color

    color_weight = {}

    for e in eset:
        color_weight[e.node.color] = 1

    x = Weighted_Suris(range_color, dim_bound[dim], color_weight)
    #gc.collect()
    #y = Find_Solutions(range_color,dim_bound[n.dim],color_weight, x)
    OPTCost = min([ x[(dim_bound[dim],c)] for c in color_weight.keys()] )

    for c in color_weight.keys():
        if x[(dim_bound[dim], c)] == OPTCost:
            OPTColor = c
            break

    #gc.collect()
    opt_list = optimal_solutions(range_color, dim_bound[dim], color_weight, color_weight.keys(), x, OPTColor)

    #e0 = n.edgeset[0]
    #return y[(dim_bound[n.dim],e0.node.color)][0], x[(dim_bound[n.dim], e0.node.color)]
    return opt_list, OPTCost




def compress_node(n):

    range_color = []
    for e in n.edgeset:
        for r in e.rangeset:
            range_color.append(((r.l, r.h), e.node.color))
    #print range_color

    color_weight = {}

    for e in n.edgeset:
        color_weight[e.node.color] = e.node.cost

    x = Weighted_Suris(range_color, dim_bound[n.dim], color_weight)
    #gc.collect()
    #y = Find_Solutions(range_color,dim_bound[n.dim],color_weight, x)
    OPTCost = min([ x[(dim_bound[n.dim],c)] for c in color_weight.keys()] )

    for c in color_weight.keys():
        if x[(dim_bound[n.dim], c)] == OPTCost:
            OPTColor = c
            break

    #gc.collect()
    opt_list = optimal_solutions(range_color, dim_bound[n.dim], color_weight, color_weight.keys(), x, OPTColor)

    #e0 = n.edgeset[0]
    #return y[(dim_bound[n.dim],e0.node.color)][0], x[(dim_bound[n.dim], e0.node.color)]
    return opt_list, OPTCost



if __name__ == "__main__":
    #test = [ ((0,2422223607),68), ((2422223608,2422223608), 3),
    #        ((2422223609 , 2422223613), 68), #((2422223614 , 2422223614), 69),
    #        ((2422223615 , 2423496703), 68), ((2423496704 , 2423497727), 28),
    #        ((2423497728 , 2587110727), 68), #((2587110728 , 2587110728), 69),
    #        ((2587110729 , 4294967295), 68), ((0, 4294967295), 69)]
    #testWeights = {68 : 1, 28:1, 3:1, 69:4294967295}
    #test = [ ((0,0),1), ((2,2),1), ((0,3),0) ]
    #testWeights = {1 : 1, 0: 1}
    test = [ ((0x61,0x6f),1), ((0,0xff),0) ]
    testWeights = {1:1,0:1}

#Usage:
    x = Weighted_Suris(test,(0,255),testWeights)
    #for keys in x.keys():
    #    print "keys", keys
    #    print x[keys]
    OPTCost = min([ x[((0, 255), c)] for c in testWeights.keys()] )

    for c in testWeights.keys():
        if x[((0, 255), c)] == OPTCost:
            OPTColor = c
            break

    print "optcolor", OPTColor

    y = Find_Solutions(test,(0,255),testWeights,x)
    opt_list = optimal_solutions(test,(0,255), testWeights, testWeights.keys(), x, OPTColor)
    #for keys in y.keys():
    #print "keys", keys

    print opt_list
    print y[((0,255),0)]
    print x[((0,255),0)]
    print OPTCost


    #print y[((0x00, 3), 0)]
    #print len(y[((0x00, 3), 0)])
    #for z in y[((0x00, 3), 0)]:
    #    print z

    #print x[((0x00, 3), 0)]
    #print x[((0x00, 3), 1)]
    print [ f for y in [[1,2], [2,4],[3]] for f in y]
    h = hpy()
    print h.heap().byrcs
