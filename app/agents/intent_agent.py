"""意图识别 Agent（已废弃 — 由 orchestrator Tool-Calling 取代）

使用 LLM 对用户输入进行意图分类，支持以下类别：
- search_book: 馆藏检索
- recommend_book: 图书推荐
- book_seat: 预约座位
- query_appointment: 查询预约
- cancel_appointment: 取消预约
- policy_query: 政策/规则咨询
- profile_query: 读者画像/借阅记录
- greeting: 问候
- other: 其他
"""
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from app.config import settings

INTENT_CATEGORIES = [
    "search_book", "recommend_book", "book_seat",
    "query_appointment", "cancel_appointment",
    "policy_query", "profile_query", "greeting", "other",
]

PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        "你是一个图书馆智能助手的意图分类器。"
        "请将用户输入分类到以下类别之一：{categories}。"
        "仅返回类别名称，不要返回其他内容。\n"
        "类别说明：\n"
        "- search_book: 搜索、查询、查找图书\n"
        "- recommend_book: 推荐图书、想看书但不知道看什么\n"
        "- book_seat: 预约座位、查看座位\n"
        "- query_appointment: 查询我的预约、查看预约记录\n"
        "- cancel_appointment: 取消预约、删除预约\n"
        "- policy_query: 图书馆规则、开放时间、借阅规则\n"
        "- profile_query: 我的借阅记录、读者画像\n"
        "- greeting: 问候、打招呼、你好\n"
        "- other: 其他不在上述类别的内容",
    ),
    ("user", "{input}"),
])


class IntentAgent:
    """意图识别"""

    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.LLM_MODEL or "qwen-plus",
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL,
            temperature=0,
        )
        self.chain = PROMPT | self.llm

    async def classify(self, user_input: str) -> dict:
        """分类用户意图"""
        categories_str = ", ".join(INTENT_CATEGORIES)
        result = await self.chain.ainvoke({
            "input": user_input,
            "categories": categories_str,
        })
        intent = result.content.strip().lower()
        if intent not in INTENT_CATEGORIES:
            intent = "other"
        return {"intent": intent, "raw_input": user_input}
