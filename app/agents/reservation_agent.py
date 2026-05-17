"""预约 Agent（已废弃 — 由 orchestrator Tool-Calling + ReservationService 取代）

处理座位预约、查询预约、取消预约等操作。
"""
from sqlalchemy.orm import Session
from datetime import datetime

from app.services.seat_service import SeatService
from app.services.reservation_service import ReservationService


class ReservationAgent:
    """预约处理 Agent"""

    def __init__(self, db: Session):
        self.db = db
        self.seat_service = SeatService(db)
        self.reservation_service = ReservationService(db)

    async def book_seat(self, user_id: int, seat_id: int, start_time: datetime, end_time: datetime) -> dict:
        """预约座位"""
        return await self.seat_service.book_seat(user_id, seat_id, start_time, end_time)

    def query_appointments(self, user_id: int) -> list:
        """查询用户预约"""
        return self.reservation_service.get_user_appointments(user_id)

    def cancel_appointment(self, appointment_id: int, user_id: int) -> bool:
        """取消预约"""
        return self.reservation_service.cancel(appointment_id, user_id)

    async def handle(self, user_id: int, intent: str, params: dict = None) -> dict:
        """处理预约相关请求"""
        if intent == "book_seat":
            if not params or "seat_id" not in params:
                return {"reply": "请提供座位编号和预约时间。"}
            result = await self.book_seat(
                user_id=user_id,
                seat_id=params["seat_id"],
                start_time=params.get("start_time", datetime.now()),
                end_time=params.get("end_time", datetime.now()),
            )
            if result["status"] == "success":
                return {"reply": f"座位预约成功！预约编号：{result['appointment_id']}"}
            return {"reply": f"预约失败：{result.get('message', '未知错误')}"}

        if intent == "query_appointment":
            apts = self.query_appointments(user_id)
            if not apts:
                return {"reply": "您目前没有预约记录。"}
            reply_lines = ["您的预约记录："]
            for a in apts:
                reply_lines.append(
                    f"- {a.resource_type} #{a.resource_id} "
                    f"[{a.start_time.strftime('%m-%d %H:%M')}-{a.end_time.strftime('%H:%M')}] "
                    f"状态：{a.status}"
                )
            return {"reply": "\n".join(reply_lines)}

        if intent == "cancel_appointment":
            if not params or "appointment_id" not in params:
                return {"reply": "请提供要取消的预约编号。"}
            ok = self.cancel_appointment(params["appointment_id"], user_id)
            if ok:
                return {"reply": f"预约 #{params['appointment_id']} 已取消。"}
            return {"reply": "取消失败，预约不存在或无权操作。"}

        return {"reply": "抱歉，暂不支持该操作。"}
