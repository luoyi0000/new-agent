"""读者画像 Agent

分析读者借阅记录、预约偏好，生成行为标签和个性化推荐。
"""
from sqlalchemy.orm import Session

from app.repositories.user_repository import UserRepository
from app.repositories.appointment_repository import AppointmentRepository
from app.services.book_service import BookService


class ProfileAgent:
    """读者画像分析"""

    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.apt_repo = AppointmentRepository(db)
        self.book_service = BookService(db)

    def get_profile(self, user_id: int) -> dict:
        """获取读者画像数据"""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return {"error": "用户不存在"}

        appointments = self.apt_repo.get_by_user(user_id)

        total_appointments = len(appointments)
        completed = sum(1 for a in appointments if a.status == "completed")
        cancelled = sum(1 for a in appointments if a.status == "cancelled")

        seat_apts = [a for a in appointments if a.resource_type == "seat"]
        seat_count = len(seat_apts)

        tags = []
        if total_appointments > 10:
            tags.append("活跃读者")
        if completed / max(total_appointments, 1) > 0.8:
            tags.append("守信读者")
        if seat_count > 5:
            tags.append("常驻自习者")

        return {
            "username": user.username,
            "student_id": user.student_id,
            "member_since": user.created_at.isoformat() if user.created_at else None,
            "stats": {
                "total_appointments": total_appointments,
                "completed": completed,
                "cancelled": cancelled,
                "seat_appointments": seat_count,
            },
            "tags": tags,
        }

    def get_recommendations(self, user_id: int, top_k: int = 5) -> list:
        """基于读者行为的简单推荐"""
        books = self.book_service.get_all()
        return [
            {"id": b.id, "title": b.title, "author": b.author}
            for b in books[:top_k]
        ]

    async def answer(self, user_id: int, query: str = "") -> dict:
        """回答读者画像相关问题"""
        profile = self.get_profile(user_id)
        if "error" in profile:
            return {"reply": profile["error"]}

        stats = profile["stats"]
        reply = (
            f"【{profile['username']} 的读者画像】\n"
            f"学号：{profile['student_id'] or '未绑定'}\n"
            f"总预约次数：{stats['total_appointments']} 次\n"
            f"已完成：{stats['completed']} 次 | 已取消：{stats['cancelled']} 次\n"
            f"座位预约：{stats['seat_appointments']} 次\n"
            f"标签：{'、'.join(profile['tags']) or '暂无标签'}"
        )
        return {"reply": reply}
