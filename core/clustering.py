"""
聚类分析引擎

支持 K-Means 聚类，用于视频聚类(F6)和用户聚类(F7)。
"""
import random
import math
from collections import defaultdict


class ClusteringEngine:
    """
    K-Means 聚类引擎

    将数据点按特征向量聚成 K 个簇:
    - F6: 视频按观看用户分布聚类
    - F7: 用户按观看行为聚类
    """

    def __init__(self):
        self.centers = []
        self.labels = []
        self.features = []

    def build_video_features(self, videos, behaviors, num_users, progress_callback=None):
        """
        构建视频特征向量

        每个视频的特征 = 各分类标签的观看用户比例（降维到分类维度）。

        Args:
            videos: 视频列表
            behaviors: 行为记录
            num_users: 用户总数
            progress_callback: 进度回调

        Returns:
            features: [[f1, f2, ...], ...] 每行一个视频
        """
        from core.data_generator import CATEGORY_LIST

        num_videos = len(videos)
        num_categories = len(CATEGORY_LIST)
        cat_index = {cat: i for i, cat in enumerate(CATEGORY_LIST)}

        # 统计每个视频的观看用户所偏好的类目分布
        video_user_cats = defaultdict(lambda: defaultdict(int))

        total = len(behaviors)
        for i, b in enumerate(behaviors):
            vid = int(b[1])
            uid = int(b[0])
            if 0 <= vid < num_videos:
                cat = videos[vid].get("category", "")
                if cat in cat_index:
                    video_user_cats[vid][cat_index[cat]] += 1

            if progress_callback and (i + 1) % 50000 == 0:
                progress_callback(i + 1, total)

        # 归一化为特征向量
        features = []
        for vid in range(num_videos):
            vec = [0.0] * num_categories
            cat_counts = video_user_cats.get(vid, {})
            total_count = sum(cat_counts.values())
            if total_count > 0:
                for cat_idx, count in cat_counts.items():
                    vec[cat_idx] = count / total_count
            features.append(vec)

        if progress_callback:
            progress_callback(total, total)

        self.features = features
        return features

    def build_user_features(self, users, behaviors, videos, progress_callback=None):
        """
        构建用户特征向量

        每个用户的特征 = 观看视频的类目分布比例。

        Args:
            users: 用户列表
            behaviors: 行为记录
            videos: 视频列表
            progress_callback: 进度回调

        Returns:
            features: [[f1, f2, ...], ...]
        """
        from core.data_generator import CATEGORY_LIST

        num_users = len(users)
        num_categories = len(CATEGORY_LIST)
        cat_index = {cat: i for i, cat in enumerate(CATEGORY_LIST)}

        user_cat_counts = defaultdict(lambda: defaultdict(int))

        total = len(behaviors)
        for i, b in enumerate(behaviors):
            uid = int(b[0])
            vid = int(b[1])
            if 0 <= vid < len(videos):
                cat = videos[vid].get("category", "")
                if cat in cat_index:
                    user_cat_counts[uid][cat_index[cat]] += 1

            if progress_callback and (i + 1) % 50000 == 0:
                progress_callback(i + 1, total)

        features = []
        for uid in range(num_users):
            vec = [0.0] * num_categories
            cat_counts = user_cat_counts.get(uid, {})
            total_count = sum(cat_counts.values())
            if total_count > 0:
                for cat_idx, count in cat_counts.items():
                    vec[cat_idx] = count / total_count
            features.append(vec)

        if progress_callback:
            progress_callback(total, total)

        self.features = features
        return features

    def kmeans(self, features, k=5, max_iter=50, progress_callback=None):
        """
        K-Means 聚类

        Args:
            features: 特征矩阵 (list of lists)
            k: 聚类数
            max_iter: 最大迭代次数
            progress_callback: 进度回调

        Returns:
            labels: 每个数据点的簇标签 [0, 2, 1, ...]
            centers: 聚类中心 [[f1, f2, ...], ...]
        """
        n = len(features)
        dim = len(features[0]) if features else 0

        if n == 0 or dim == 0 or k <= 0:
            return [], []

        k = min(k, n)

        # 初始化：随机选 K 个点作为中心
        indices = random.sample(range(n), k)
        centers = [features[i][:] for i in indices]

        labels = [0] * n

        for iteration in range(max_iter):
            # Step 1: 分配每个点到最近的中心
            changed = False
            for i in range(n):
                min_dist = float('inf')
                min_label = 0
                for j in range(k):
                    dist = self._euclidean_dist(features[i], centers[j])
                    if dist < min_dist:
                        min_dist = dist
                        min_label = j
                if labels[i] != min_label:
                    labels[i] = min_label
                    changed = True

            if progress_callback:
                progress_callback(iteration + 1, max_iter)

            # Step 2: 更新中心
            new_centers = [[0.0] * dim for _ in range(k)]
            counts = [0] * k
            for i in range(n):
                cluster = labels[i]
                counts[cluster] += 1
                for d in range(dim):
                    new_centers[cluster][d] += features[i][d]

            for j in range(k):
                if counts[j] > 0:
                    for d in range(dim):
                        new_centers[j][d] /= counts[j]
                else:
                    # 空簇：随机重新选一个点
                    new_centers[j] = features[random.randint(0, n - 1)][:]

            centers = new_centers

            if not changed:
                break

        self.labels = labels
        self.centers = centers

        if progress_callback:
            progress_callback(max_iter, max_iter)

        return labels, centers

    def get_cluster_info(self, labels, items, item_type="video"):
        """
        获取各簇的详细信息

        Args:
            labels: 聚类标签
            items: 原始数据项列表（视频或用户）
            item_type: "video" 或 "user"

        Returns:
            [{cluster_id, size, members: [...], common_features: ...}, ...]
        """
        from core.data_generator import CATEGORY_LIST

        clusters = defaultdict(list)
        for i, label in enumerate(labels):
            if i < len(items):
                clusters[label].append(items[i])

        result = []
        for cluster_id in sorted(clusters.keys()):
            members = clusters[cluster_id]
            info = {
                "cluster_id": cluster_id,
                "size": len(members),
                "members": members[:50],  # 最多展示 50 个
            }

            # 分析共同特征
            if item_type == "video":
                cat_counts = defaultdict(int)
                for m in members:
                    cat_counts[m.get("category", "")] += 1
                top_cats = sorted(cat_counts.items(), key=lambda x: -x[1])[:5]
                info["top_categories"] = top_cats
            elif item_type == "user":
                tag_counts = defaultdict(int)
                for m in members:
                    for tag in m.get("preference_tags", []):
                        tag_counts[tag] += 1
                top_tags = sorted(tag_counts.items(), key=lambda x: -x[1])[:10]
                info["top_tags"] = top_tags

            result.append(info)

        return result

    @staticmethod
    def _euclidean_dist(a, b):
        """欧氏距离"""
        return math.sqrt(sum((ai - bi) ** 2 for ai, bi in zip(a, b)))
