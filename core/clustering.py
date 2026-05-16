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

        每个视频的特征 = 实际观看用户集合的压缩向量 + 轻量热度特征。

        Args:
            videos: 视频列表
            behaviors: 行为记录
            num_users: 用户总数
            progress_callback: 进度回调

        Returns:
            features: [[f1, f2, ...], ...] 每行一个视频
        """
        num_videos = len(videos)
        user_dim = min(256, max(32, num_users or 32))

        # 统计每个视频的真实观看用户集合。用 user_id 哈希桶压缩高维用户向量，
        # 避免 10 万视频 × 1 万用户的完整矩阵占用过多内存。
        video_unique_users = defaultdict(set)
        video_watch_counts = defaultdict(int)
        video_like_counts = defaultdict(int)
        video_fav_counts = defaultdict(int)

        total = len(behaviors)
        for i, b in enumerate(behaviors):
            vid = int(b[1])
            uid = int(b[0])
            if 0 <= vid < num_videos:
                video_watch_counts[vid] += 1
                video_unique_users[vid].add(uid)

                action = b[2]
                if action == "like":
                    video_like_counts[vid] += 1
                elif action == "favorite":
                    video_fav_counts[vid] += 1

            if progress_callback and (i + 1) % 50000 == 0:
                progress_callback(i + 1, total)

        # 归一化为特征向量
        features = []
        max_watch = max(video_watch_counts.values()) if video_watch_counts else 1
        for vid in range(num_videos):
            vec = [0.0] * (user_dim + 4)
            buckets = defaultdict(float)
            for uid in video_unique_users.get(vid, set()):
                bucket = self._stable_hash(uid) % user_dim
                buckets[bucket] += 1.0
            norm = math.sqrt(sum(value * value for value in buckets.values()))
            if norm > 0:
                for bucket, value in buckets.items():
                    vec[bucket] = value / norm

            stats_offset = user_dim
            watches = video_watch_counts.get(vid, 0)
            vec[stats_offset] = math.log1p(watches) / math.log1p(max_watch)
            vec[stats_offset + 1] = video_like_counts.get(vid, 0) / max(watches, 1)
            vec[stats_offset + 2] = video_fav_counts.get(vid, 0) / max(watches, 1)
            vec[stats_offset + 3] = len(video_unique_users.get(vid, set())) / max(num_users, 1)
            features.append(vec)

        if progress_callback:
            progress_callback(total, total)

        self.features = features
        self._video_feature_categories = None
        return features

    def build_user_features(self, users, behaviors, videos, progress_callback=None):
        """
        构建用户特征向量

        每个用户的特征 = 观看类目分布 + 显式偏好类目/标签 + 活跃和互动特征。

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
        tag_dim = 32
        cat_index = {cat: i for i, cat in enumerate(CATEGORY_LIST)}

        user_cat_counts = defaultdict(lambda: defaultdict(int))
        user_watch_counts = defaultdict(int)
        user_like_counts = defaultdict(int)
        user_fav_counts = defaultdict(int)
        user_watch_seconds = defaultdict(int)

        total = len(behaviors)
        for i, b in enumerate(behaviors):
            uid = int(b[0])
            vid = int(b[1])
            if 0 <= vid < len(videos):
                user_watch_counts[uid] += 1
                action = b[2]
                if action == "like":
                    user_like_counts[uid] += 1
                elif action == "favorite":
                    user_fav_counts[uid] += 1
                try:
                    user_watch_seconds[uid] += int(b[4])
                except (ValueError, TypeError):
                    pass

                cat = videos[vid].get("category", "")
                if cat in cat_index:
                    user_cat_counts[uid][cat_index[cat]] += 1

            if progress_callback and (i + 1) % 50000 == 0:
                progress_callback(i + 1, total)

        features = []
        max_watch = max(user_watch_counts.values()) if user_watch_counts else 1
        for uid in range(num_users):
            vec = [0.0] * (num_categories * 2 + tag_dim + 4)
            cat_counts = user_cat_counts.get(uid, {})
            total_count = sum(cat_counts.values())
            if total_count > 0:
                for cat_idx, count in cat_counts.items():
                    vec[cat_idx] = count / total_count

            user = users[uid] if uid < len(users) else {}
            pref_cats = user.get("preference_categories", [])
            if pref_cats:
                weight = 1.0 / len(pref_cats)
                for cat in pref_cats:
                    if cat in cat_index:
                        vec[num_categories + cat_index[cat]] += weight

            tag_offset = num_categories * 2
            pref_tags = user.get("preference_tags", [])
            if pref_tags:
                tag_weight = 1.0 / len(pref_tags)
                for tag in pref_tags:
                    slot = self._stable_hash(tag) % tag_dim
                    vec[tag_offset + slot] += tag_weight

            stats_offset = tag_offset + tag_dim
            watches = user_watch_counts.get(uid, 0)
            vec[stats_offset] = math.log1p(watches) / math.log1p(max_watch)
            vec[stats_offset + 1] = user_like_counts.get(uid, 0) / max(watches, 1)
            vec[stats_offset + 2] = user_fav_counts.get(uid, 0) / max(watches, 1)
            vec[stats_offset + 3] = user_watch_seconds.get(uid, 0) / max(watches, 1) / 600
            features.append(vec)

        if progress_callback:
            progress_callback(total, total)

        self.features = features
        self._video_feature_categories = None
        self._user_feature_categories = [
            "|".join(sorted(user.get("preference_categories") or [""]))
            for user in users
        ]
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

        feature_categories = getattr(self, "_video_feature_categories", None)
        balance_limit = None
        if feature_categories and len(feature_categories) == n:
            centers = self._init_centers_by_category(features, feature_categories, k)
        elif getattr(self, "_user_feature_categories", None) and len(self._user_feature_categories) == n:
            centers = self._init_centers_by_category(features, self._user_feature_categories, k)
            balance_limit = math.ceil(n / k * 1.25)
        else:
            # 初始化：用最远点优先选择中心，避免随机中心都落在同一大类附近。
            indices = self._init_centers_farthest_first(features, k)
            centers = [features[i][:] for i in indices]

        labels = [0] * n

        for iteration in range(max_iter):
            # Step 1: 分配每个点到最近的中心
            changed = False
            assigned_counts = [0] * k
            for i in range(n):
                distances = [
                    (self._euclidean_dist(features[i], centers[j]), j)
                    for j in range(k)
                ]
                distances.sort(key=lambda item: item[0])
                min_dist, min_label = distances[0]
                for dist, candidate in distances:
                    if balance_limit is not None and assigned_counts[candidate] >= balance_limit:
                        continue
                    if abs(dist - min_dist) <= 1e-12 and assigned_counts[candidate] < assigned_counts[min_label]:
                        min_label = candidate
                    else:
                        min_label = candidate
                    break
                if labels[i] != min_label:
                    labels[i] = min_label
                    changed = True
                assigned_counts[min_label] += 1

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

    def _init_centers_farthest_first(self, features, k):
        """选择彼此距离更远的初始中心，降低单个大簇吞并多数样本的概率。"""
        n = len(features)
        first = random.randint(0, n - 1)
        centers = [first]
        min_dists = [self._euclidean_dist(vec, features[first]) for vec in features]

        while len(centers) < k:
            next_idx = max(range(n), key=lambda idx: min_dists[idx])
            if min_dists[next_idx] == 0:
                remaining = [idx for idx in range(n) if idx not in centers]
                if not remaining:
                    break
                next_idx = random.choice(remaining)
            centers.append(next_idx)
            for idx, vec in enumerate(features):
                dist = self._euclidean_dist(vec, features[next_idx])
                if dist < min_dists[idx]:
                    min_dists[idx] = dist

        while len(centers) < k:
            candidate = random.randint(0, n - 1)
            if candidate not in centers:
                centers.append(candidate)
        return centers

    def _init_centers_by_category(self, features, categories, k):
        """按视频类目分层初始化中心，避免未选中类目全部贴到同一个随机中心。"""
        category_counts = defaultdict(int)
        for cat in categories:
            category_counts[cat] += 1

        buckets = [[] for _ in range(k)]
        bucket_sizes = [0] * k
        for cat, count in sorted(category_counts.items(), key=lambda item: -item[1]):
            bucket = min(range(k), key=lambda idx: bucket_sizes[idx])
            buckets[bucket].append(cat)
            bucket_sizes[bucket] += count

        dim = len(features[0]) if features else 0
        centers = []
        for bucket_cats in buckets:
            indexes = [
                idx for idx, cat in enumerate(categories)
                if cat in bucket_cats
            ]
            if not indexes:
                indexes = [random.randint(0, len(features) - 1)]

            center = [0.0] * dim
            for idx in indexes:
                for d, value in enumerate(features[idx]):
                    center[d] += value
            centers.append([value / len(indexes) for value in center])

        return centers

    @staticmethod
    def _stable_hash(text):
        """稳定字符串哈希，避免 Python 进程级 hash 随机盐影响聚类结果。"""
        value = 0
        for ch in str(text):
            value = (value * 131 + ord(ch)) & 0xFFFFFFFF
        return value
