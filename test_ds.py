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
sm.set(0, 1, 1)
sm.set(0, 3, 1)
sm.set(1, 1, 1)
sm.set(1, 2, 1)
sm.set(2, 3, 1)
sm.set(2, 4, 1)
sm.build()
assert sm.row_nnz(0) == 2
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
assert idx.term_count("java") == 2
print("✓ InvertedIndex OK")

# Test Graph
from data_structures.graph import Graph
g = Graph()
g.add_edge("a", "b", 0.9)
g.add_edge("a", "b", 0.95)
g.add_edge("b", "c", 0.8)
g.add_edge("d", "e", 0.7)
comps = g.connected_components()
assert len(comps) == 2
assert g.num_edges == 3
print("✓ Graph OK")

# Test Similarity + Recommender integration
from core.similarity import SimilarityEngine
from core.recommender import Recommender

users = [{"user_id": i, "name": f"u{i}"} for i in range(3)]
behaviors = [
    [0, 0, "view", 0, 10],
    [0, 1, "view", 0, 10],
    [0, 1, "like", 0, 10],  # duplicate user-video pair should not duplicate matrix columns
    [1, 0, "view", 0, 10],
    [1, 1, "view", 0, 10],
    [1, 2, "view", 0, 10],
    [2, 3, "view", 0, 10],
]
engine = SimilarityEngine()
engine.build_matrix(users, behaviors)
assert engine.matrix.row_nnz(0) == 2
similar = engine.find_similar_users(0, top_k=2)
assert similar and similar[0][0] == 1
assert engine.similarity_graph.num_edges == 1
recs = Recommender(engine).recommend(0, similar, top_n=2, videos=[{} for _ in range(4)])
assert recs and recs[0]["video_id"] == 2
print("✓ Similarity/Recommender integration OK")

# Test video clustering feature semantics
from core.clustering import ClusteringEngine

videos = [
    {"video_id": 0, "category": "游戏", "tags": ["a"]},
    {"video_id": 1, "category": "音乐", "tags": ["b"]},
    {"video_id": 2, "category": "游戏", "tags": ["a"]},
]
cluster_behaviors = [
    [0, 0, "watch", 0, 10],
    [1, 0, "watch", 0, 10],
    [0, 1, "watch", 0, 10],
    [1, 1, "watch", 0, 10],
    [4, 2, "watch", 0, 10],
    [5, 2, "watch", 0, 10],
]
cluster_engine = ClusteringEngine()
features = cluster_engine.build_video_features(videos, cluster_behaviors, num_users=6)
dist_same_audience = cluster_engine._euclidean_dist(features[0], features[1])
dist_same_content = cluster_engine._euclidean_dist(features[0], features[2])
assert dist_same_audience < dist_same_content
labels, centers = cluster_engine.kmeans(features, k=2, max_iter=5)
assert len(labels) == len(videos)
assert len(centers) == 2
video_labels, video_centers = cluster_engine.kmeans_videos(
    features, k=2, max_iter=5, min_unique_watchers=2
)
assert video_labels == [0, 0, 1] or video_labels == [1, 1, 0]
assert len(video_centers) == 2

low_watch_videos = videos + [{"video_id": 3, "category": "科技", "tags": ["c"]}]
low_watch_behaviors = cluster_behaviors + [[2, 3, "watch", 0, 10]]
low_watch_engine = ClusteringEngine()
low_watch_features = low_watch_engine.build_video_features(
    low_watch_videos, low_watch_behaviors, num_users=6
)
low_watch_labels, _ = low_watch_engine.kmeans_videos(
    low_watch_features, k=2, max_iter=5, min_unique_watchers=2
)
assert low_watch_labels[3] == -1
low_watch_info = low_watch_engine.get_cluster_info(
    low_watch_labels, low_watch_videos, "video"
)
assert any(info.get("cluster_name") == "低观看/无观看视频" for info in low_watch_info)
print("✓ Video clustering uses watched-user similarity OK")

print("\n全部数据结构测试通过！")
