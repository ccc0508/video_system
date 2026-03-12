"""
自实现倒排索引 (Inverted Index)

将标签/类目映射到视频 ID 列表，支持单词条和多词条检索。
用于: F1 视频搜索（按标签/类目快速检索）。
"""


class InvertedIndex:
    """
    倒排索引

    内部结构: HashMap<term, Set<doc_id>>
    - 每个词条 (term) 映射到包含该词条的文档 ID 集合
    - 支持 AND/OR 多词条检索
    """

    def __init__(self):
        self._index = {}  # {term: set(doc_ids)}

    def add(self, term, doc_id):
        """添加一条索引: 词条 → 文档 ID"""
        if term not in self._index:
            self._index[term] = set()
        self._index[term].add(doc_id)

    def add_many(self, terms, doc_id):
        """批量添加: 多个词条 → 同一文档 ID"""
        for term in terms:
            self.add(term, doc_id)

    def search(self, term):
        """单词条检索，返回 doc_id 集合"""
        return self._index.get(term, set())

    def search_and(self, terms):
        """多词条 AND 检索（交集）"""
        if not terms:
            return set()
        result = self.search(terms[0]).copy()
        for term in terms[1:]:
            result &= self.search(term)
        return result

    def search_or(self, terms):
        """多词条 OR 检索（并集）"""
        result = set()
        for term in terms:
            result |= self.search(term)
        return result

    def remove(self, term, doc_id):
        """从索引中移除一条记录"""
        if term in self._index:
            self._index[term].discard(doc_id)
            if not self._index[term]:
                del self._index[term]

    def get_terms(self):
        """获取所有词条"""
        return list(self._index.keys())

    def term_count(self, term):
        """获取某词条的文档数量"""
        return len(self._index.get(term, set()))

    def __len__(self):
        return len(self._index)

    def __contains__(self, term):
        return term in self._index

    def __repr__(self):
        return f"InvertedIndex(terms={len(self._index)})"
