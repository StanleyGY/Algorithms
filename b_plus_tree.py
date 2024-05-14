from __future__ import annotations
from typing import Any, Optional, cast
from bisect import bisect_left, bisect_right

NodeKey = Any
LeafValue = Any

class Node:
    def __init__(self, d, parent, leaf) -> None:
        self.parent: Optional[InternelNode] = parent
        self.keys: list[NodeKey] = []
        self.leaf: bool = leaf
        self.d: int = d

    def is_full(self) -> bool:
        return len(self.keys) == self.d

    def is_underflow(self) -> bool:
        return len(self.keys) < self.d // 2

    def can_borrow(self) -> bool:
        return len(self.keys) - 1 >= self.d // 2

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

    def update_key_after_removal(self, key: NodeKey) -> None:
        """Update keys of the internel node when a leaf node is removed
        This ensures that all keys in an internal node can be found in leaf nodes.

             A3   <-
          /     \
        A1,A2   [A3] A4

        Upon removing A3, ensure that the internal node A3's key is updated to
        leftmost child of A4

        Args:
            key (NodeKey):
        """
        ind = bisect_left(self.keys, key)

        if ind < len(self.keys):
            curr = self.children[ind + 1]
            while not curr.leaf:
                curr = cast(InternelNode, curr)
                curr = curr.children[0]

            curr = cast(LeafNode, curr)
            self.keys[ind] = curr.keys[0]

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

    def borrow_from_right_sibling(self, parent_ind: int, right: InternelNode):
        """Borrow a key from right sibling

               2
             /   \
         [ ]     4, 5
          |     /  |  \
          1   2   4   5

        becomes
              4
            /    \
           2      5
          / \    / \
          1  2  4  5

        Args:
            parent_ind (int): index of `self` in parent node's children
            right (Node): right sibling node
        """
        assert(self.parent)
        assert(self.is_underflow())

        # Borrow the leftmost key from right sibling
        self.keys.append(self.parent.keys[parent_ind])
        self.children.append(right.children[0])
        right.children[0].parent = self

        self.parent.keys[parent_ind] = right.keys[0]
        right.keys.pop(0)
        right.children.pop(0)

    def borrow_from_left_sibling(self, parent_ind: int, left: InternelNode):
        assert(self.parent)
        assert(self.is_underflow())

        self.keys.insert(0, self.parent.keys[parent_ind - 1])
        self.children.insert(0, left.children[-1])
        left.children[-1].parent = self

        self.parent.keys[parent_ind - 1] = left.keys[-1]
        left.keys.pop()
        left.children.pop()

    def merge_with_right_sibling(self, parent_ind: int, right: InternelNode):
        """
               3
             /   \
           []    4
           |    /  \
           A    B  C
        becomes
                []
                /
              3, 4
             /  |  \
            A   B  C
        Args:
            parent_ind (int): index of `self` in parent node's children
            right (InternelNode):
        """
        assert(self.parent)

        self.keys.append(self.parent.keys[parent_ind])

        # Merge with right sibling
        self.keys.extend(right.keys)
        self.children.extend(right.children)
        for c in right.children:
            c.parent = self

        # Merge of two children causes a parent's key to be deleted
        self.parent.keys.pop(parent_ind)
        self.parent.children.pop(parent_ind + 1)

    def merge_with_left_sibling(self, parent_ind: int, left: InternelNode):
        """
              3
            /   \
           2     []
          / \     |
         A    B   C

        becomes
            []
            /
           2,3
          / | \
         A  B  C

        Args:
            parent_ind (int): index of `self` in parent node's children
            left (InternelNode):
        """
        assert(self.parent)

        self.keys.insert(0, self.parent.keys[parent_ind - 1])
        self.keys = left.keys + self.keys
        self.children = left.children + self.children
        for c in left.children:
            c.parent = self

        # Merge of two children causes a parent's key to be deleted
        self.parent.keys.pop(parent_ind - 1)
        self.parent.children.pop(parent_ind - 1)


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

    def remove_value(self, key: NodeKey) -> None:
        ind = bisect_left(self.keys, key)
        assert(self.keys[ind] == key)

        # Remove the key/value from leaf node
        self.keys.pop(ind)
        self.values.pop(ind)

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

    def borrow_from_right_sibling(self, right: LeafNode):
        """
              B
             / \
          []    B,C
          self  right

        becomes
            C
           / \
          B   C

        Args:
            right (LeafNode):
        """
        assert(self.next == right)
        assert(right.parent)

        self.keys.append(right.keys[0])
        self.values.append(right.values[0])
        right.keys.pop(0)
        right.values.pop(0)

        # Need to update the key in parent node
        # as a larger node was moved over from right leaf to left leaf
        p = right.parent
        for i in range(0, len(p.children)):
            if p.children[i] == right:
                p.keys[i - 1] = right.keys[0]
                break

    def borrow_from_left_sibling(self, left: LeafNode):
        assert(self.prev == left)
        assert(self.parent)

        self.keys.insert(0, left.keys[-1])
        self.values.insert(0, left.values[-1])
        left.keys.pop()
        left.values.pop()

        # Need to update the key in parent node
        # as a smaller node was moved over from left leaf to right leaf
        p = self.parent
        for i in range(0, len(p.children)):
            if p.children[i] == self:
                p.keys[i - 1] = self.keys[0]
                break

    def merge_with_right_sibling(self, right: LeafNode):
        assert(self.next == right)
        assert(self.parent)

        self.keys.extend(right.keys)
        self.values.extend(right.values)

        self.next = right.next
        if right.next:
            right.next.prev = self

        # Merge of two children causes a parent's key to be deleted
        p = self.parent
        for i in range(0, len(p.children)):
            if p.children[i] == right:
                p.keys.pop(i - 1)
                p.children.pop(i)
                break

    def merge_with_left_sibling(self, left: LeafNode):
        assert(self.prev == left)
        assert(self.parent)

        left.keys.extend(self.keys)
        left.values.extend(self.values)

        left.next = self.next
        if self.next:
            self.next.prev = left

        # Merge of two children causes a parent's key to be deleted
        p = self.parent
        for i in range(0, len(p.children)):
            if p.children[i] == self:
                p.keys.pop(i - 1)
                p.children.pop(i)
                break

class BPlusTree:
    def __init__(self, d) -> None:
        self.root: Node = LeafNode(d=d, parent=None)
        self.d: int = d

    def get(self, key: NodeKey) -> Optional[LeafValue]:
        curr = self.root
        while not curr.leaf:
            curr = cast(InternelNode, curr)
            curr, _ = curr.get_child(key)

        curr = cast(LeafNode, curr)
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
            curr = cast(InternelNode, curr)
            curr, _ = curr.get_child(key)

        curr = cast(LeafNode, curr)
        curr.add_value(key, value)

        # If the leaf node is full, split the leaf node
        if curr.is_full():
            key0, left, right = curr.split_leaf()
            _push_up(key0, left, right)

    def remove(self, key: NodeKey):
        # Traverse until reaching the leaf node
        curr = self.root
        while not curr.leaf:
            curr = cast(InternelNode, curr)
            curr, _ = curr.get_child(key)

        curr = cast(LeafNode, curr)
        curr.remove_value(key)

        def _push_up(curr: InternelNode):
            curr.update_key_after_removal(key)

            if not curr.is_underflow():
                return

            if curr == self.root:
                # Reached the top of tree, so we should stop propagating
                # If only one node is left
                if len(curr.keys) == 0 and len(curr.children) == 1:
                    self.root = curr.children[0]
                    self.root.parent = None
                return

            assert(curr.parent)

            # Get position of `curr` in parent node
            for ind, c in enumerate(curr.parent.children):
                if c == curr:
                    break

            # Get the sibling of internal node
            prev = None
            next = None
            if ind + 1 < len(curr.parent.children):
                next = curr.parent.children[ind + 1]
            if ind > 0:
                prev = curr.parent.children[ind - 1]

            # Try balance the tree
            if next and next.parent == curr.parent:
                next = cast(InternelNode, next)

                if next.can_borrow():
                    curr.borrow_from_right_sibling(ind, next)
                else:
                    curr.merge_with_right_sibling(ind, next)

            elif prev and prev.parent == curr.parent:
                prev = cast(InternelNode, prev)

                if prev.can_borrow():
                    curr.borrow_from_left_sibling(ind, prev)
                else:
                    curr.merge_with_left_sibling(ind, prev)

            else:
                assert(False)

            if curr.parent:
                _push_up(curr.parent)

        if curr != self.root and curr.is_underflow():
            next = curr.next
            prev = curr.prev

            if next and next.parent == curr.parent:

                if next.can_borrow():
                    curr.borrow_from_right_sibling(next)
                else:
                    curr.merge_with_right_sibling(next)

            elif prev and prev.parent == curr.parent:

                if prev.can_borrow():
                    curr.borrow_from_left_sibling(prev)
                else:
                    curr.merge_with_left_sibling(prev)

            else:
                assert(False)

        if curr.parent:
            _push_up(curr.parent)

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
