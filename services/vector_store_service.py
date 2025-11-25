"""
向量库服务 - 支持 Chroma 和 Pinecone
"""
import os
from typing import List, Optional, Union
from pathlib import Path
import threading
import logging

from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings

from utils.config import config
from utils.performance_monitor import monitor_vector_db
import streamlit as st
from .vector_strategies import VectorStoreStrategy, ChromaStrategy, PineconeStrategy

logger = logging.getLogger(__name__)


class VectorStoreService:
    """向量库服务 - 每用户独立 Collection"""
    
    def __init__(self):
        # 异步加载 Embedding 模型（不阻塞初始化）
        self.embeddings: Optional[HuggingFaceEmbeddings] = None
        self.strategy: Optional[VectorStoreStrategy] = None
        self._embeddings_loading = False
        self._embeddings_loaded = False
        self._embeddings_lock = threading.Lock()
        
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
                # 初始化策略
                if config.VECTOR_DB_MODE == "cloud":
                    self.strategy = PineconeStrategy(embeddings)
                else:
                    self.strategy = ChromaStrategy(embeddings)
                
                self._embeddings_loaded = True
                self._embeddings_loading = False
            
            logger.info(f"[向量库服务] Embedding 模型加载完成: {config.EMBEDDING_MODEL}, 策略: {type(self.strategy).__name__}")
        except Exception as e:
            logger.error(f"[向量库服务] Embedding 模型加载失败: {str(e)}", exc_info=True)
            with self._embeddings_lock:
                self._embeddings_loading = False
    
    def _ensure_embeddings_loaded(self, timeout: float = 300.0):
        """确保 Embedding 模型已加载"""
        if self._embeddings_loaded and self.embeddings is not None:
            return True
        
        if not self._embeddings_loading:
            self._start_loading_embeddings()
        
        import time
        start_time = time.time()
        while not self._embeddings_loaded:
            if time.time() - start_time > timeout:
                logger.error(f"[向量库服务] 等待 Embedding 模型加载超时（{timeout}秒）")
                return False
            time.sleep(0.1)
        
        return self.embeddings is not None
    
    def is_embeddings_ready(self) -> bool:
        """检查 Embedding 模型是否已加载完成"""
        return self._embeddings_loaded and self.embeddings is not None
    
    def get_embeddings_loading_status(self) -> dict:
        """获取 Embedding 模型加载状态"""
        return {
            'loaded': self._embeddings_loaded,
            'loading': self._embeddings_loading,
            'ready': self.is_embeddings_ready(),
            'model_name': config.EMBEDDING_MODEL
        }
    
    def _get_strategy(self) -> VectorStoreStrategy:
        """获取当前策略（确保已初始化）"""
        if not self._ensure_embeddings_loaded():
            raise RuntimeError(f"Embedding 模型加载失败或超时: {config.EMBEDDING_MODEL}")
        return self.strategy
    
    def add_documents(self, user_id: int, documents: List[Document]) -> List[str]:
        """添加文档到向量库"""
        doc_count = len(documents)
        details = f"user_id={user_id}, doc_count={doc_count}"
        
        with monitor_vector_db("add_documents", details):
            return self._get_strategy().add_documents(user_id, documents)
    
    def delete_documents(self, user_id: int, doc_id: str):
        """删除文档的所有向量"""
        details = f"user_id={user_id}, doc_id={doc_id}"
        
        with monitor_vector_db("delete_documents", details):
            self._get_strategy().delete_documents(user_id, doc_id)
    
    def search_similar(self, user_id: int, query: str, k: int = None) -> List[Document]:
        """相似度搜索"""
        if k is None:
            k = config.RETRIEVAL_K
        
        query_len = len(query)
        details = f"user_id={user_id}, k={k}, query_len={query_len}"
        
        with monitor_vector_db("search_similar", details):
            return self._get_strategy().search(user_id, query, k)
    
    def search_with_score(self, user_id: int, query: str, k: int = None) -> List[tuple]:
        """相似度搜索（带评分）"""
        if k is None:
            k = config.RETRIEVAL_K
        
        query_len = len(query)
        details = f"user_id={user_id}, k={k}, query_len={query_len}"
        
        with monitor_vector_db("search_with_score", details):
            return self._get_strategy().search_with_score(user_id, query, k)
    
    def get_retriever(self, user_id: int, k: int = None):
        """获取检索器"""
        if k is None:
            k = config.RETRIEVAL_K
        
        vectorstore = self._get_strategy().get_vector_store(user_id)
        
        # 针对不同策略的特殊处理（如 Pinecone 需要 filter）
        # 这里为了保持通用性，我们尽量使用 vectorstore 的标准接口
        # 但 PineconeVectorStore.as_retriever 需要 filter 参数在 search_kwargs 中
        
        search_kwargs = {"k": k}
        if config.VECTOR_DB_MODE == "cloud":
             search_kwargs["filter"] = {"user_id": user_id}
        
        return vectorstore.as_retriever(
            search_type=config.RETRIEVAL_SEARCH_TYPE,
            search_kwargs=search_kwargs
        )
    
    def get_document_count(self, user_id: int) -> int:
        """获取用户向量库中的文档数量"""
        with monitor_vector_db("get_document_count", f"user_id={user_id}"):
            # 尝试使用策略获取，如果失败（如模型未加载），返回 0
            try:
                if self.is_embeddings_ready():
                    return self.strategy.get_document_count(user_id)
                else:
                    # 如果模型未加载，尝试直接从数据库获取（作为 fallback）
                    from database import DocumentDAO
                    doc_dao = DocumentDAO()
                    return doc_dao.get_total_chunk_count(user_id, status='active')
            except Exception:
                return 0

@st.cache_resource
def get_vector_store_service() -> VectorStoreService:
    """获取全局向量库服务实例（Streamlit缓存，确保模型只加载一次）"""
    logger.info("[向量库服务] 创建新的VectorStoreService实例")
    return VectorStoreService()

