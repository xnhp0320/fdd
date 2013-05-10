#!/usr/bin/python

# A binary trie implementation

class Trie:
    def __init__(self):
        self.trie = [[0,0,0] for i in range(1025)]
        self.r = 0
        self.li = 1
        self.l = [-1]

    def insert(self, prefix, prefixlen, l):
        index = 0

        s = bin(prefix)[2:]
        if len(s) < prefixlen:
            s = '0' * (prefixlen-len(s)) + s

        if len(s) > prefixlen:
            prefix >>= (len(s) - prefixlen)
            s = bin(prefix)[2:]

        if prefixlen == 0:
            self.trie[0][2] = self.li
            self.l.append(l)
            self.li += 1
            #print self.l
            return

        for x in s:
            if x == '1':
                if self.trie[index][1] == 0:
                    self.r += 1
                    self.trie[index][1] = self.r
                    index = self.r
                else:
                    index = self.trie[index][1]
            else:
                if self.trie[index][0] == 0:
                    self.r += 1
                    self.trie[index][0] = self.r
                    index = self.r
                else:
                    index = self.trie[index][0]

        self.trie[index][2] = self.li
        self.l.append(l)
        self.li += 1
        #print prefix, prefixlen
        #print self.l
        #print "done"

    def search(self, prefix, prefixlen):

        index = 0
        s = bin(prefix)[2:]
        if len(s) < prefixlen:
            s = '0' * (prefixlen-len(s)) + s

        if len(s) > prefixlen:
            prefix >>= (len(s) - prefixlen)
            s = bin(prefix)[2:]

        if prefixlen == 0:
            if self.trie[index][2] != 0:
                return self.l[self.trie[index][2]]
            else:
                return None

        for x in s:
            if x == '1':
                index = self.trie[index][1]
            else:
                index = self.trie[index][0]

            if index == 0:
                return None

        return self.l[self.trie[index][2]]

    def check_insert(self, prefix, prefixlen, l):
        if self.search(prefix, prefixlen) == None:
            self.insert(prefix, prefixlen, l)
            return True
        else:
            return False

    def get_leaves(self):
        return self.l[1:]

    def dfs(self, index, prefix, prefixlen, visit):

        if self.trie[index][2] != 0:
            visit(prefix, prefixlen, index)

        if self.trie[index][0] != 0:
            self.dfs(self.trie[index][0], prefix<<1, prefixlen+1, visit)

        if self.trie[index][1] != 0:
            self.dfs(self.trie[index][1], prefix<<1|1, prefixlen+1, visit)



    def get_prefix(self):
        prefix_set = []

        def visit(prefix, prefixlen, index):
            prefix_set.append((prefix, prefixlen))

        self.dfs(0, 0, 0, visit)
        return prefix_set




if __name__ == "__main__":
    t = Trie()
    t.insert(0b111, 3, 1)
    t.insert(0b101, 3, 2)
    t.insert(0b001, 3, 3)
    t.insert(0b001, 2, 4)

    print t.search(0b111, 3)

    print t.get_prefix()
    print t.get_leaves()






















