import asyncio
from typing import TYPE_CHECKING

from .http.endpoints import Endpoint
from .data import StatusData, LogsData, FullLogsData, BackupData
if TYPE_CHECKING:
    from .app import Application
from typing import Callable


class ListenerManager:
    def __init__(self, app: 'Application'):
        self.app: Application = app
        self.listeners: dict[str, Callable] = {}

    def add_listener(self, endpoint: Endpoint, call: Callable):
        self.listeners[endpoint.name] = call

    async def on_request_end(self, endpoint: Endpoint, **kwargs):
        call: Callable = self.listeners.get(endpoint.name)
        if not call:
            return
        match endpoint.name:
            case 'APP_STATUS':
                status: StatusData = kwargs.get('status')
                if asyncio.iscoroutinefunction(call):
                    return await call(status=status)
                return call(status=status)
            case 'LOGS':
                logs: LogsData = kwargs.get('logs')
                if asyncio.iscoroutinefunction(call):
                    return await call(logs=logs)
                return call(logs=logs)
            case 'FULL_LOGS':
                full_logs: FullLogsData = kwargs.get('full_logs')
                if asyncio.iscoroutinefunction(call):
                    return await call(full_logs=full_logs)
                return call(full_logs=full_logs)
            case 'BACKUP':
                backup: BackupData = kwargs.get('backup')
                if asyncio.iscoroutinefunction(call):
                    return await call(backup=backup)
                return call(backup=backup)
