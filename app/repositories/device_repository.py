from app.repositories.base import BaseRepository
from app.models.device import Device
from typing import Optional, List


class DeviceRepository(BaseRepository):
    def create_device(self, name: str, device_type: str, location: Optional[str] = None, hourly_rate: float = 0.0) -> int:
        device = Device(name=name, device_type=device_type, location=location, hourly_rate=hourly_rate)
        return self.add(device)

    def get_by_id(self, device_id: int) -> Optional[Device]:
        return self.db.query(Device).filter(Device.id == device_id).first()

    def get_all(self) -> List[Device]:
        return self.db.query(Device).all()

    def get_available(self) -> List[Device]:
        return self.db.query(Device).filter(Device.status == "available").all()
