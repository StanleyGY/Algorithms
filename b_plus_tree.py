from __future__ import annotations
from typing import Any, Optional, cast
from bisect import bisect_left, bisect_right

NodeKey = Any
LeafValue = Any

class Node:
    def __init__(self, d, parent, leaf) -> None:
        self.parent: Optional[Node] = parent
        self.keys: list[NodeKey] = []
        self.leaf: bool = leaf
        self.d: int = d

    def get_value(self, searching_key: NodeKey) -> Optional[LeafValue]:
        raise NotImplementedError

    def get_child(self, searching_key: NodeKey) -> tuple[Node, int]:
        raise NotImplementedError

    def add_value(self, key: NodeKey, value: LeafValue) -> None:
        raise NotImplementedError

    def add_child(self, key: NodeKey, left_child: Node, right_child: Node) -> None:
        raise NotImplementedError

    def remove_value(self, key:NodeKey) -> None:
        raise NotImplementedError

    def split_leaf(self) -> tuple[NodeKey, Node, Node]:
        raise NotImplementedError

    def split_internal(self) -> tuple[NodeKey, Node, Node]:
        raise NotImplementedError

    def is_full(self) -> bool:
        return len(self.keys) == self.d

    # def is_underflow(self) -> bool:
    #     return len(self.keys) < self.d // 2


class InternelNode(Node):
    def __init__(self, d, parent) -> None:
        self.children: list[Node] = []
        super(InternelNode, self).__init__(d, parent, False)

    def get_child(self, searching_key: NodeKey) -> tuple[Node, int]:
        ind = bisect_right(self.keys, searching_key)
        return self.children[ind], ind

    def add_child(self, key: NodeKey, left_child: Node, right_child: Node) -> None:
        assert (len(self.keys) > 0)

        ind = bisect_left(self.keys, key)

        assert(ind >= len(self.keys) or self.keys[ind] != key)

        self.keys.insert(ind, key)
        self.children[ind] = left_child
        self.children.insert(ind + 1, right_child)

    def split_internal(self) -> tuple[NodeKey, Node, Node]:
        assert(self.is_full())

        mid = len(self.keys) // 2

        left = InternelNode(d=self.d, parent=self.parent)
        left.keys = self.keys[:mid]
        left.children = self.children[:mid+1]

        for c in left.children:
            c.parent = left

        key = self.keys[mid]
        self.keys = self.keys[mid+1:]
        self.children = self.children[mid+1:]

        return key, left, self


class LeafNode(Node):
    def __init__(self, d, parent) -> None:
        self.prev: Optional[LeafNode] = None
        self.next: Optional[LeafNode] = None
        self.values: list[LeafValue] = []
        super(LeafNode, self).__init__(d, parent, True)

    def get_value(self, searching_key: NodeKey) -> Optional[LeafValue]:
        assert(len(self.keys) == len(self.values))

        for ind, key in enumerate(self.keys):
            if key == searching_key:
                return self.values[ind]
        return None

    def add_value(self, key: NodeKey, value: LeafValue) -> None:
        if not self.keys:
            self.keys.append(key)
            self.values.append(value)
            return

        # Insert the key while keeping the array sorted
        ind = bisect_left(self.keys, key)

        # Check if there's a duplicate
        if ind < len(self.keys) and self.keys[ind] == key:
            return

        self.keys.insert(ind, key)
        self.values.insert(ind, value)

    # def remove_value(self, key:NodeKey) -> None:
    #     ind = bisect_left(self.keys, key)
    #     assert(self.keys[ind] == key)

    #     self.keys.pop(ind)
    #     self.values.pop(ind)

    #     if self.parent:
    #         pass


    def split_leaf(self):
        assert(self.is_full())

        mid = len(self.keys) // 2

        # Split into two leaf nodes
        left = LeafNode(d=self.d, parent=self.parent)
        left.keys = self.keys[:mid]
        left.values = self.values[:mid]

        self.keys = self.keys[mid:]
        self.values = self.values[mid:]

        # Link leaf nodes
        if self.prev:
            self.prev.next = left
        left.prev = self.prev
        left.next = self
        self.prev = left

        return self.keys[0], left, self

class BPlusTree:
    def __init__(self, d) -> None:
        self.root: Node = LeafNode(d=d, parent=None)
        self.d: int = d

    def get(self, key: NodeKey) -> Optional[LeafValue]:
        curr = self.root
        while not curr.leaf:
            curr, _ = curr.get_child(key)

        return curr.get_value(key)

    def insert(self, key: NodeKey, value: LeafValue) -> None:
        """Insert a key-value pair into B+ tree

        Args:
            key (NodeKey): _description_
            value (LeafValue): _description_
        """

        def _push_up(key0: NodeKey, left: Node, right: Node):
            parent = right.parent

            if not parent:
                new_parent = InternelNode(d=self.d, parent=None)
                new_parent.keys.append(key0)
                new_parent.children.extend([left, right])
                left.parent = right.parent = self.root = new_parent
            else:
                parent.add_child(key0, left, right)
                if parent.is_full():
                    key0, left, right = parent.split_internal()
                    _push_up(key0, left, right)

        # Traverse until reaching the leaf node
        curr = self.root
        while not curr.leaf:
            curr, _ = curr.get_child(key)

        curr.add_value(key, value)

        # If the leaf node is full, split the leaf node
        if curr.is_full():
            key0, left, right = curr.split_leaf()
            _push_up(key0, left, right)

    # def remove(self, key: NodeKey):
    #     # Traverse until reaching the leaf node
    #     curr = self.root
    #     while not curr.leaf:
    #         curr, _ = curr.get_child(key)

    #     curr.remove_value(key)

    #     if curr.is_underflow():

    def leafwalk(self):
        curr = self.root

        while not curr.leaf:
            curr = cast(InternelNode, curr)
            curr = curr.children[0]

        while curr:
            curr = cast(LeafNode, curr)
            for ind in range(0, len(curr.keys)):
                yield (curr.keys[ind], curr.values[ind])
            curr = curr.next

    def visualize(self):
        def _stringify(lst: list[Any]) -> list[str]:
            return [str(e) for e in lst]

        def _visualize(curr: Node, level: int):
            print("." * (level * 2), end=" ")
            print("[%s]" % (", ".join(_stringify(curr.keys))), end=(" " if curr.leaf else "\n"))

            if curr.leaf:
                curr = cast(LeafNode, curr)
                print("-> (%s)" % (", ".join(_stringify(curr.values))))
            else:
                curr = cast(InternelNode, curr)
                for i, c in enumerate(curr.children):
                    if i < len(curr.keys):
                        print("." * (level * 2 + 1), end=" ")
                        print("If < %s" % curr.keys[i])
                    else:
                        print("." * (level * 2 + 1), end=" ")
                        print("Else" )
                    _visualize(c, level + 1)

        _visualize(self.root, 1)
