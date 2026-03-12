"""
数据生成器

生成模拟的视频信息库（10万+）和用户行为数据（1万+用户）。
F1: 视频生成  F2: 用户和行为生成
"""
import random
import time

from storage.file_manager import save_json, save_csv

# ==================== 视频分类与标签体系 ====================

CATEGORIES = {
    "搞笑幽默": ["段子", "整蛊", "搞笑配音", "沙雕动画", "脱口秀", "模仿秀", "方言搞笑", "反转剧情", "神评论", "表情包"],
    "音乐舞蹈": ["流行音乐", "古风音乐", "说唱", "翻唱", "乐器演奏", "街舞", "民族舞", "拉丁舞", "广场舞", "编舞教学"],
    "美食烹饪": ["家常菜", "烘焙", "甜品", "地方美食", "快手菜", "减脂餐", "火锅", "烧烤", "探店", "美食测评"],
    "旅行风景": ["国内游", "出境游", "自驾游", "背包客", "城市风光", "自然风景", "古镇", "海岛", "雪山", "航拍"],
    "时尚穿搭": ["日常穿搭", "职场穿搭", "街头潮流", "汉服", "妆容教程", "护肤", "发型", "饰品", "穿搭技巧", "时尚测评"],
    "科技数码": ["手机评测", "电脑硬件", "智能家居", "数码配件", "APP推荐", "科技前沿", "AI技术", "编程教程", "拆机", "性价比"],
    "游戏电竞": ["王者荣耀", "原神", "英雄联盟", "和平精英", "游戏攻略", "主播集锦", "电竞赛事", "独立游戏", "怀旧游戏", "游戏测评"],
    "影视解说": ["电影解说", "电视剧推荐", "综艺片段", "动漫推荐", "纪录片", "经典影视", "影视混剪", "预告片", "幕后花絮", "影评"],
    "生活日常": ["日常vlog", "房间改造", "收纳整理", "购物分享", "租房装修", "独居生活", "打工日记", "校园生活", "减压", "生活技巧"],
    "手工DIY":  ["折纸", "编织", "绘画", "书法", "黏土", "模型", "木工", "刺绣", "首饰制作", "创意改造"],
    "教育学习": ["英语学习", "考研", "公务员", "职场技能", "读书分享", "历史知识", "科普", "数学思维", "语文作文", "学习方法"],
    "新闻资讯": ["时事热点", "社会新闻", "国际新闻", "科技资讯", "财经新闻", "本地新闻", "深度报道", "辟谣", "政策解读", "行业动态"],
    "健康养生": ["中医养生", "健身教程", "瑜伽", "跑步", "营养搭配", "减肥", "心理健康", "睡眠改善", "急救知识", "医学科普"],
    "宠物动物": ["猫", "狗", "仓鼠", "兔子", "鹦鹉", "爬宠", "水族", "野生动物", "宠物日常", "宠物训练"],
    "体育运动": ["篮球", "足球", "乒乓球", "羽毛球", "游泳", "滑板", "跑酷", "格斗", "体育赛事", "运动装备"],
    "汽车":     ["新车评测", "二手车", "改装", "驾驶技巧", "事故分析", "自驾路线", "新能源车", "摩托车", "汽车保养", "车载好物"],
    "母婴亲子": ["育儿知识", "孕期护理", "辅食制作", "亲子游戏", "绘本推荐", "宝宝日常", "儿童教育", "二胎生活", "月子护理", "儿童安全"],
    "情感心理": ["恋爱技巧", "婚姻经营", "心理测试", "社交技巧", "自我提升", "情感故事", "失恋治愈", "家庭关系", "职场人际", "心灵鸡汤"],
    "财经理财": ["股票基金", "理财入门", "房产", "保险", "创业", "副业", "经济分析", "税务知识", "数字货币", "省钱攻略"],
    "三农":     ["种植技术", "养殖技术", "农村生活", "乡村美食", "农产品", "农机设备", "农村创业", "赶集", "钓鱼", "田园风光"],
}

CATEGORY_LIST = list(CATEGORIES.keys())

# 视频标题模板
TITLE_TEMPLATES = {
    "搞笑幽默": ["太搞笑了！{tag}合集", "笑到停不下来的{tag}", "这个{tag}绝了", "高能{tag}来袭", "没想到{tag}还能这样玩"],
    "音乐舞蹈": ["{tag}超好听！", "神仙{tag}安利", "全网最火{tag}", "一听就上头的{tag}", "{tag}教学来了"],
    "美食烹饪": ["{tag}做法大公开", "超简单的{tag}教程", "吃了这个{tag}再也不想出门", "正宗{tag}的做法", "{tag}这样做太香了"],
    "旅行风景": ["{tag}旅行攻略", "带你看最美的{tag}", "{tag}绝美打卡地", "人少景美的{tag}", "{tag}自由行全攻略"],
    "时尚穿搭": ["{tag}分享", "超实用{tag}技巧", "今日{tag}look", "{tag}一周穿搭", "平价{tag}推荐"],
    "科技数码": ["{tag}深度体验", "{tag}到底值不值得买", "全网最详细{tag}评测", "{tag}使用技巧", "{tag}开箱"],
    "游戏电竞": ["{tag}高端操作", "{tag}上分攻略", "震惊！{tag}这波操作", "{tag}新手入门指南", "{tag}精彩集锦"],
    "影视解说": ["{tag}推荐", "一口气看完{tag}", "{tag}深度解析", "被低估的{tag}", "{tag}高燃混剪"],
    "生活日常": ["我的{tag}日常", "{tag}记录", "真实的{tag}分享", "{tag}必看", "超治愈的{tag}"],
    "手工DIY":  ["{tag}教程", "手把手教你{tag}", "超解压的{tag}", "零基础{tag}入门", "{tag}作品展示"],
    "教育学习": ["{tag}干货分享", "高效{tag}方法", "{tag}必备知识点", "一看就懂的{tag}", "{tag}备考攻略"],
    "新闻资讯": ["{tag}最新动态", "关于{tag}你需要知道的", "{tag}深度解读", "今日{tag}速览", "{tag}全面解析"],
    "健康养生": ["{tag}指南", "每天坚持{tag}的好处", "{tag}入门教程", "科学{tag}方法", "{tag}注意事项"],
    "宠物动物": ["我家{tag}又搞事了", "超萌{tag}日常", "{tag}成精了", "养{tag}必看", "{tag}搞笑瞬间"],
    "体育运动": ["{tag}精彩瞬间", "{tag}教学", "震撼{tag}现场", "{tag}入门指南", "{tag}装备推荐"],
    "汽车":     ["{tag}全面测评", "{tag}真实车主分享", "买{tag}前必看", "{tag}使用体验", "{tag}对比分析"],
    "母婴亲子": ["{tag}经验分享", "新手妈妈{tag}指南", "{tag}注意事项", "宝宝{tag}日常", "{tag}好物推荐"],
    "情感心理": ["{tag}小技巧", "关于{tag}的思考", "{tag}真实故事", "学会{tag}受益终生", "{tag}你做对了吗"],
    "财经理财": ["{tag}入门指南", "普通人如何{tag}", "{tag}避坑攻略", "{tag}深度分析", "{tag}实操教程"],
    "三农":     ["{tag}实拍", "农村{tag}日常", "{tag}技术分享", "回乡{tag}记录", "{tag}丰收了"],
}

# 用户昵称素材
SURNAME = ["小", "大", "老", "阿", ""]
NICKNAMES = ["明", "红", "军", "强", "芳", "静", "磊", "洋", "勇", "丽",
             "超", "霞", "杰", "艳", "涛", "慧", "鹏", "琳", "辉", "娟",
             "飞", "玲", "华", "敏", "伟", "娜", "平", "莉", "峰", "燕"]
NICKNAME_SUFFIX = ["同学", "老师", "哥", "姐", "呀", "吖", "er", "酱", "子", "仔",
                   "的日常", "爱生活", "爱美食", "打工人", "在努力", ""]


def generate_videos(count=100000, progress_callback=None):
    """
    生成模拟视频信息库

    Args:
        count: 视频数量 (默认 10 万)
        progress_callback: 进度回调函数 callback(current, total)

    Returns:
        视频列表
    """
    videos = []
    authors_count = count // 20  # 平均每作者 20 个视频

    for i in range(count):
        category = random.choice(CATEGORY_LIST)
        tags = CATEGORIES[category]
        # 每个视频 1-3 个标签
        video_tags = random.sample(tags, min(random.randint(1, 3), len(tags)))
        # 用标签生成标题
        tag_for_title = random.choice(video_tags)
        templates = TITLE_TEMPLATES.get(category, ["{tag}"])
        title = random.choice(templates).format(tag=tag_for_title)

        video = {
            "video_id": i,
            "title": title,
            "category": category,
            "tags": video_tags,
            "duration": random.randint(15, 600),  # 15秒 ~ 10分钟
            "publish_time": _random_timestamp(days_back=365),
            "author_id": random.randint(0, authors_count - 1),
        }
        videos.append(video)

        if progress_callback and (i + 1) % 5000 == 0:
            progress_callback(i + 1, count)

    # 保存到文件
    save_json(videos, "videos.json")

    if progress_callback:
        progress_callback(count, count)

    return videos


def generate_users(count=10000, progress_callback=None):
    """
    生成模拟用户

    Args:
        count: 用户数量 (默认 1 万)
        progress_callback: 进度回调函数

    Returns:
        用户列表
    """
    users = []

    for i in range(count):
        # 每用户偏好 2-5 个类目
        pref_count = random.randint(2, 5)
        pref_categories = random.sample(CATEGORY_LIST, pref_count)
        # 每个偏好类目选 1-3 个标签
        pref_tags = []
        for cat in pref_categories:
            tags = CATEGORIES[cat]
            pref_tags.extend(random.sample(tags, min(random.randint(1, 3), len(tags))))

        name = (random.choice(SURNAME) +
                random.choice(NICKNAMES) +
                random.choice(NICKNAME_SUFFIX))

        user = {
            "user_id": i,
            "name": name,
            "preference_categories": pref_categories,
            "preference_tags": pref_tags,
            "register_time": _random_timestamp(days_back=730),
        }
        users.append(user)

        if progress_callback and (i + 1) % 1000 == 0:
            progress_callback(i + 1, count)

    save_json(users, "users.json")

    if progress_callback:
        progress_callback(count, count)

    return users


def generate_behaviors(users, videos, progress_callback=None):
    """
    模拟用户观看行为 — 基于齐普夫分布(Zipf)的长尾模型

    核心设计:
    1. 视频热度服从 Zipf 分布: 极少数"爆款"视频被海量观看，大量尾部视频少人问津
    2. 用户活跃度服从 Zipf 分布: 少数重度用户产生大量行为，多数轻度用户只看几个
    3. 偏好池内也用 Zipf 加权: 同一类目下的视频热度也有分化
    4. 行为类型与观看深度关联: 看得越久越可能点赞/收藏

    Args:
        users: 用户列表
        videos: 视频列表
        progress_callback: 进度回调函数

    Returns:
        行为总数
    """
    import numpy as np

    num_videos = len(videos)
    total_users = len(users)

    # ========== 1. 用 Zipf 分布生成视频的全局热度权重 ==========
    # Zipf 参数 a=1.5: 头部集中但不至于太极端
    # 先生成排名权重，然后随机打乱（不让 video_id 小的永远最热）
    zipf_weights = 1.0 / np.arange(1, num_videos + 1) ** 1.5
    zipf_weights = zipf_weights / zipf_weights.sum()  # 归一化为概率
    # 随机打乱排名，避免 video_id 与热度强相关
    shuffled_indices = np.random.permutation(num_videos)
    video_popularity = np.zeros(num_videos)
    for rank, vid in enumerate(shuffled_indices):
        video_popularity[vid] = zipf_weights[rank]

    # ========== 2. 建立标签/类目 → 视频ID的索引 ==========
    tag_to_videos = {}
    cat_to_videos = {}
    for v in videos:
        for tag in v["tags"]:
            if tag not in tag_to_videos:
                tag_to_videos[tag] = []
            tag_to_videos[tag].append(v["video_id"])
        cat = v["category"]
        if cat not in cat_to_videos:
            cat_to_videos[cat] = []
        cat_to_videos[cat].append(v["video_id"])

    # ========== 3. 用 Zipf 分布决定每个用户的活跃度 ==========
    # 参数 a=1.3: 少数活跃用户看 300+ 视频，多数用户只看 20-50
    raw_activity = np.random.zipf(a=1.3, size=total_users)
    # 裁剪到合理范围: 最少 20, 最多 500
    user_watch_counts = np.clip(raw_activity, 20, 500).astype(int)

    behaviors = []
    headers = ["user_id", "video_id", "action_type", "timestamp", "watch_duration"]

    for idx, user in enumerate(users):
        user_id = user["user_id"]
        pref_tags = user["preference_tags"]
        pref_cats = user["preference_categories"]

        watch_count = int(user_watch_counts[idx])

        # ---- 偏好视频池（70%来源）----
        pref_video_pool = set()
        for tag in pref_tags:
            pref_video_pool.update(tag_to_videos.get(tag, []))
        for cat in pref_cats:
            pref_video_pool.update(cat_to_videos.get(cat, []))

        pref_list = list(pref_video_pool)
        pref_watch = min(int(watch_count * 0.7), len(pref_list))
        random_watch = watch_count - pref_watch

        watched_videos = set()

        # ---- 偏好池内: 按 Zipf 加权抽样（池内也有热门/冷门之分）----
        if pref_list and pref_watch > 0:
            pref_weights = video_popularity[pref_list]
            pref_probs = pref_weights / pref_weights.sum()
            n_sample = min(pref_watch, len(pref_list))
            selected = np.random.choice(
                pref_list, size=n_sample, replace=False, p=pref_probs
            )
            watched_videos.update(selected.tolist())

        # ---- 随机探索: 按全局 Zipf 热度加权抽样 ----
        if random_watch > 0:
            # 将已看过的视频权重置零
            explore_weights = video_popularity.copy()
            for vid in watched_videos:
                explore_weights[vid] = 0
            total_w = explore_weights.sum()
            if total_w > 0:
                explore_probs = explore_weights / total_w
                n_sample = min(random_watch, int((explore_weights > 0).sum()))
                if n_sample > 0:
                    selected = np.random.choice(
                        num_videos, size=n_sample, replace=False, p=explore_probs
                    )
                    watched_videos.update(selected.tolist())

        # ---- 生成行为记录（行为类型与观看深度关联）----
        for vid in watched_videos:
            video_dur = videos[vid]["duration"]
            # Zipf 热门视频倾向被看更久
            popularity_factor = min(video_popularity[vid] / zipf_weights.mean(), 3.0)
            min_dur = max(5, int(video_dur * 0.1))
            max_dur = video_dur
            # 热门视频的最低观看时长更高
            min_dur = max(min_dur, int(video_dur * 0.2 * popularity_factor))
            watch_dur = random.randint(min(min_dur, max_dur), max_dur)

            # 观看比例越高 → 点赞/收藏概率越大
            watch_ratio = watch_dur / max(video_dur, 1)
            action = "watch"
            if random.random() < 0.25 * watch_ratio:  # 看完全程 → 25% 点赞
                action = "like"
            elif random.random() < 0.12 * watch_ratio:  # 看完全程 → 12% 收藏
                action = "favorite"

            ts = _random_timestamp(days_back=180)
            behaviors.append([user_id, vid, action, ts, watch_dur])

        if progress_callback and (idx + 1) % 500 == 0:
            progress_callback(idx + 1, total_users)

    # 按时间排序
    behaviors.sort(key=lambda x: x[3])

    # 保存到 CSV
    save_csv(behaviors, "behaviors.csv", headers=headers)

    if progress_callback:
        progress_callback(total_users, total_users)

    return len(behaviors)


def _random_timestamp(days_back=365):
    """生成过去 N 天内的随机时间戳"""
    now = int(time.time())
    offset = random.randint(0, days_back * 86400)
    return now - offset
