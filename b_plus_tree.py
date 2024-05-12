from __future__ import annotations
from typing import Any, Optional

NodeKey = Any
LeafValue = Any

class Node:
    def __init__(self, d, parent, leaf) -> None:
        self.parent: Optional[Node] = parent
        self.keys: list[NodeKey] = []
        self.children: list[Node] = []      # For internal nodes
        self.values: list[LeafValue] = []   # For leaf nodes
        self.leaf: bool = leaf
        self.d: int = d

    def get_value(self, searching_key: NodeKey) -> Optional[LeafValue]:
        assert(self.leaf)
        assert(len(self.keys) == len(self.values))

        for ind, key in enumerate(self.keys):
            if key == searching_key:
                return self.values[ind]
        return None

    def get_child(self, searching_key: NodeKey) -> tuple[Node, int]:
        assert(not self.leaf)

        for ind, key in enumerate(self.keys):
            if searching_key < key:
                return self.children[ind], ind
        return self.children[ind + 1], ind + 1

    def add_value(self, key: NodeKey, value: LeafValue) -> None:
        assert(self.leaf)

        if not self.keys:
            self.keys.append(key)
            self.values.append(value)
            return

        # Insert the key to maintain the sorted order
        for ind in range(0, len(self.keys)):
            if key == self.keys[ind]:
                self.values[ind] = value
                return

            if key < self.keys[ind] and (ind == 0 or self.keys[ind - 1] < key):
                self.keys = self.keys[:ind] + [key] + self.keys[ind:]
                self.values = self.values[:ind] + [value] + self.values[ind:]
                return

        self.keys.append(key)
        self.values.append(value)

    def add_child(self, key: NodeKey, left_child: Node, right_child: Node) -> None:
        if self.leaf:
            raise Exception("Cannot add value to a child node")

        '''
              42
           /      \\
          []  [43 44 45 46]

        becomes
              42    45
           /      \\    \\
          []  [43 44] [45 46]
        '''

        assert (len(self.keys) > 0)

        for ind in range(0, len(self.keys)):
            assert (key != self.keys[ind])

            if key < self.keys[ind]:
                self.keys = self.keys[:ind] + [key] + self.keys[ind:]
                self.children = self.children[:ind] + [left_child, right_child] + self.children[ind + 1:]
                return

        self.keys.append(key)
        self.children = self.children[:-1] + [left_child, right_child]


    def split_leaf(self) -> tuple[NodeKey, Node, Node]:
        assert(self.leaf)
        assert(self.is_full())

        mid = len(self.keys) // 2

        # Split into two leaf nodes
        left = Node(d=self.d, parent=self.parent, leaf=True)
        left.keys = self.keys[:mid]
        left.values = self.values[:mid]

        self.keys = self.keys[mid:]
        self.values = self.values[mid:]

        return self.keys[0], left, self

    def split_internal(self) -> tuple[NodeKey, Node, Node]:
        assert(not self.leaf)
        assert(self.is_full())

        mid = len(self.keys) // 2

        left = Node(d=self.d, parent=self.parent, leaf=False)
        left.keys = self.keys[:mid]
        left.children = self.children[:mid+1]

        for c in left.children:
            c.parent = left

        key = self.keys[mid]

        self.keys = self.keys[mid+1:]
        self.children = self.children[mid+1:]

        return key, left, self

    def is_full(self) -> bool:
        return len(self.keys) == self.d

class BPlusTree:
    def __init__(self, d) -> None:
        self.root: Node = Node(d=d, parent=None, leaf=True)
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
                new_parent = Node(d=self.d, parent=None, leaf=False)
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


    def visualize(self):
        def _stringify(lst: list[Any]) -> list[str]:
            return [str(e) for e in lst]

        def _visualize(curr: Node, level: int):
            print("." * (level * 2), end=" ")
            print("[%s]" % (", ".join(_stringify(curr.keys))), end=(" " if curr.leaf else "\n"))

            if curr.leaf:
                print("-> (%s)" % (", ".join(_stringify(curr.values))))
            else:
                for i, c in enumerate(curr.children):
                    if i < len(curr.keys):
                        print("." * (level * 2 + 1), end=" ")
                        print("If < %s" % curr.keys[i])
                    else:
                        print("." * (level * 2 + 1), end=" ")
                        print("Else" )
                    _visualize(c, level + 1)

        _visualize(self.root, 1)
