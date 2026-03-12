"""
热度预测引擎

基于历史观看数据进行时间序列分析，预测视频未来热度。
用于: F5 视频热度预测。
"""
import time
from collections import defaultdict


class Predictor:
    """
    视频热度预测引擎

    使用时间序列数组存储历史数据，支持:
    - 移动平均法
    - 线性回归预测
    - 加权移动平均
    """

    def __init__(self):
        self._video_daily = {}  # {video_id: {day_offset: count}}

    def build_time_series(self, behaviors, progress_callback=None):
        """
        从行为数据构建每个视频的日观看时间序列

        Args:
            behaviors: 行为记录列表
            progress_callback: 进度回调
        """
        now = int(time.time())
        video_daily = defaultdict(lambda: defaultdict(int))

        total = len(behaviors)
        for i, b in enumerate(behaviors):
            vid = int(b[1])
            ts = int(b[3])
            # 计算距今天数
            day_offset = (now - ts) // 86400
            video_daily[vid][day_offset] += 1

            if progress_callback and (i + 1) % 50000 == 0:
                progress_callback(i + 1, total)

        self._video_daily = dict(video_daily)

        if progress_callback:
            progress_callback(total, total)

    def predict(self, video_id, history_days=30, predict_days=14):
        """
        预测视频热度

        Args:
            video_id: 视频 ID
            history_days: 历史天数
            predict_days: 预测天数

        Returns:
            {
                "history": [(day, count), ...],
                "moving_avg": [(day, avg), ...],
                "prediction": [(day, predicted), ...],
                "stats": {...}
            }
        """
        daily = self._video_daily.get(video_id, {})
        if not daily:
            return None

        # 构建历史时间序列（从远到近）
        history = []
        for day in range(history_days, -1, -1):
            count = daily.get(day, 0)
            history.append((-day, count))  # 负数表示过去

        # 移动平均（窗口大小 7 天）
        window = 7
        moving_avg = self._moving_average(history, window)

        # 线性回归预测
        prediction = self._linear_predict(history, predict_days)

        # 统计信息
        total_views = sum(daily.values())
        avg_daily = total_views / max(len(daily), 1)
        recent_7 = sum(daily.get(d, 0) for d in range(7))
        prev_7 = sum(daily.get(d, 0) for d in range(7, 14))
        growth_rate = ((recent_7 - prev_7) / max(prev_7, 1)) * 100

        return {
            "history": history,
            "moving_avg": moving_avg,
            "prediction": prediction,
            "stats": {
                "total_views": total_views,
                "avg_daily": round(avg_daily, 1),
                "recent_7_days": recent_7,
                "growth_rate": round(growth_rate, 1),
            }
        }

    def _moving_average(self, series, window):
        """
        移动平均

        使用环形缓冲区思想: O(1) 更新每个窗口的均值。
        """
        if len(series) < window:
            return []

        result = []
        window_sum = sum(v for _, v in series[:window])

        for i in range(window - 1, len(series)):
            if i >= window:
                window_sum += series[i][1]
                window_sum -= series[i - window][1]
            avg = window_sum / window
            result.append((series[i][0], round(avg, 2)))

        return result

    def _linear_predict(self, history, predict_days):
        """
        线性回归预测

        最小二乘法拟合 y = a*x + b，然后外推未来。
        """
        n = len(history)
        if n < 2:
            return []

        # 用最近的数据点做回归
        x_vals = list(range(n))
        y_vals = [v for _, v in history]

        sum_x = sum(x_vals)
        sum_y = sum(y_vals)
        sum_xy = sum(x * y for x, y in zip(x_vals, y_vals))
        sum_xx = sum(x * x for x in x_vals)

        denominator = n * sum_xx - sum_x * sum_x
        if denominator == 0:
            return []

        a = (n * sum_xy - sum_x * sum_y) / denominator
        b = (sum_y - a * sum_x) / n

        # 外推预测
        prediction = []
        for day in range(1, predict_days + 1):
            x = n + day - 1
            predicted = max(0, a * x + b)
            prediction.append((day, round(predicted, 1)))

        return prediction

    def get_video_stats(self, video_id):
        """获取视频的基础统计信息"""
        daily = self._video_daily.get(video_id, {})
        if not daily:
            return None
        total = sum(daily.values())
        days = max(daily.keys()) - min(daily.keys()) + 1 if daily else 1
        return {
            "total_views": total,
            "active_days": len(daily),
            "span_days": days,
            "avg_daily": round(total / days, 1) if days > 0 else 0,
        }
