"""快速验证脚本"""
# Test HashMap
from data_structures.hash_map import HashMap
hm = HashMap()
for i in range(1000):
    hm[f"key_{i}"] = i
assert len(hm) == 1000
assert hm["key_500"] == 500
del hm["key_999"]
assert len(hm) == 999
print("✓ HashMap OK")

# Test Heap
from data_structures.heap import MinHeap
heap = MinHeap(capacity=5)
for i in range(100):
    heap.insert((i * 0.1, f"item_{i}"))
result = heap.to_sorted_list(reverse=True)
assert len(result) == 5
assert result[0][0] == 9.9  # 最大的在最前
print("✓ MinHeap Top-K OK")

# Test SparseMatrix
from data_structures.sparse_matrix import SparseMatrix
sm = SparseMatrix(3, 5)
sm.set(0, 1, 1)
sm.set(0, 3, 1)
sm.set(1, 1, 1)
sm.set(1, 2, 1)
sm.set(2, 3, 1)
sm.set(2, 4, 1)
sm.build()
sim01 = sm.cosine_similarity(0, 1)
sim02 = sm.cosine_similarity(0, 2)
print(f"✓ SparseMatrix OK (sim(0,1)={sim01:.4f}, sim(0,2)={sim02:.4f})")

# Test InvertedIndex
from data_structures.inverted_index import InvertedIndex
idx = InvertedIndex()
idx.add("python", 1)
idx.add("python", 2)
idx.add("java", 2)
idx.add("java", 3)
assert idx.search("python") == {1, 2}
assert idx.search_and(["python", "java"]) == {2}
print("✓ InvertedIndex OK")

# Test Graph
from data_structures.graph import Graph
g = Graph()
g.add_edge("a", "b", 0.9)
g.add_edge("b", "c", 0.8)
g.add_edge("d", "e", 0.7)
comps = g.connected_components()
assert len(comps) == 2
print("✓ Graph OK")

print("\n全部数据结构测试通过！")
