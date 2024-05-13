from b_plus_tree import BPlusTree
import random

if __name__ == "__main__":

    MAXNUM = 100000
    d = random.randint(3, 10)

    print("Testing starts: d=%d MAXNUM=%d" % (d, MAXNUM))

    t = BPlusTree(d)
    seq = list(range(0, MAXNUM))
    random.shuffle(seq)

    for v in seq:
        t.insert(v, v)

    random.shuffle(seq)
    for v in seq:
        assert(t.get(v) == v)

    print("Test: Insert and Get: OK")

    ind = 0
    for (k, v) in t.leafwalk():
        assert(k == v)
        ind += 1
    assert(ind == MAXNUM)

    print("Test: Leafwalk: OK")


