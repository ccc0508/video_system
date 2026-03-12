"""
相似度计算引擎

基于协同过滤计算用户相似度 (余弦相似度)。
用于: F3 相似用户分析。
"""
from data_structures.sparse_matrix import SparseMatrix
from data_structures.heap import MinHeap


class SimilarityEngine:
    """
    用户相似度计算引擎

    基于用户-视频交互的稀疏矩阵，用余弦相似度衡量用户间的兴趣相似程度。
    使用最小堆维护 Top-K 最相似的用户。
    """

    def __init__(self):
        self.matrix = None       # 稀疏矩阵
        self.user_count = 0
        self.video_count = 0
        self._user_watched = {}  # {user_id: set(video_ids)}

    def build_matrix(self, users, behaviors, progress_callback=None):
        """
        从行为数据构建用户-视频交互稀疏矩阵

        Args:
            users: 用户列表
            behaviors: 行为记录列表 [[user_id, video_id, action, ts, dur], ...]
            progress_callback: 进度回调
        """
        self.user_count = len(users)
        # 查找最大 video_id
        max_vid = 0
        for b in behaviors:
            vid = int(b[1])
            if vid > max_vid:
                max_vid = vid
        self.video_count = max_vid + 1

        self.matrix = SparseMatrix(self.user_count, self.video_count)
        self._user_watched = {}

        total = len(behaviors)
        for i, b in enumerate(behaviors):
            uid = int(b[0])
            vid = int(b[1])
            # 简单设置为 1（观看过）
            self.matrix.set(uid, vid, 1)

            if uid not in self._user_watched:
                self._user_watched[uid] = set()
            self._user_watched[uid].add(vid)

            if progress_callback and (i + 1) % 50000 == 0:
                progress_callback(i + 1, total)

        self.matrix.build()

        if progress_callback:
            progress_callback(total, total)

    def find_similar_users(self, target_uid, top_k=20, progress_callback=None):
        """
        找到与目标用户最相似的 Top-K 个用户

        使用最小堆维护 Top-K，时间复杂度 O(N × log K)。

        Args:
            target_uid: 目标用户 ID
            top_k: 返回的相似用户数量

        Returns:
            [(user_id, similarity_score), ...] 按得分降序排列
        """
        if self.matrix is None:
            return []

        # 检查目标用户是否有观看记录
        if self.matrix.row_nnz(target_uid) == 0:
            return []

        heap = MinHeap(capacity=top_k)

        for uid in range(self.user_count):
            if uid == target_uid:
                continue
            if self.matrix.row_nnz(uid) == 0:
                continue

            sim = self.matrix.cosine_similarity(target_uid, uid)
            if sim > 0:
                heap.insert((sim, uid))

            if progress_callback and (uid + 1) % 1000 == 0:
                progress_callback(uid + 1, self.user_count)

        if progress_callback:
            progress_callback(self.user_count, self.user_count)

        # 从堆中取出结果（降序）
        result = heap.to_sorted_list(reverse=True)
        return [(uid, score) for score, uid in result]

    def get_user_watched(self, uid):
        """获取用户观看过的视频集合"""
        return self._user_watched.get(uid, set())

    def jaccard_similarity(self, uid1, uid2):
        """计算两个用户的 Jaccard 相似度"""
        set1 = self._user_watched.get(uid1, set())
        set2 = self._user_watched.get(uid2, set())
        if not set1 or not set2:
            return 0.0
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        return intersection / union if union > 0 else 0.0
