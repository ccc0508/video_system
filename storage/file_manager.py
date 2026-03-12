"""
文件管理器

负责所有数据文件的读写操作，支持 JSON 和 CSV 格式。
大文件（行为日志）采用分块流式读取。
"""
import json
import csv
import os

# 数据目录
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")


def ensure_dirs():
    """确保数据目录存在"""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(RESULTS_DIR, exist_ok=True)
    os.makedirs(os.path.join(DATA_DIR, "indexes"), exist_ok=True)


def save_json(data, filename, directory=DATA_DIR):
    """保存数据到 JSON 文件"""
    ensure_dirs()
    filepath = os.path.join(directory, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=None)  # 不缩进以节省空间
    return filepath


def load_json(filename, directory=DATA_DIR):
    """从 JSON 文件加载数据"""
    filepath = os.path.join(directory, filename)
    if not os.path.exists(filepath):
        return None
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_csv(data, filename, headers=None, directory=DATA_DIR):
    """保存数据到 CSV 文件"""
    ensure_dirs()
    filepath = os.path.join(directory, filename)
    with open(filepath, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        if headers:
            writer.writerow(headers)
        writer.writerows(data)
    return filepath


def load_csv_chunked(filename, chunk_size=10000, directory=DATA_DIR):
    """
    分块读取 CSV 文件（生成器），每次返回 chunk_size 行。
    适用于百万级行为日志。
    """
    filepath = os.path.join(directory, filename)
    if not os.path.exists(filepath):
        return
    with open(filepath, 'r', encoding='utf-8', newline='') as f:
        reader = csv.reader(f)
        header = next(reader, None)
        chunk = []
        for row in reader:
            chunk.append(row)
            if len(chunk) >= chunk_size:
                yield header, chunk
                chunk = []
        if chunk:
            yield header, chunk


def load_csv_all(filename, directory=DATA_DIR):
    """一次性加载 CSV 文件的所有行"""
    filepath = os.path.join(directory, filename)
    if not os.path.exists(filepath):
        return None, []
    with open(filepath, 'r', encoding='utf-8', newline='') as f:
        reader = csv.reader(f)
        header = next(reader, None)
        rows = list(reader)
    return header, rows


def save_result(data, filename):
    """保存分析结果到 results 目录"""
    return save_json(data, filename, directory=RESULTS_DIR)


def load_result(filename):
    """加载分析结果"""
    return load_json(filename, directory=RESULTS_DIR)


def data_file_exists(filename, directory=DATA_DIR):
    """检查数据文件是否存在"""
    return os.path.exists(os.path.join(directory, filename))


def get_file_size(filename, directory=DATA_DIR):
    """获取文件大小（MB）"""
    filepath = os.path.join(directory, filename)
    if not os.path.exists(filepath):
        return 0
    return os.path.getsize(filepath) / (1024 * 1024)
