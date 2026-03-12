"""
自实现堆 (Heap)

支持最小堆和最大堆，用于 Top-K/Top-N 选择。
用于: F3 相似用户 Top-K, F4 推荐视频 Top-N。
"""


class MinHeap:
    """
    最小堆

    堆顶为最小元素。用于维护 Top-K 最大值:
    维护大小为 K 的最小堆，堆顶是第 K 大的元素。
    新元素如果比堆顶大就替换堆顶。
    """

    def __init__(self, capacity=None):
        self._data = []
        self._capacity = capacity  # None 表示无限制

    def insert(self, item):
        """
        插入元素。item 应为可比较的元组，如 (score, id)。
        如果设置了容量限制且已满，当新元素大于堆顶时替换堆顶。
        """
        if self._capacity and len(self._data) >= self._capacity:
            if item > self._data[0]:
                self._data[0] = item
                self._sift_down(0)
            return
        self._data.append(item)
        self._sift_up(len(self._data) - 1)

    def extract(self):
        """弹出并返回堆顶（最小）元素"""
        if not self._data:
            raise IndexError("堆为空")
        if len(self._data) == 1:
            return self._data.pop()
        top = self._data[0]
        self._data[0] = self._data.pop()
        self._sift_down(0)
        return top

    def peek(self):
        """查看堆顶元素"""
        if not self._data:
            raise IndexError("堆为空")
        return self._data[0]

    def _sift_up(self, idx):
        """上浮调整"""
        while idx > 0:
            parent = (idx - 1) // 2
            if self._data[idx] < self._data[parent]:
                self._data[idx], self._data[parent] = self._data[parent], self._data[idx]
                idx = parent
            else:
                break

    def _sift_down(self, idx):
        """下沉调整"""
        n = len(self._data)
        while True:
            smallest = idx
            left = 2 * idx + 1
            right = 2 * idx + 2

            if left < n and self._data[left] < self._data[smallest]:
                smallest = left
            if right < n and self._data[right] < self._data[smallest]:
                smallest = right

            if smallest != idx:
                self._data[idx], self._data[smallest] = self._data[smallest], self._data[idx]
                idx = smallest
            else:
                break

    def to_sorted_list(self, reverse=True):
        """返回排序后的列表（默认降序，即最大的在前）"""
        result = []
        heap_copy = MinHeap()
        heap_copy._data = self._data[:]
        while heap_copy._data:
            result.append(heap_copy.extract())
        if reverse:
            result.reverse()
        return result

    @property
    def size(self):
        return len(self._data)

    def __len__(self):
        return len(self._data)

    def __bool__(self):
        return bool(self._data)


class MaxHeap:
    """
    最大堆

    堆顶为最大元素。通过对元素取反复用 MinHeap 逻辑。
    """

    def __init__(self, capacity=None):
        self._heap = MinHeap(capacity)

    def insert(self, item):
        """插入元素。item 为 (score, id) 元组。"""
        neg_item = (-item[0], item[1]) if isinstance(item, tuple) else -item
        self._heap.insert(neg_item)

    def extract(self):
        """弹出并返回堆顶（最大）元素"""
        item = self._heap.extract()
        return (-item[0], item[1]) if isinstance(item, tuple) else -item

    def peek(self):
        """查看堆顶元素"""
        item = self._heap.peek()
        return (-item[0], item[1]) if isinstance(item, tuple) else -item

    def to_sorted_list(self, reverse=False):
        """返回排序后的列表（默认降序）"""
        result = []
        heap_copy = MaxHeap()
        heap_copy._heap._data = self._heap._data[:]
        while heap_copy._heap._data:
            result.append(heap_copy.extract())
        if reverse:
            result.reverse()
        return result

    @property
    def size(self):
        return self._heap.size

    def __len__(self):
        return self._heap.size

    def __bool__(self):
        return bool(self._heap)
