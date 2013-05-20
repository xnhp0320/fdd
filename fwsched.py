#!/usr/bin/python


from rule import Range

class PrepSchedData:
    def __init__(self, r, color, cost):
        self.r = r
        self.color = color
        self.cost = cost

    def __cmp__(self, other):
        return self.r.__cmp__(other.r)
    def __repr__(self):
        return "R: "+ str(self.r) +" " + "C: " +  str(self.color) +" "+ "Cost: " + str(self.cost)

class Scheduler:

    def __init__(self, color, cost, group):
        self.color = color
        self.cost = cost
        self.group = group

        self.M = [[0 for x in xrange(len(self.color))] for x in xrange(len(self.color))]
        self.C = [[0 for x in xrange(len(self.color))] for x in xrange(len(self.color))]
        self.R = []
        self.RC = []

        for c in xrange(len(self.color)):
            #print c
            #print self.C[c][c]
            self.C[c][c] = self.cost[self.color[c]]
            #print self.C

        #print self.C



    def FSA_cost(self, i, j):
        #print i,j
        if self.C[i][j] == 0:
            mincost = self.cost[self.color[i]] + self.FSA_cost(i+1, j)
            self.M[i][j] = i
            for x in self.group[self.color[i]] :
                if x >= i+2 and x <=j:
                    xmincost = self.FSA_cost(i+1, x-1) + self.FSA_cost(x,j)
                    if xmincost < mincost:
                        mincost = xmincost
                        self.M[i][j] = x
            self.C[i][j] = mincost

        return self.C[i][j]

    def FSA_result(self, t, i, j):
        if i == j:
            #print t,i
            self.R.append(Range(t,i))
            self.RC.append(self.color[t])
        else:
            if self.M[i][j] == i:
                self.FSA_result(i+1, i+1, j)
                #print t,i
                self.R.append(Range(t,i))
                self.RC.append(self.color[t])
            else:
                self.FSA_result(i+1, i + 1, self.M[i][j] - 1)
                self.FSA_result(t, self.M[i][j], j)



if __name__ == "__main__":
#cost is per color
    cost = {}
    cost[0] = 1
    cost[1] = 1
    cost[2] = 1
#color is per task(range)
    color = [0,1,2,1,0]
#group is a dict for color
    group ={0:[0,4], 1:[1,3],2:[3]}

    sched = Scheduler(color, cost, group)
    sched.FSA_cost(0,4)
    #print sched.C, sched.M
    sched.FSA_result(0,0,4)
    #print sched.C[0][2]
    print sched.R
    print sched.RC






