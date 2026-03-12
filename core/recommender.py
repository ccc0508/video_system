"""
推荐引擎

基于用户的协同过滤 (User-Based CF) 推荐视频。
用于: F4 视频推荐。
"""
from data_structures.heap import MinHeap


class Recommender:
    """
    视频推荐引擎

    推荐逻辑:
    1. 找到目标用户的 Top-K 相似用户（复用 SimilarityEngine）
    2. 汇总相似用户看过但目标用户没看过的视频
    3. 按加权得分排序，取 Top-N
    """

    def __init__(self, similarity_engine):
        """
        Args:
            similarity_engine: SimilarityEngine 实例
        """
        self.sim_engine = similarity_engine

    def recommend(self, target_uid, similar_users, top_n=20, videos=None):
        """
        为目标用户推荐视频

        Args:
            target_uid: 目标用户 ID
            similar_users: 相似用户列表 [(uid, sim_score), ...]
            top_n: 推荐视频数量
            videos: 视频列表（用于附带视频信息）

        Returns:
            [{"video_id": ..., "score": ..., "reason": ..., "video_info": ...}, ...]
        """
        target_watched = self.sim_engine.get_user_watched(target_uid)

        # 候选视频得分表
        candidate_scores = {}  # {video_id: total_score}
        candidate_sources = {}  # {video_id: [(uid, sim)]}

        for neighbor_uid, sim_score in similar_users:
            neighbor_watched = self.sim_engine.get_user_watched(neighbor_uid)
            # 找出邻居看过但目标用户没看过的视频
            new_videos = neighbor_watched - target_watched
            for vid in new_videos:
                if vid not in candidate_scores:
                    candidate_scores[vid] = 0.0
                    candidate_sources[vid] = []
                candidate_scores[vid] += sim_score
                candidate_sources[vid].append((neighbor_uid, sim_score))

        if not candidate_scores:
            return []

        # 用最小堆选 Top-N
        heap = MinHeap(capacity=top_n)
        for vid, score in candidate_scores.items():
            heap.insert((score, vid))

        # 取出结果
        sorted_items = heap.to_sorted_list(reverse=True)

        results = []
        for score, vid in sorted_items:
            sources = candidate_sources[vid]
            reason = f"有{len(sources)}位兴趣相似的用户也在看"

            item = {
                "video_id": vid,
                "score": round(score, 4),
                "reason": reason,
                "similar_user_count": len(sources),
            }

            # 附带视频信息
            if videos and 0 <= vid < len(videos):
                v = videos[vid]
                item["title"] = v.get("title", "")
                item["category"] = v.get("category", "")
                item["tags"] = v.get("tags", [])

            results.append(item)

        return results
