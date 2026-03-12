"""
自实现图 (Graph)

邻接表表示的加权无向图。
用于: F6/F7 聚类中的相似度网络和连通分量分析。
"""
from collections import deque


class Graph:
    """
    加权无向图 (邻接表存储)

    内部结构: dict<node_id, list<(neighbor_id, weight)>>
    """

    def __init__(self):
        self._adj = {}  # {node: [(neighbor, weight), ...]}

    def add_node(self, node):
        """添加节点"""
        if node not in self._adj:
            self._adj[node] = []

    def add_edge(self, u, v, weight=1.0):
        """添加无向边"""
        self.add_node(u)
        self.add_node(v)
        self._adj[u].append((v, weight))
        self._adj[v].append((u, weight))

    def neighbors(self, node):
        """获取邻居列表 [(neighbor_id, weight), ...]"""
        return self._adj.get(node, [])

    def nodes(self):
        """获取所有节点"""
        return list(self._adj.keys())

    def bfs(self, start):
        """广度优先遍历，返回访问的节点列表"""
        visited = set()
        queue = deque([start])
        visited.add(start)
        result = []

        while queue:
            node = queue.popleft()
            result.append(node)
            for neighbor, _ in self._adj.get(node, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        return result

    def connected_components(self):
        """计算连通分量，返回 [component1, component2, ...]"""
        visited = set()
        components = []

        for node in self._adj:
            if node not in visited:
                component = self.bfs(node)
                visited.update(component)
                components.append(component)

        return components

    def degree(self, node):
        """获取节点的度"""
        return len(self._adj.get(node, []))

    @property
    def num_nodes(self):
        return len(self._adj)

    @property
    def num_edges(self):
        return sum(len(neighbors) for neighbors in self._adj.values()) // 2

    def __contains__(self, node):
        return node in self._adj

    def __repr__(self):
        return f"Graph(nodes={self.num_nodes}, edges={self.num_edges})"
