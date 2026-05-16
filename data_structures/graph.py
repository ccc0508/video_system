"""
自实现图 (Graph)

邻接表表示的加权无向图。
用于: F3 相似用户网络和连通分量分析。
"""
from collections import deque
from data_structures.hash_map import HashMap


class Graph:
    """
    加权无向图 (邻接表存储)

    内部结构: HashMap<node_id, list<(neighbor_id, weight)>>
    """

    def __init__(self):
        self._adj = HashMap()  # HashMap<node, [(neighbor, weight), ...]>

    def add_node(self, node):
        """添加节点"""
        if node not in self._adj:
            self._adj.put(node, [])

    def add_edge(self, u, v, weight=1.0):
        """添加无向边"""
        self.add_node(u)
        self.add_node(v)
        self._upsert_neighbor(u, v, weight)
        self._upsert_neighbor(v, u, weight)

    def _upsert_neighbor(self, node, neighbor, weight):
        """添加或更新一条邻接边，避免重复边影响度数和连通分析。"""
        neighbors = self._adj.get(node, [])
        for i, (current, _) in enumerate(neighbors):
            if current == neighbor:
                neighbors[i] = (neighbor, weight)
                return
        neighbors.append((neighbor, weight))

    def neighbors(self, node):
        """获取邻居列表 [(neighbor_id, weight), ...]"""
        return self._adj.get(node, [])

    def nodes(self):
        """获取所有节点"""
        return self._adj.keys()

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
