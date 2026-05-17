"""馆藏客服 Agent

处理图书检索和推荐类问题，接入 ChromaDB 混合检索。
"""
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from sqlalchemy.orm import Session

from app.config import settings
from app.retrieval.hybrid_search import HybridSearch

PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        "你是一个图书馆馆藏客服助手。根据检索到的图书信息回答用户问题。\n"
        "要求：\n"
        "1. 回答与图书馆馆藏相关的问题\n"
        "2. 引用检索结果中的书名、作者、位置等信息\n"
        "3. 如果检索结果不足以回答，如实告知用户\n"
        "4. 回答简洁，使用中文\n\n"
        "检索结果：\n{context}",
    ),
    ("user", "{input}"),
])


class ServiceAgent:
    """馆藏客服"""

    def __init__(self, db: Session):
        self.db = db
        self.llm = ChatOpenAI(
            model=settings.LLM_MODEL or "qwen-plus",
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL,
            temperature=0.3,
        )
        self.chain = PROMPT | self.llm
        self.hybrid_search = HybridSearch()

    async def search_books(self, query: str) -> list:
        """检索图书"""
        results = await self.hybrid_search.search(
            query=query,
            collection_name="library_books",
            top_k=10,
        )
        return results

    async def answer(self, user_input: str) -> dict:
        """回答馆藏相关问题"""
        search_results = await self.search_books(user_input)

        if not search_results:
            context = "未找到相关图书信息。"
        else:
            context_lines = []
            for r in search_results:
                meta = r.get("metadata", {})
                title = meta.get("title", "未知")
                author = meta.get("author", "未知")
                location = meta.get("location", "未知")
                context_lines.append(f"- 《{title}》作者：{author} 馆藏位置：{location}")
            context = "\n".join(context_lines)

        result = await self.chain.ainvoke({
            "input": user_input,
            "context": context,
        })

        return {
            "reply": result.content.strip(),
            "books": search_results,
        }

    async def recommend(self, user_input: str) -> dict:
        """图书推荐"""
        return await self.answer(user_input)
