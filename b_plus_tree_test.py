from b_plus_tree import BPlusTree
import random


if __name__ == "__main__":
    MAXNUM = 100000
    d = random.randint(3, 10)
    t = BPlusTree(d)

    print("Testing starts: d=%d MAXNUM=%d" % (d, MAXNUM))

    for i in range(0, 4):
        seq = list(range(MAXNUM))
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

        # Remove a random size of nodes
        seq = seq[: random.randint(len(seq) // 2, len(seq))]
        random.shuffle(seq)
        for v in seq:
            t.remove(v)

        print("Test: Remove: OK")

        ind = 0
        for (k, v) in t.leafwalk():
            ind += 1
            assert(k == v)
        assert(ind == MAXNUM - len(seq))

        print("Test: Leafwalk after removals: OK")
