from b_plus_tree import BPlusTree
import random

if __name__ == "__main__":

    print("==== Test: Insert and Get ====")

    MAXNUM = 100000
    d = random.randint(3, 10)
    print("d: %d" % (d))

    t = BPlusTree(d)
    seq = list(range(0, MAXNUM))
    random.shuffle(seq)

    for v in seq:
        t.insert(v, v)

    random.shuffle(seq)
    for v in seq:
        assert(t.get(v) == v)

    print("==== Test: Insert and Get: OK ====")

