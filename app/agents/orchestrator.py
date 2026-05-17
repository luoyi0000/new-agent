"""Agent 调度器 — Tool-Calling 范式

LLM 自主决定调用哪些工具，执行后生成回复。取代旧的意图分类 + if/else 路由。
"""
import re
from datetime import datetime

from sqlalchemy.orm import Session
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain_openai import ChatOpenAI

from app.config import settings
from app.agents.service_agent import ServiceAgent
from app.services.reservation_service import ReservationService, PolicyService
from app.services.seat_service import SeatService
from app.repositories.seat_repository import SeatRepository
from app.memory import MemoryManager


class AgentOrchestrator:
    """Agent 调度器 — Tool-Calling 范式"""

    # update_memory 的工具 ID，用于在 _execute_tool 中跳过记忆更新（避免递归）
    _MEMORY_TOOL_NAME = "update_memory"

    TOOL_DEFINITIONS = [
        {
            "type": "function",
            "function": {
                "name": "search_books",
                "description": "根据关键词搜索图书馆的藏书信息，如书名、作者、主题等",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "搜索关键词，如书名、作者"},
                    },
                    "required": ["query"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "query_policies",
                "description": "查询图书馆的规则政策，如开馆时间、借阅规则、罚款标准、座位预约规则等",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "keyword": {"type": "string", "description": "查询关键词"},
                    },
                    "required": ["keyword"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "book_seat",
                "description": "预约图书馆座位。需要用户提供座位编号、日期、开始时间和结束时间",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "seat_code": {"type": "string", "description": "座位编号，如 3F-A01"},
                        "date": {"type": "string", "description": "预约日期，格式 YYYY-MM-DD"},
                        "start_time": {"type": "string", "description": "开始时间，格式 HH:MM"},
                        "end_time": {"type": "string", "description": "结束时间，格式 HH:MM"},
                    },
                    "required": ["seat_code", "date", "start_time", "end_time"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "query_appointments",
                "description": "查询当前用户的座位预约记录",
                "parameters": {"type": "object", "properties": {}},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "cancel_appointment",
                "description": "根据预约编号取消指定的预约",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "appointment_id": {"type": "integer", "description": "预约编号"},
                    },
                    "required": ["appointment_id"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "query_available_seats",
                "description": "获取当前实时可用的座位列表。当用户问有哪些座位、可用座位、空座位、哪里能坐、有没有位子时调用。不用于查询预约规则。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "floor": {"type": "string", "description": "楼层，如 3F、4F、5F（可选，不传则查所有楼层）"},
                    },
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "update_memory",
                "description": "记住用户的重要信息，例如偏好的座位楼层、区域、学习时段、感兴趣的图书类型等。当用户明确表达个人喜好或身份信息时调用。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "fact": {"type": "string", "description": "要记住的用户信息"},
                        "memory_type": {
                            "type": "string",
                            "enum": ["preference", "fact"],
                            "description": "preference=偏好, fact=事实",
                        },
                    },
                    "required": ["fact", "memory_type"],
                },
            },
        },
    ]

    SYSTEM_PROMPT_TEMPLATE = (
        "你是图书馆智能助手。\n\n"
        "请使用工具函数来完成用户请求。\n\n"
        "必须调用工具的场景：\n"
        "- 用户问图书/书/书籍/阅读/推荐 → 调用 search_books\n"
        "- 用户问开馆/开放时间/规则/借阅/罚款 → 调用 query_policies\n"
        "- 用户问有哪些座位/可用座位/空座位/哪里能坐 → 调用 query_available_seats\n"
        "- 用户要预约座位 → 调用 book_seat\n"
        "- 用户要查看预约/取消预约 → 调用 query_appointments / cancel_appointment\n\n"
        "需要调用 update_memory 的场景：\n"
        "- 用户表明个人偏好：如喜欢某个楼层（\u201c喜欢3F\u201d）、偏好某类区域（\u201c安静区\u201d）、常用时段\n"
        "- 用户表明身份信息：如是哪个院系（\u201c计算机系\u201d）、身份（\u201c研究生/老师\u201d）、研究方向（\u201c搞AI的\u201d）\n"
        "- 用户提及常借图书类型：如\u201c我喜欢看科幻小说\u201d、\u201c我常借历史类书籍\u201d\n"
        "- 用户明确要求\u201c记住\u201d某事：如\u201c记住我喜欢靠窗的位置\u201d\n"
        "注意：update_memory 只需记录关键信息，不要记录同义反复的对话。\n\n"
        "直接回复的场景：打招呼、闲聊、无关问题。\n\n"
        "重要限制：你的回复中绝对不能出现 <tool_calls>、<invoke>、<parameter> 等 XML 格式内容，"
        "以及类似 function_call、tool_call 标记。只需用自然的中文直接回答用户。"
    )

    def _get_system_prompt(self) -> str:
        """生成包含当前时间的系统提示词"""
        from datetime import datetime
        now = datetime.now()
        today_cn = now.strftime("%Y年%m月%d日")
        weekday_cn = ["一", "二", "三", "四", "五", "六", "日"][now.weekday()]
        date_line = f"⚠️ 重要事实：当前真实的日期是 {today_cn} 星期{weekday_cn}，不要使用你训练数据中的默认日期。\n\n"
        return date_line + self.SYSTEM_PROMPT_TEMPLATE

    def _inject_current_date(self, user_input: str) -> str:
        """将当前日期注入到用户消息，并替换相对日期为实际日期"""
        from datetime import datetime, timedelta
        now = datetime.now()
        today_iso = now.strftime("%Y-%m-%d")
        today_cn = now.strftime("%Y年%m月%d日")
        weekday_cn = ["一", "二", "三", "四", "五", "六", "日"][now.weekday()]
        tomorrow_iso = (now + timedelta(days=1)).strftime("%Y-%m-%d")
        day_after_iso = (now + timedelta(days=2)).strftime("%Y-%m-%d")

        # 将用户消息中的相对日期替换为实际日期，让 LLM 直接看到真实日期
        user_input_replaced = user_input
        user_input_replaced = user_input_replaced.replace('后天', f' {day_after_iso} ')
        user_input_replaced = user_input_replaced.replace('明天', f' {tomorrow_iso} ')
        user_input_replaced = user_input_replaced.replace('今天', f' {today_iso} ')

        # 从替换后的文本中提取 ISO 日期（用于校正 LLM 传错日期）
        dates_found = re.findall(r'\d{4}-\d{2}-\d{2}', user_input_replaced)
        if dates_found:
            self._correct_date = dates_found[-1]
        else:
            self._correct_date = today_iso

        return (
            f"【当前真实日期：{today_cn} 星期{weekday_cn}】\n"
            f"⚠️ 注意：你训练数据中的日期是错误的，请以上面的真实日期为准。\n\n"
            f"用户说：{user_input_replaced}"
        )

    def __init__(self, db: Session):
        self.db = db
        self._correct_date = None  # 由 _inject_current_date 设置，_book_seat 使用
        self.llm = ChatOpenAI(
            model=settings.LLM_MODEL or "deepseek-chat",
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL,
            temperature=0,
        )

    async def process(
        self, user_input: str, user_id: int = None, history: list = None
    ) -> dict:
        """处理用户消息 — Tool-Calling 流程（注入三层记忆上下文）"""
        # 加载记忆上下文（L1 + L2 + L3）
        memory_mgr = MemoryManager(self.db)
        memory_context = await memory_mgr.load_context(user_id, user_input)
        base_prompt = self._get_system_prompt()
        if memory_context:
            base_prompt += (
                f"\n\n## 关于该用户的记忆\n{memory_context}\n\n"
                "注：以上是该用户的历史信息。如果用户在本轮对话中提到了新的偏好"
                "或身份信息，请及时调用 update_memory 记录下来。"
            )

        messages = [SystemMessage(content=base_prompt)]
        # 把当前日期注入到用户消息中（DeepSeek 会忽略系统提示里的日期）
        dated_input = self._inject_current_date(user_input)

        if history:
            for h in history[-5:]:
                if h.get("user"):
                    messages.append(HumanMessage(content=h["user"]))
                if h.get("assistant"):
                    messages.append(AIMessage(content=h["assistant"]))

        messages.append(HumanMessage(content=dated_input))

        llm_with_tools = self.llm.bind_tools(self.TOOL_DEFINITIONS)
        response = await llm_with_tools.ainvoke(messages)

        tool_calls = response.tool_calls or []

        # 兜底：LLM 没调用工具但文本中有伪调用标记
        if not tool_calls:
            parsed = self._extract_fake_tool_call(response.content)
            if parsed:
                result = await self._execute_tool(parsed["name"], parsed["args"], user_id)
                messages.append(HumanMessage(
                    content=f"工具执行结果：{result}，请用中文回复用户。"
                ))
                final = await self.llm.ainvoke(messages)
                result = self._build_response(final.content, [{"name": parsed["name"]}])
                # 更新记忆（仅在非 update_memory 工具调用时）
                if parsed["name"] != self._MEMORY_TOOL_NAME:
                    await memory_mgr.update(user_id, user_input, result["reply"],
                                            result["intent"], tool_calls=[{"name": parsed["name"]}])
                return result

        if tool_calls:
            messages.append(response)
            for tc in tool_calls:
                result = await self._execute_tool(
                    tc["name"], tc.get("args", {}), user_id
                )
                if tc.get("id"):
                    messages.append(
                        ToolMessage(content=result, tool_call_id=tc["id"])
                    )

            final = await self.llm.ainvoke(messages)
            result = self._build_response(final.content, response.tool_calls)

            # 更新记忆（跳过 update_memory 工具避免递归）
            tool_names = [tc.get("name", "") for tc in tool_calls]
            if self._MEMORY_TOOL_NAME not in tool_names:
                await memory_mgr.update(user_id, user_input, result["reply"],
                                        result["intent"], tool_calls=tool_calls)
            return result

        result = self._build_response(response.content, [])
        await memory_mgr.update(user_id, user_input, result["reply"],
                                result["intent"])
        return result

    async def process_stream(
        self, user_input: str, user_id: int = None, history: list = None
    ):
        """流式处理用户消息 — 逐步 yield token（注入三层记忆上下文）"""
        memory_mgr = MemoryManager(self.db)
        memory_context = await memory_mgr.load_context(user_id, user_input)
        base_prompt = self._get_system_prompt()
        if memory_context:
            base_prompt += (
                f"\n\n## 关于该用户的记忆\n{memory_context}\n\n"
                "注：以上是该用户的历史信息。如果用户在本轮对话中提到了新的偏好"
                "或身份信息，请及时调用 update_memory 记录下来。"
            )

        messages = [SystemMessage(content=base_prompt)]
        dated_input = self._inject_current_date(user_input)

        if history:
            for h in history[-5:]:
                if h.get("user"):
                    messages.append(HumanMessage(content=h["user"]))
                if h.get("assistant"):
                    messages.append(AIMessage(content=h["assistant"]))

        messages.append(HumanMessage(content=dated_input))

        llm_with_tools = self.llm.bind_tools(self.TOOL_DEFINITIONS)
        response = await llm_with_tools.ainvoke(messages)

        tool_calls = response.tool_calls or []
        fake_parsed = None

        # 兜底：LLM 没调用工具但文本中有伪调用标记
        if not tool_calls:
            fake_parsed = self._extract_fake_tool_call(response.content)

        if fake_parsed:
            result = await self._execute_tool(fake_parsed["name"], fake_parsed["args"], user_id)
            tool_calls = [{"name": fake_parsed["name"]}]
            messages.append(HumanMessage(
                content=f"工具执行结果：{result}，请用中文回复用户。"
            ))
            full_content = ""
            async for chunk in self.llm.astream(messages):
                if chunk.content:
                    clean = self._strip_xml(chunk.content)
                    full_content += clean
                    if clean:
                        yield {"type": "token", "content": clean}
            yield {"type": "done", "content": full_content, "tool_calls": tool_calls}
            # 流式完成后更新记忆
            if fake_parsed and fake_parsed["name"] != self._MEMORY_TOOL_NAME:
                await memory_mgr.update(user_id, user_input, full_content,
                                        "other", tool_calls=[{"name": fake_parsed["name"]}])
            return

        if tool_calls:
            messages.append(response)
            for tc in tool_calls:
                result = await self._execute_tool(
                    tc["name"], tc.get("args", {}), user_id
                )
                if tc.get("id"):
                    messages.append(
                        ToolMessage(content=result, tool_call_id=tc["id"])
                    )

        full_content = ""
        async for chunk in self.llm.astream(messages):
            if chunk.content:
                clean = self._strip_xml(chunk.content)
                full_content += clean
                if clean:
                    yield {"type": "token", "content": clean}

        yield {"type": "done", "content": full_content, "tool_calls": tool_calls}
        # 流式完成后更新记忆
        tool_names = [tc.get("name", "") for tc in tool_calls]
        if self._MEMORY_TOOL_NAME not in tool_names:
            await memory_mgr.update(user_id, user_input, full_content,
                                    "other", tool_calls=tool_calls)

    def _extract_fake_tool_call(self, text: str):
        """从 LLM 文本回复中提取伪工具调用（DeepSeek 可能输出 DSML/XML 格式的工具标记）"""
        # 匹配 <invoke name="tool_name">...</invoke> 或 <||DSML||invoke name="tool_name">...</||DSML||invoke>
        patterns = [
            r'<invoke\s+name="(\w+)"[^>]*>(.*?)</invoke>',
            r'<\|\|DSML\|\|invoke\s+name="(\w+)"[^>]*>(.*?)</\|\|DSML\|\|invoke>',
        ]
        param_patterns = [
            r'<parameter\s+name="(\w+)"[^>]*>(.*?)</parameter>',
            r'<\|\|DSML\|\|parameter\s+name="(\w+)"[^>]*>(.*?)</\|\|DSML\|\|parameter>',
        ]

        for ip in patterns:
            m = re.search(ip, text, re.DOTALL)
            if not m:
                continue
            name = m.group(1)
            body = m.group(2)
            params = {}
            for pp in param_patterns:
                for pm in re.finditer(pp, body, re.DOTALL):
                    val = pm.group(2).strip()
                    try:
                        if val.isdigit():
                            val = int(val)
                    except (ValueError, AttributeError):
                        pass
                    params[pm.group(1)] = val
            if name in ("search_books", "query_policies", "query_available_seats",
                        "book_seat", "query_appointments", "cancel_appointment",
                        "update_memory"):
                return {"name": name, "args": params}
        return None

    def _strip_xml(self, text: str) -> str:
        """去除回复中残留的 XML / DSML 工具标记"""
        # DeepSeek DSML 格式：<||DSML||invoke ...> ... </||DSML||invoke>
        text = re.sub(r'<\|\|DSML\|\|invoke[^>]*>.*?</\|\|DSML\|\|invoke>', '', text, flags=re.DOTALL)
        text = re.sub(r'<\|\|DSML\|\|parameter[^>]*>.*?</\|\|DSML\|\|parameter>', '', text, flags=re.DOTALL)
        text = re.sub(r'<\|\|DSML\|\|tool_calls>\s*', '', text)
        text = re.sub(r'\s*</\|\|DSML\|\|tool_calls>', '', text)
        # 普通 XML 格式
        text = re.sub(r'<invoke[^>]*>.*?</invoke>', '', text, flags=re.DOTALL)
        text = re.sub(r'<parameter[^>]*>.*?</parameter>', '', text, flags=re.DOTALL)
        text = re.sub(r'<tool_calls>\s*', '', text)
        text = re.sub(r'\s*</tool_calls>', '', text)
        # 删除可能残留的空行
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    async def _execute_tool(self, tool_name: str, args: dict, user_id: int) -> str:
        """执行工具调用"""
        try:
            result = None
            if tool_name == "search_books":
                result = await self._search_books(args.get("query", ""))
            elif tool_name == "query_policies":
                result = self._query_policies(args.get("keyword", ""))
            elif tool_name == "book_seat":
                # 兜底：强制用 _correct_date 覆盖 LLM 传错的日期
                if self._correct_date and args.get("date"):
                    args["date"] = self._correct_date
                result = await self._book_seat(args, user_id)
            elif tool_name == "query_appointments":
                result = self._query_appointments(user_id)
            elif tool_name == "cancel_appointment":
                result = self._cancel_appointment(
                    args.get("appointment_id"), user_id
                )
            elif tool_name == "query_available_seats":
                result = self._query_available_seats(args.get("floor"))
            elif tool_name == "update_memory":
                fact = args.get("fact", "")
                mem_type = args.get("memory_type", "fact")
                memory_mgr = MemoryManager(self.db)
                await memory_mgr.semantic.remember(user_id, fact, mem_type)
                memory_mgr.working.update(user_id, "preference", fact)
                # 同时记录 L3 历史（update_memory 也会产生会话记录）
                memory_mgr.history.log(
                    user_id=user_id,
                    user_message=f"update_memory: {mem_type}={fact}",
                    agent_reply="已记住",
                    intent="update_memory",
                )
                result = f"已记住：{fact}"
            else:
                result = f"未知工具: {tool_name}"

            if tool_name in ("book_seat", "cancel_appointment"):
                try:
                    self.db.commit()
                except Exception:
                    self.db.rollback()
            return result
        except Exception as e:
            return f"执行出错: {str(e)}"

    async def _search_books(self, query: str) -> str:
        """搜索图书"""
        agent = ServiceAgent(self.db)
        result = await agent.answer(query)
        books = result.get("books", [])
        if not books:
            return "未找到相关图书信息。"
        lines = ["为您找到以下相关图书："]
        for i, b in enumerate(books, 1):
            meta = b.get("metadata", {})
            title = meta.get("title", "未知")
            author = meta.get("author", "未知")
            location = meta.get("location", "未知")
            lines.append(f"{i}. 《{title}》作者：{author} 馆藏位置：{location}")
        return "\n".join(lines)

    def _query_policies(self, keyword: str) -> str:
        """查询图书馆规则"""
        service = PolicyService(self.db)
        results = service.search(keyword)
        if not results:
            return "未找到相关规则信息。"
        lines = [f"关于「{keyword}」的相关规则："]
        for r in results:
            preview = r.content[:200]
            if len(r.content) > 200:
                preview += "..."
            lines.append(f"- 【{r.title}】{preview}")
        return "\n".join(lines)

    async def _book_seat(self, args: dict, user_id: int) -> str:
        """预约座位（自动校正 LLM 传错的日期）"""
        if not user_id:
            return "请先登录后再预约座位。"

        seat_code = args.get("seat_code", "")
        date = args.get("date", "")
        start_str = args.get("start_time", "")
        end_str = args.get("end_time", "")

        if not all([seat_code, date, start_str, end_str]):
            return "预约信息不完整，请提供座位编号、日期、开始时间和结束时间。"

        # 用预处理的正确日期覆盖 LLM 传错的日期（DeepSeek 常用 2025 年）
        correct_date = getattr(self, '_correct_date', None)
        if correct_date:
            date = correct_date

        seat_repo = SeatRepository(self.db)
        seat = seat_repo.get_by_code(seat_code)
        if not seat:
            return f"未找到编号为「{seat_code}」的座位。"

        if seat.status != "available":
            return f"座位 {seat_code} 当前状态为「{seat.status}」，暂无法预约。"

        try:
            start_dt = datetime.strptime(f"{date} {start_str}", "%Y-%m-%d %H:%M")
            end_dt = datetime.strptime(f"{date} {end_str}", "%Y-%m-%d %H:%M")
        except ValueError:
            return "日期时间格式错误，请使用 YYYY-MM-DD 和 HH:MM 格式。"

        if start_dt >= end_dt:
            return "结束时间必须晚于开始时间。"

        from app.services.seat_service import SeatService

        seat_service = SeatService(self.db)
        result = await seat_service.book_seat(user_id, seat.id, start_dt, end_dt)

        if result["status"] == "success":
            return (
                f"座位 {seat_code} 预约成功！预约编号：{result['appointment_id']}，"
                f"日期：{date}，时段：{start_str}-{end_str}。"
            )
        return f"预约失败：{result.get('message', '未知错误')}"

    def _query_appointments(self, user_id: int) -> str:
        """查询预约记录"""
        if not user_id:
            return "请先登录后再查看预约记录。"
        service = ReservationService(self.db)
        apts = service.get_user_appointments(user_id)
        if not apts:
            return "您目前没有预约记录。"
        lines = ["您的预约记录："]
        for a in apts:
            code = str(a.resource_id)
            if a.resource_type == "seat":
                from app.models.seat import Seat

                seat = (
                    self.db.query(Seat)
                    .filter(Seat.id == a.resource_id)
                    .first()
                )
                code = seat.code if seat else f"#{a.resource_id}"
            lines.append(
                f"- 座位 {code} | {a.start_time.strftime('%m-%d %H:%M')}"
                f"-{a.end_time.strftime('%H:%M')} | 状态：{a.status}"
            )
        return "\n".join(lines)

    def _cancel_appointment(self, appointment_id: int, user_id: int) -> str:
        """取消预约"""
        if not user_id:
            return "请先登录后再操作。"
        if not appointment_id:
            return "请提供要取消的预约编号。"
        service = ReservationService(self.db)
        ok = service.cancel(appointment_id, user_id)
        if ok:
            return f"预约 #{appointment_id} 已成功取消。"
        return "取消失败，预约不存在或无权操作。"

    def _query_available_seats(self, floor: str = None) -> str:
        """查询可用座位"""
        service = SeatService(self.db)
        seats = service.get_available(floor)
        if not seats:
            msg = "当前没有可用座位。" if not floor else f"{floor} 当前没有可用座位。"
            return msg

        by_floor = {}
        for s in seats:
            by_floor.setdefault(s.floor, []).append(s)

        lines = ["当前可用座位如下："]
        for fl in sorted(by_floor.keys()):
            seat_list = by_floor[fl]
            codes = [s.code for s in seat_list]
            zones = set(s.zone for s in seat_list if s.zone)
            info = f"  {fl}（共 {len(seat_list)} 个可用）"
            if zones:
                info += f" [{', '.join(sorted(zones))}]"
            lines.append(info)
            for i in range(0, len(codes), 8):
                lines.append(f"  {'  '.join(codes[i:i+8])}")
        return "\n".join(lines)

    def _build_response(self, reply: str, tool_calls: list) -> dict:
        """构建统一的响应格式（始终清理 DSML/XML）"""
        reply = self._strip_xml(reply)
        INTENT_MAP = {
            "search_books": "search_book",
            "query_policies": "policy_query",
            "book_seat": "book_seat",
            "query_appointments": "query_appointment",
            "cancel_appointment": "cancel_appointment",
            "query_available_seats": "book_seat",
            "update_memory": "update_memory",
        }
        intent = "other"
        if tool_calls:
            intent = INTENT_MAP.get(tool_calls[0]["name"], "other")
        return {"reply": reply, "intent": intent}
