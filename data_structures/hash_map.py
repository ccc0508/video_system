"""
自实现哈希表 (HashMap)

采用链地址法处理冲突，支持自动扩容。
用于: 视频主索引、用户主索引、候选视频得分表等。
"""


class HashNode:
    """哈希表节点（链表节点）"""
    __slots__ = ('key', 'value', 'next')

    def __init__(self, key, value, next_node=None):
        self.key = key
        self.value = value
        self.next = next_node


class HashMap:
    """
    自实现哈希表

    特性:
    - 链地址法处理冲突
    - 负载因子 > 0.75 时自动扩容（容量翻倍）
    - 支持迭代遍历
    """
    DEFAULT_CAPACITY = 16
    LOAD_FACTOR = 0.75

    def __init__(self, capacity=None):
        self._capacity = capacity or self.DEFAULT_CAPACITY
        self._size = 0
        self._buckets = [None] * self._capacity

    def _hash(self, key):
        """计算哈希值"""
        return hash(key) % self._capacity

    def put(self, key, value):
        """插入或更新键值对"""
        idx = self._hash(key)
        node = self._buckets[idx]

        # 查找是否已存在
        while node:
            if node.key == key:
                node.value = value
                return
            node = node.next

        # 头插法
        new_node = HashNode(key, value, self._buckets[idx])
        self._buckets[idx] = new_node
        self._size += 1

        # 检查是否需要扩容
        if self._size > self._capacity * self.LOAD_FACTOR:
            self._resize()

    def get(self, key, default=None):
        """获取值"""
        idx = self._hash(key)
        node = self._buckets[idx]
        while node:
            if node.key == key:
                return node.value
            node = node.next
        return default

    def remove(self, key):
        """删除键值对，返回被删除的值"""
        idx = self._hash(key)
        node = self._buckets[idx]
        prev = None

        while node:
            if node.key == key:
                if prev:
                    prev.next = node.next
                else:
                    self._buckets[idx] = node.next
                self._size -= 1
                return node.value
            prev = node
            node = node.next
        return None

    def contains(self, key):
        """判断是否包含键"""
        return self.get(key, _SENTINEL) is not _SENTINEL

    def _resize(self):
        """扩容: 容量翻倍，重新哈希所有元素"""
        old_buckets = self._buckets
        self._capacity *= 2
        self._buckets = [None] * self._capacity
        self._size = 0

        for node in old_buckets:
            while node:
                self.put(node.key, node.value)
                node = node.next

    @property
    def size(self):
        return self._size

    def keys(self):
        """返回所有键的列表"""
        result = []
        for node in self._buckets:
            while node:
                result.append(node.key)
                node = node.next
        return result

    def values(self):
        """返回所有值的列表"""
        result = []
        for node in self._buckets:
            while node:
                result.append(node.value)
                node = node.next
        return result

    def items(self):
        """返回所有键值对"""
        result = []
        for node in self._buckets:
            while node:
                result.append((node.key, node.value))
                node = node.next
        return result

    def __len__(self):
        return self._size

    def __contains__(self, key):
        return self.contains(key)

    def __getitem__(self, key):
        val = self.get(key, _SENTINEL)
        if val is _SENTINEL:
            raise KeyError(key)
        return val

    def __setitem__(self, key, value):
        self.put(key, value)

    def __delitem__(self, key):
        if self.remove(key) is None:
            raise KeyError(key)

    def __iter__(self):
        for node in self._buckets:
            while node:
                yield node.key
                node = node.next

    def __repr__(self):
        pairs = [f"{k!r}: {v!r}" for k, v in self.items()]
        return "HashMap({" + ", ".join(pairs) + "})"


# 哨兵对象，用于区分 None 值和键不存在
_SENTINEL = object()
