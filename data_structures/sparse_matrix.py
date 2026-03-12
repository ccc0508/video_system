"""
自实现稀疏矩阵 (CSR 格式)

用于存储用户-视频交互矩阵，支持高效的行向量提取和向量点积。
用于: F3 相似用户计算（余弦相似度）。
"""
import math


class SparseMatrix:
    """
    CSR (Compressed Sparse Row) 稀疏矩阵

    适用于 10000 用户 × 100000 视频的交互矩阵，
    非零元素仅占 0.05%-0.2%，CSR 格式可节省 500+ 倍空间。

    内部存储:
    - values: 非零值数组
    - col_indices: 每个非零值对应的列索引
    - row_ptr: 每行在 values 中的起始位置
    """

    def __init__(self, num_rows, num_cols):
        self.num_rows = num_rows
        self.num_cols = num_cols
        self.values = []
        self.col_indices = []
        self.row_ptr = [0] * (num_rows + 1)
        self._built = False

        # 构建期间使用临时存储
        self._temp_data = {}  # {row: [(col, val), ...]}

    def set(self, row, col, value):
        """设置矩阵元素（构建阶段使用）"""
        if self._built:
            raise RuntimeError("矩阵已构建，不可修改")
        if value == 0:
            return
        if row not in self._temp_data:
            self._temp_data[row] = []
        self._temp_data[row].append((col, value))

    def build(self):
        """将临时数据编译为 CSR 格式（构建完成后调用）"""
        self.values = []
        self.col_indices = []
        self.row_ptr = [0] * (self.num_rows + 1)

        for row in range(self.num_rows):
            entries = self._temp_data.get(row, [])
            # 按列索引排序
            entries.sort(key=lambda x: x[0])
            for col, val in entries:
                self.values.append(val)
                self.col_indices.append(col)
            self.row_ptr[row + 1] = len(self.values)

        self._temp_data = {}
        self._built = True

    def get_row(self, row):
        """获取某行的非零元素，返回 [(col, value), ...]"""
        if not self._built:
            # 未构建时从临时数据返回
            return self._temp_data.get(row, [])
        start = self.row_ptr[row]
        end = self.row_ptr[row + 1]
        return list(zip(self.col_indices[start:end], self.values[start:end]))

    def get_row_cols(self, row):
        """获取某行的非零列索引集合"""
        if not self._built:
            return set(col for col, _ in self._temp_data.get(row, []))
        start = self.row_ptr[row]
        end = self.row_ptr[row + 1]
        return set(self.col_indices[start:end])

    def row_dot(self, row1, row2):
        """计算两行的点积（只遍历非零元素交集）"""
        cols1 = self.get_row(row1)
        cols2_dict = {}
        for col, val in self.get_row(row2):
            cols2_dict[col] = val

        dot = 0.0
        for col, val in cols1:
            if col in cols2_dict:
                dot += val * cols2_dict[col]
        return dot

    def row_norm(self, row):
        """计算某行的 L2 范数"""
        entries = self.get_row(row)
        return math.sqrt(sum(v * v for _, v in entries))

    def cosine_similarity(self, row1, row2):
        """计算两行的余弦相似度"""
        dot = self.row_dot(row1, row2)
        if dot == 0:
            return 0.0
        norm1 = self.row_norm(row1)
        norm2 = self.row_norm(row2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot / (norm1 * norm2)

    def row_nnz(self, row):
        """获取某行的非零元素个数"""
        if not self._built:
            return len(self._temp_data.get(row, []))
        return self.row_ptr[row + 1] - self.row_ptr[row]

    @property
    def nnz(self):
        """总非零元素个数"""
        return len(self.values)

    def __repr__(self):
        return (f"SparseMatrix({self.num_rows}×{self.num_cols}, "
                f"nnz={self.nnz}, "
                f"density={self.nnz / (self.num_rows * self.num_cols) * 100:.4f}%)")
