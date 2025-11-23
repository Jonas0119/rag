"""
向量库服务 - Chroma 向量库管理
"""
import os
from typing import List, Optional
from pathlib import Path
import threading
import logging

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

from utils.config import config

logger = logging.getLogger(__name__)


class VectorStoreService:
    """向量库服务 - 每用户独立 Collection"""
    
    def __init__(self):
        # 异步加载 Embedding 模型（不阻塞初始化）
        self.embeddings: Optional[HuggingFaceEmbeddings] = None
        self._embeddings_loading = False
        self._embeddings_loaded = False
        self._embeddings_lock = threading.Lock()
        self._cache = {}  # 缓存向量库实例
        
        # 在后台线程中启动模型加载
        self._start_loading_embeddings()
    
    def _start_loading_embeddings(self):
        """在后台线程中启动模型加载"""
        if self._embeddings_loading or self._embeddings_loaded:
            return
        
        self._embeddings_loading = True
        thread = threading.Thread(
            target=self._load_embeddings_async,
            daemon=True,
            name="EmbeddingModelLoader"
        )
        thread.start()
        logger.info(f"[向量库服务] 已在后台启动 Embedding 模型加载: {config.EMBEDDING_MODEL}")
    
    def _load_embeddings_async(self):
        """异步加载 Embedding 模型（在后台线程中执行）"""
        try:
            logger.info(f"[向量库服务] 开始加载 Embedding 模型: {config.EMBEDDING_MODEL}")
            # 解决 HuggingFace tokenizers 的 fork 警告
            os.environ["TOKENIZERS_PARALLELISM"] = "false"
            
            embeddings = HuggingFaceEmbeddings(
                model_name=config.EMBEDDING_MODEL,
                model_kwargs={'device': config.EMBEDDING_DEVICE},
                encode_kwargs={'normalize_embeddings': config.NORMALIZE_EMBEDDINGS}
            )
            
            with self._embeddings_lock:
                self.embeddings = embeddings
                self._embeddings_loaded = True
                self._embeddings_loading = False
            
            logger.info(f"[向量库服务] Embedding 模型加载完成: {config.EMBEDDING_MODEL}")
        except Exception as e:
            logger.error(f"[向量库服务] Embedding 模型加载失败: {str(e)}", exc_info=True)
            with self._embeddings_lock:
                self._embeddings_loading = False
    
    def _ensure_embeddings_loaded(self, timeout: float = 300.0):
        """
        确保 Embedding 模型已加载（如果正在加载则等待）
        
        Args:
            timeout: 最大等待时间（秒），默认 5 分钟
        
        Returns:
            bool: 模型是否已加载
        """
        if self._embeddings_loaded and self.embeddings is not None:
            return True
        
        # 如果还没开始加载，启动加载
        if not self._embeddings_loading:
            self._start_loading_embeddings()
        
        # 等待模型加载完成
        import time
        start_time = time.time()
        while not self._embeddings_loaded:
            if time.time() - start_time > timeout:
                logger.error(f"[向量库服务] 等待 Embedding 模型加载超时（{timeout}秒）")
                return False
            time.sleep(0.1)  # 等待 100ms 后重试
        
        return self.embeddings is not None
    
    def is_embeddings_ready(self) -> bool:
        """检查 Embedding 模型是否已加载完成"""
        return self._embeddings_loaded and self.embeddings is not None
    
    def get_embeddings_loading_status(self) -> dict:
        """
        获取 Embedding 模型加载状态
        
        Returns:
            dict: 包含加载状态的字典
        """
        return {
            'loaded': self._embeddings_loaded,
            'loading': self._embeddings_loading,
            'ready': self.is_embeddings_ready(),
            'model_name': config.EMBEDDING_MODEL
        }
    
    def get_collection_name(self, user_id: int) -> str:
        """获取用户的 Collection 名称"""
        return f"user_{user_id}_docs"
    
    def get_persist_directory(self, user_id: int) -> str:
        """获取用户的向量库存储目录"""
        return f"{config.CHROMA_DB_DIR}/user_{user_id}_collection"
    
    def get_vector_store(self, user_id: int) -> Chroma:
        """
        获取用户的向量库实例（带缓存）
        
        Args:
            user_id: 用户 ID
        
        Returns:
            Chroma 向量库实例
        
        Raises:
            RuntimeError: 如果 Embedding 模型未加载完成
        """
        # 确保 Embedding 模型已加载
        if not self._ensure_embeddings_loaded():
            raise RuntimeError(f"Embedding 模型加载失败或超时: {config.EMBEDDING_MODEL}")
        
        # 从缓存获取
        if user_id in self._cache:
            return self._cache[user_id]
        
        # 创建新实例
        collection_name = self.get_collection_name(user_id)
        persist_directory = self.get_persist_directory(user_id)
        
        # 确保目录存在
        Path(persist_directory).mkdir(parents=True, exist_ok=True)
        
        vectorstore = Chroma(
            collection_name=collection_name,
            embedding_function=self.embeddings,
            persist_directory=persist_directory
        )
        
        # 缓存实例
        self._cache[user_id] = vectorstore
        
        return vectorstore
    
    def add_documents(self, user_id: int, documents: List[Document]) -> List[str]:
        """
        添加文档到向量库
        
        Args:
            user_id: 用户 ID
            documents: 文档列表
        
        Returns:
            文档 ID 列表
        """
        vectorstore = self.get_vector_store(user_id)
        ids = vectorstore.add_documents(documents)
        return ids
    
    def delete_documents(self, user_id: int, doc_id: str):
        """
        删除文档的所有向量
        
        Args:
            user_id: 用户 ID
            doc_id: 文档 ID
        """
        vectorstore = self.get_vector_store(user_id)
        
        # 通过 metadata 过滤删除
        # 注意：Chroma 的删除需要指定 ID 或 where 条件
        try:
            # 查询所有包含该 doc_id 的向量
            results = vectorstore.get(where={"doc_id": doc_id})
            if results and results['ids']:
                vectorstore.delete(ids=results['ids'])
        except Exception as e:
            print(f"删除向量失败: {e}")
    
    def search_similar(self, user_id: int, query: str, k: int = None) -> List[Document]:
        """
        相似度搜索
        
        Args:
            user_id: 用户 ID
            query: 查询文本
            k: 返回数量
        
        Returns:
            相关文档列表
        """
        if k is None:
            k = config.RETRIEVAL_K
        
        vectorstore = self.get_vector_store(user_id)
        docs = vectorstore.similarity_search(query, k=k)
        return docs
    
    def search_with_score(self, user_id: int, query: str, k: int = None) -> List[tuple]:
        """
        相似度搜索（带评分）
        
        Args:
            user_id: 用户 ID
            query: 查询文本
            k: 返回数量
        
        Returns:
            (文档, 评分) 元组列表
        """
        if k is None:
            k = config.RETRIEVAL_K
        
        vectorstore = self.get_vector_store(user_id)
        docs_with_scores = vectorstore.similarity_search_with_score(query, k=k)
        return docs_with_scores
    
    def get_retriever(self, user_id: int, k: int = None):
        """
        获取检索器
        
        Args:
            user_id: 用户 ID
            k: 返回数量
        
        Returns:
            Retriever 对象
        """
        if k is None:
            k = config.RETRIEVAL_K
        
        vectorstore = self.get_vector_store(user_id)
        retriever = vectorstore.as_retriever(
            search_type=config.RETRIEVAL_SEARCH_TYPE,
            search_kwargs={"k": k}
        )
        return retriever
    
    def get_document_count(self, user_id: int) -> int:
        """获取用户向量库中的文档数量"""
        try:
            vectorstore = self.get_vector_store(user_id)
            # Chroma 的 count 方法
            return vectorstore._collection.count()
        except Exception:
            return 0
    
    def clear_cache(self, user_id: Optional[int] = None):
        """清除缓存"""
        if user_id:
            if user_id in self._cache:
                del self._cache[user_id]
        else:
            self._cache.clear()


# 全局向量库服务实例
_vector_store_service: Optional[VectorStoreService] = None


def get_vector_store_service() -> VectorStoreService:
    """获取全局向量库服务实例（单例）"""
    global _vector_store_service
    if _vector_store_service is None:
        _vector_store_service = VectorStoreService()
    return _vector_store_service

