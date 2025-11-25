"""
RAG 服务 - 检索增强生成
"""
import os
from typing import List, Dict, Optional, Generator
import time

from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from utils.config import config
from utils.prompts import RAG_TEMPLATE, DIRECT_ANSWER_TEMPLATE
from .vector_store_service import get_vector_store_service


class RAGService:
    """RAG 问答服务"""
    
    def __init__(self):
        self.vector_service = get_vector_store_service()
        self.llm = self._init_llm()
        self.prompt = ChatPromptTemplate.from_template(RAG_TEMPLATE)
        self.direct_prompt = ChatPromptTemplate.from_template(DIRECT_ANSWER_TEMPLATE)
    
    def _init_llm(self):
        """初始化 LLM"""
        # 设置环境变量
        os.environ["ANTHROPIC_API_KEY"] = config.ANTHROPIC_API_KEY
        os.environ["ANTHROPIC_BASE_URL"] = config.ANTHROPIC_BASE_URL
        
        llm = ChatAnthropic(
            model=config.LLM_MODEL,
            temperature=config.LLM_TEMPERATURE,
            max_tokens=config.LLM_MAX_TOKENS
        )
        return llm
    
    def query(self, user_id: int, question: str, k: int = None) -> Dict:
        """
        执行 RAG 查询
        
        Args:
            user_id: 用户 ID
            question: 用户问题
            k: 检索数量
        
        Returns:
            查询结果字典：
            {
                'answer': str,
                'retrieved_docs': List[Dict],
                'thinking_process': List[Dict],
                'elapsed_time': float,
                'tokens_used': int
            }
        """
        start_time = time.time()
        
        # 1. 向量检索
        thinking_process = []
        thinking_process.append({
            'step': 1,
            'action': '分析问题',
            'description': f'识别问题类型并提取关键词',
            'details': f'问题长度: {len(question)} 字符'
        })
        
        docs_with_scores = self.vector_service.search_with_score(user_id, question, k=k)
        
        # 判断是否需要降级到直接回答
        should_fallback = False
        fallback_reason = ""
        
        if not docs_with_scores:
            # 情况 A：没有检索到文档
            should_fallback = True
            fallback_reason = "未找到相关文档"
        elif config.RAG_FALLBACK_ENABLED:
            # 情况 B：检查相似度阈值
            max_similarity = max([max(0, 1 - score) for _, score in docs_with_scores])
            if max_similarity < config.RAG_SIMILARITY_THRESHOLD:
                should_fallback = True
                fallback_reason = f"相似度太低（最高相似度: {max_similarity:.2f}）"
        
        if should_fallback:
            # 使用直接回答模式
            thinking_process.append({
                'step': 2,
                'action': '降级到直接回答',
                'description': fallback_reason,
                'details': '使用大模型直接回答，不依赖知识库'
            })
            
            thinking_process.append({
                'step': 3,
                'action': '生成答案',
                'description': '使用大模型直接回答',
                'details': '不依赖知识库内容'
            })
            
            # 使用直接回答 Chain
            direct_chain = self.direct_prompt | self.llm | StrOutputParser()
            answer = direct_chain.invoke({"question": question})
            
            elapsed_time = time.time() - start_time
            
            thinking_process.append({
                'step': 4,
                'action': '完成',
                'description': f'回答生成完成',
                'details': f'耗时: {elapsed_time:.2f} 秒'
            })
            
            # 估算 Token 消耗（直接回答没有上下文）
            estimated_tokens = len(question) // 4 + len(answer) // 4
            
            return {
                'answer': answer,
                'retrieved_docs': [],
                'thinking_process': thinking_process,
                'elapsed_time': elapsed_time,
                'tokens_used': estimated_tokens,
                'fallback_mode': True,
                'fallback_reason': fallback_reason
            }
        
        # 2. 处理检索结果（RAG 模式）
        retrieved_docs = []
        context_parts = []
        
        for i, (doc, score) in enumerate(docs_with_scores):
            # 转换评分为相似度（Chroma 使用距离，越小越相似）
            similarity = max(0, 1 - score)  # 简单转换
            
            retrieved_docs.append({
                'chunk_id': i,
                'content': doc.page_content,
                'similarity': round(similarity, 2),
                'metadata': doc.metadata
            })
            
            context_parts.append(f"[文档片段 {i+1}]\n{doc.page_content}")
        
        context = "\n\n".join(context_parts)
        
        avg_similarity = sum([d['similarity'] for d in retrieved_docs]) / len(retrieved_docs)
        thinking_process.append({
            'step': 2,
            'action': '文档检索',
            'description': f'检索到 {len(retrieved_docs)} 个相关段落',
            'details': f'平均相似度: {avg_similarity:.2f}'
        })
        
        # 3. 构造 Prompt 并调用 LLM
        thinking_process.append({
            'step': 3,
            'action': '生成答案',
            'description': '基于检索结果生成回答',
            'details': f'上下文长度: {len(context)} 字符'
        })
        
        # 使用 LangChain RAG Chain
        rag_chain = (
            {"context": lambda x: context, "question": RunnablePassthrough()}
            | self.prompt
            | self.llm
            | StrOutputParser()
        )
        
        answer = rag_chain.invoke(question)
        
        elapsed_time = time.time() - start_time
        
        thinking_process.append({
            'step': 4,
            'action': '完成',
            'description': f'回答生成完成',
            'details': f'耗时: {elapsed_time:.2f} 秒'
        })
        
        # TODO: 计算实际 Token 消耗
        estimated_tokens = len(context) // 4 + len(question) // 4 + len(answer) // 4
        
        return {
            'answer': answer,
            'retrieved_docs': retrieved_docs,
            'thinking_process': thinking_process,
            'elapsed_time': elapsed_time,
            'tokens_used': estimated_tokens,
            'fallback_mode': False
        }
    
    def query_stream(self, user_id: int, question: str, k: int = None) -> Generator[Dict, None, None]:
        """
        流式执行 RAG 查询
        
        Args:
            user_id: 用户 ID
            question: 用户问题
            k: 检索数量
        
        Yields:
            字典，包含不同类型的信息：
            - type='thinking': 思考过程信息
              {
                  'type': 'thinking',
                  'thinking_process': List[Dict]
              }
            - type='chunk': 答案片段
              {
                  'type': 'chunk',
                  'content': str  # 增量内容
              }
            - type='complete': 完成信息（最后一条）
              {
                  'type': 'complete',
                  'answer': str,  # 完整答案
                  'retrieved_docs': List[Dict],
                  'thinking_process': List[Dict],
                  'elapsed_time': float,
                  'tokens_used': int
              }
        """
        start_time = time.time()
        
        # 1. 向量检索
        thinking_process = []
        thinking_process.append({
            'step': 1,
            'action': '分析问题',
            'description': f'识别问题类型并提取关键词',
            'details': f'问题长度: {len(question)} 字符'
        })
        
        docs_with_scores = self.vector_service.search_with_score(user_id, question, k=k)
        
        # 判断是否需要降级到直接回答
        should_fallback = False
        fallback_reason = ""
        
        if not docs_with_scores:
            # 情况 A：没有检索到文档
            should_fallback = True
            fallback_reason = "未找到相关文档"
        elif config.RAG_FALLBACK_ENABLED:
            # 情况 B：检查相似度阈值
            max_similarity = max([max(0, 1 - score) for _, score in docs_with_scores])
            if max_similarity < config.RAG_SIMILARITY_THRESHOLD:
                should_fallback = True
                fallback_reason = f"相似度太低（最高相似度: {max_similarity:.2f}）"
        
        if should_fallback:
            # 使用直接回答模式（流式）
            thinking_process.append({
                'step': 2,
                'action': '降级到直接回答',
                'description': fallback_reason,
                'details': '使用大模型直接回答，不依赖知识库'
            })
            
            thinking_process.append({
                'step': 3,
                'action': '生成答案',
                'description': '使用大模型直接回答',
                'details': '不依赖知识库内容'
            })
            
            # 先 yield 思考过程
            yield {
                'type': 'thinking',
                'thinking_process': thinking_process
            }
            
            # 流式生成直接回答
            direct_chain = self.direct_prompt | self.llm | StrOutputParser()
            full_answer = ""
            for chunk in direct_chain.stream({"question": question}):
                full_answer += chunk
                yield {
                    'type': 'chunk',
                    'content': chunk
                }
            
            elapsed_time = time.time() - start_time
            
            thinking_process.append({
                'step': 4,
                'action': '完成',
                'description': f'回答生成完成',
                'details': f'耗时: {elapsed_time:.2f} 秒'
            })
            
            # 估算 Token 消耗（直接回答没有上下文）
            estimated_tokens = len(question) // 4 + len(full_answer) // 4
            
            # 最后 yield 完整结果
            yield {
                'type': 'complete',
                'answer': full_answer,
                'retrieved_docs': [],
                'thinking_process': thinking_process,
                'elapsed_time': elapsed_time,
                'tokens_used': estimated_tokens,
                'fallback_mode': True,
                'fallback_reason': fallback_reason
            }
            return
        
        # 2. 处理检索结果（RAG 模式）
        retrieved_docs = []
        context_parts = []
        
        for i, (doc, score) in enumerate(docs_with_scores):
            # 转换评分为相似度（Chroma 使用距离，越小越相似）
            similarity = max(0, 1 - score)  # 简单转换
            
            retrieved_docs.append({
                'chunk_id': i,
                'content': doc.page_content,
                'similarity': round(similarity, 2),
                'metadata': doc.metadata
            })
            
            context_parts.append(f"[文档片段 {i+1}]\n{doc.page_content}")
        
        context = "\n\n".join(context_parts)
        
        avg_similarity = sum([d['similarity'] for d in retrieved_docs]) / len(retrieved_docs)
        thinking_process.append({
            'step': 2,
            'action': '文档检索',
            'description': f'检索到 {len(retrieved_docs)} 个相关段落',
            'details': f'平均相似度: {avg_similarity:.2f}'
        })
        
        # 3. 构造 Prompt 并调用 LLM（流式）
        thinking_process.append({
            'step': 3,
            'action': '生成答案',
            'description': '基于检索结果生成回答',
            'details': f'上下文长度: {len(context)} 字符'
        })
        
        # 先 yield 思考过程
        yield {
            'type': 'thinking',
            'thinking_process': thinking_process
        }
        
        # 使用 LangChain RAG Chain（流式）
        rag_chain = (
            {"context": lambda x: context, "question": RunnablePassthrough()}
            | self.prompt
            | self.llm
            | StrOutputParser()
        )
        
        # 流式生成答案
        full_answer = ""
        for chunk in rag_chain.stream(question):
            full_answer += chunk
            yield {
                'type': 'chunk',
                'content': chunk
            }
        
        elapsed_time = time.time() - start_time
        
        thinking_process.append({
            'step': 4,
            'action': '完成',
            'description': f'回答生成完成',
            'details': f'耗时: {elapsed_time:.2f} 秒'
        })
        
        # TODO: 计算实际 Token 消耗
        estimated_tokens = len(context) // 4 + len(question) // 4 + len(full_answer) // 4
        
        # 最后 yield 完整结果
        yield {
            'type': 'complete',
            'answer': full_answer,
            'retrieved_docs': retrieved_docs,
            'thinking_process': thinking_process,
            'elapsed_time': elapsed_time,
            'tokens_used': estimated_tokens,
            'fallback_mode': False
        }
    
    def format_docs(self, docs) -> str:
        """格式化文档列表为字符串"""
        return "\n\n".join(doc.page_content for doc in docs)


# 全局 RAG 服务实例
_rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    """获取全局 RAG 服务实例（单例）"""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service

