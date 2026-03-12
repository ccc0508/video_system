"""
图表配置工具

解决 matplotlib 中文显示问题。
"""
import matplotlib
import matplotlib.pyplot as plt


def setup_chinese_font():
    """配置 matplotlib 支持中文显示"""
    plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'SimSun', 'KaiTi']
    plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
