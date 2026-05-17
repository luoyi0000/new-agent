"""Celery 异步任务

- 预约提醒：在预约开始前发送提醒通知
- 超时释放：预约过期后自动释放座位
- 候补通知：有空位时通知候补用户
"""
from .reminder import send_appointment_reminder
from .timeout import release_expired_appointments

__all__ = ["send_appointment_reminder", "release_expired_appointments"]
