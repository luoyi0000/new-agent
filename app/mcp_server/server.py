"""MCP Server 实现

开放 5 个 Tool 供外部 AI 客户端调用：
1. search_books — 馆藏检索
2. get_seats — 查询座位
3. book_seat — 预约座位
4. get_policies — 查询规则
5. get_user_appointments — 查询预约
"""
from mcp.server import FastMCP
from app.core.database import SessionLocal
from app.services.book_service import BookService
from app.services.seat_service import SeatService
from app.services.reservation_service import ReservationService, PolicyService
from app.repositories.policy_repository import PolicyRepository

mcp = FastMCP("图书馆智能服务系统")


def get_db():
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()


@mcp.tool()
def search_books(query: str, category: str = None) -> list:
    """检索图书"""
    db = get_db()
    try:
        service = BookService(db)
        results = service.search_books(query, category)
        return [
            {"id": b.id, "title": b.title, "author": b.author,
             "category": b.category, "location": b.location, "status": b.status}
            for b in results
        ]
    finally:
        db.close()


@mcp.tool()
def get_seats(floor: str = None) -> list:
    """查询座位"""
    db = get_db()
    try:
        service = SeatService(db)
        seats = service.get_by_floor(floor) if floor else service.get_available()
        return [
            {"id": s.id, "code": s.code, "floor": s.floor,
             "zone": s.zone, "status": s.status}
            for s in seats
        ]
    finally:
        db.close()


@mcp.tool()
def get_policies(keyword: str = "") -> list:
    """查询图书馆规则"""
    db = get_db()
    try:
        service = PolicyService(db)
        if keyword:
            results = service.search(keyword)
        else:
            results = PolicyRepository(db).get_all()
        return [
            {"id": p.id, "title": p.title, "content": p.content[:200], "category": p.category}
            for p in results
        ]
    finally:
        db.close()


@mcp.tool()
def get_user_appointments(user_id: int) -> list:
    """查询用户预约"""
    db = get_db()
    try:
        service = ReservationService(db)
        apts = service.get_user_appointments(user_id)
        return [
            {"id": a.id, "resource_type": a.resource_type,
             "resource_id": a.resource_id,
             "start_time": a.start_time.isoformat(),
             "end_time": a.end_time.isoformat(),
             "status": a.status}
            for a in apts
        ]
    finally:
        db.close()
