"""
向量库服务 - 支持 Chroma 和 Pinecone
"""
import os
from typing import List, Optional, Union
from pathlib import Path
import threading
import logging

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

from utils.config import config
from utils.performance_monitor import monitor_vector_db

logger = logging.getLogger(__name__)

# Pinecone 相关导入（可选）
try:
    from pinecone import Pinecone, ServerlessSpec
    from langchain_pinecone import PineconeVectorStore
    PINECONE_AVAILABLE = True
except ImportError:
    PINECONE_AVAILABLE = False


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
    
    def get_vector_store(self, user_id: int) -> Union[Chroma, 'PineconeVectorStore']:
        """
        获取用户的向量库实例（带缓存）
        
        Args:
            user_id: 用户 ID
        
        Returns:
            Chroma 或 PineconeVectorStore 向量库实例
        
        Raises:
            RuntimeError: 如果 Embedding 模型未加载完成
        """
        # 确保 Embedding 模型已加载
        if not self._ensure_embeddings_loaded():
            raise RuntimeError(f"Embedding 模型加载失败或超时: {config.EMBEDDING_MODEL}")
        
        # 根据模式选择向量库
        if config.VECTOR_DB_MODE == "cloud":
            # 使用 Pinecone
            return self._get_pinecone_vector_store()
        else:
            # 使用 Chroma（原有逻辑）
            return self._get_chroma_vector_store(user_id)
    
    def _get_chroma_vector_store(self, user_id: int) -> Chroma:
        """获取 Chroma 向量库实例"""
        # 从缓存获取
        cache_key = f"chroma_{user_id}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
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
        self._cache[cache_key] = vectorstore
        
        return vectorstore
    
    def _get_pinecone_vector_store(self) -> 'PineconeVectorStore':
        """获取 Pinecone 向量库实例（单 Index，所有用户共享）"""
        # 检查 Pinecone 是否可用
        if not PINECONE_AVAILABLE:
            raise ImportError("使用 Pinecone 需要安装: pip install pinecone-client langchain-pinecone")
        
        # 检查配置
        if not config.PINECONE_API_KEY:
            raise ValueError("VECTOR_DB_MODE=cloud 时，必须配置 PINECONE_API_KEY")
        
        # 从缓存获取（Pinecone 是全局单例）
        cache_key = "pinecone_global"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # 初始化 Pinecone 客户端
        pc = Pinecone(api_key=config.PINECONE_API_KEY)
        
        # 检查 Index 是否存在
        index_name = config.PINECONE_INDEX_NAME
        # Pinecone 6.x API: list_indexes() 返回 IndexList 对象
        try:
            index_list = pc.list_indexes()
            # 检查返回类型并提取名称
            if hasattr(index_list, 'names'):
                existing_indexes = index_list.names()
            elif hasattr(index_list, '__iter__'):
                # 如果是可迭代对象，尝试提取名称
                existing_indexes = [idx.name if hasattr(idx, 'name') else str(idx) for idx in index_list]
            else:
                existing_indexes = []
        except Exception as e:
            logger.warning(f"[向量库服务] 获取 Index 列表失败: {str(e)}")
            existing_indexes = []
        
        if index_name not in existing_indexes:
            # 创建 Index（如果不存在）
            logger.warning(f"[向量库服务] Pinecone Index '{index_name}' 不存在，尝试创建...")
            try:
                pc.create_index(
                    name=index_name,
                    dimension=1024,  # BGE-large-zh-v1.5 的维度
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",  # 默认 AWS，可以从环境变量读取
                        region=config.PINECONE_ENVIRONMENT or "us-east-1"
                    )
                )
                logger.info(f"[向量库服务] Pinecone Index '{index_name}' 创建成功")
            except Exception as e:
                logger.error(f"[向量库服务] 创建 Pinecone Index 失败: {str(e)}")
                raise
        
        # 创建 PineconeVectorStore
        vectorstore = PineconeVectorStore(
            index_name=index_name,
            embedding=self.embeddings
        )
        
        # 缓存实例
        self._cache[cache_key] = vectorstore
        
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
        doc_count = len(documents)
        details = f"user_id={user_id}, doc_count={doc_count}"
        
        with monitor_vector_db("add_documents", details):
            # 关键：Pinecone 模式下，必须为每个文档添加 user_id 到 metadata
            if config.VECTOR_DB_MODE == "cloud":
                for doc in documents:
                    if "user_id" not in doc.metadata:
                        doc.metadata["user_id"] = user_id
            
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
        details = f"user_id={user_id}, doc_id={doc_id}"
        
        with monitor_vector_db("delete_documents", details):
            vectorstore = self.get_vector_store(user_id)
            
            try:
                if config.VECTOR_DB_MODE == "cloud":
                    # Pinecone: 使用 metadata 过滤删除
                    # 关键：必须同时过滤 user_id 和 doc_id
                    # PineconeVectorStore.delete() 支持 filter 参数
                    vectorstore.delete(
                        filter={"user_id": user_id, "doc_id": doc_id}
                    )
                else:
                    # Chroma: 通过 metadata 过滤删除
                    results = vectorstore.get(where={"doc_id": doc_id})
                    if results and results['ids']:
                        vectorstore.delete(ids=results['ids'])
            except Exception as e:
                logger.error(f"[向量库服务] 删除向量失败: {str(e)}")
                raise
    
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
        
        query_len = len(query)
        details = f"user_id={user_id}, k={k}, query_len={query_len}"
        
        with monitor_vector_db("search_similar", details):
            vectorstore = self.get_vector_store(user_id)
            
            # 关键：Pinecone 模式下，必须使用 metadata 过滤
            if config.VECTOR_DB_MODE == "cloud":
                docs = vectorstore.similarity_search(
                    query,
                    k=k,
                    filter={"user_id": user_id}  # 必须加 filter！
                )
            else:
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
        
        query_len = len(query)
        details = f"user_id={user_id}, k={k}, query_len={query_len}"
        
        with monitor_vector_db("search_with_score", details):
            vectorstore = self.get_vector_store(user_id)
            
            # 关键：Pinecone 模式下，必须使用 metadata 过滤
            if config.VECTOR_DB_MODE == "cloud":
                docs_with_scores = vectorstore.similarity_search_with_score(
                    query,
                    k=k,
                    filter={"user_id": user_id}  # 必须加 filter！
                )
            else:
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
        
        # 关键：Pinecone 模式下，必须在 search_kwargs 中添加 filter
        if config.VECTOR_DB_MODE == "cloud":
            retriever = vectorstore.as_retriever(
                search_type=config.RETRIEVAL_SEARCH_TYPE,
                search_kwargs={
                    "k": k,
                    "filter": {"user_id": user_id}  # 必须加 filter！
                }
            )
        else:
            retriever = vectorstore.as_retriever(
                search_type=config.RETRIEVAL_SEARCH_TYPE,
                search_kwargs={"k": k}
            )
        
        return retriever
    
    def get_document_count(self, user_id: int) -> int:
        """获取用户向量库中的文档数量"""
        with monitor_vector_db("get_document_count", f"user_id={user_id}"):
            try:
                vectorstore = self.get_vector_store(user_id)
                
                if config.VECTOR_DB_MODE == "cloud":
                    # Pinecone: 通过 metadata 过滤统计向量数量
                    # 注意：Pinecone 没有直接按 metadata 统计的 API
                    # 方法：使用 query 方法，设置一个大的 top_k 来获取所有匹配的向量
                    try:
                        from pinecone import Pinecone
                        pc = Pinecone(api_key=config.PINECONE_API_KEY)
                        index = pc.Index(config.PINECONE_INDEX_NAME)
                        
                        # 使用零向量作为查询向量（不会影响过滤结果，只是用于触发查询）
                        # 设置一个很大的 top_k 来获取所有匹配的向量
                        query_vector = [0.0] * 1024  # BGE-large-zh-v1.5 的维度
                        
                        # Pinecone 的 top_k 最大值为 10000
                        # 如果用户的向量数量可能超过 10000，需要分页查询
                        max_top_k = 10000
                        
                        results = index.query(
                            vector=query_vector,
                            top_k=max_top_k,
                            filter={"user_id": user_id},
                            include_metadata=False
                        )
                        
                        # 获取匹配的向量数量
                        if results and 'matches' in results:
                            matches = results['matches']
                            count = len(matches)
                            
                            # 如果返回的数量等于 max_top_k，说明可能还有更多向量
                            # 这种情况下，使用备用方案：从数据库获取
                            if count == max_top_k:
                                logger.warning(f"[向量库服务] 用户 {user_id} 的向量数量可能超过 {max_top_k}，使用数据库统计作为备用方案")
                                # 使用数据库的 chunk_count 作为备用方案
                                try:
                                    from database import DocumentDAO
                                    doc_dao = DocumentDAO()
                                    db_count = doc_dao.get_total_chunk_count(user_id, status='active')
                                    # 返回数据库统计和查询结果中的较大值
                                    return max(count, db_count)
                                except Exception:
                                    return count
                            
                            return count
                        else:
                            # 如果没有匹配结果，返回 0
                            return 0
                            
                    except Exception as e:
                        logger.error(f"[向量库服务] Pinecone 向量统计失败: {str(e)}")
                        # 如果查询失败，尝试从数据库获取（作为备用方案）
                        try:
                            from database import DocumentDAO
                            doc_dao = DocumentDAO()
                            # 从数据库获取该用户的 chunk_count 总和
                            return doc_dao.get_total_chunk_count(user_id, status='active')
                        except Exception:
                            logger.warning(f"[向量库服务] 无法从数据库获取向量数量，返回 0")
                            return 0
                else:
                    # Chroma 的 count 方法
                    return vectorstore._collection.count()
            except Exception:
                return 0
    
    def clear_cache(self, user_id: Optional[int] = None):
        """清除缓存"""
        if user_id:
            # 清除该用户的缓存
            cache_key = f"chroma_{user_id}" if config.VECTOR_DB_MODE == "local" else "pinecone_global"
            if cache_key in self._cache:
                del self._cache[cache_key]
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

