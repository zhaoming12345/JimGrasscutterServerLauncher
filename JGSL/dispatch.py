from loguru import logger
import asyncio
import websockets
from typing import Optional, Dict

class DispatchServer:
    """内置调度服务器实现
    
    负责处理WebSocket连接和消息分发
    """
    def __init__(self, host: str = '0.0.0.0', port: int = 443):
        self.host = host
        self.port = port
        self.clients: Dict[str, websockets.WebSocketServerProtocol] = {}
        self.server: Optional[websockets.WebSocketServer] = None

    async def handle_connection(self, websocket, path):
        """处理新客户端连接
        
        Args:
            websocket: 客户端WebSocket连接
            path: 连接路径
        """
        client_id = path.lstrip('/')
        self.clients[client_id] = websocket
        logger.info(f"新客户端连接: {client_id} ")

        try:
            async for message in websocket:
                await self.handle_message(client_id, message)
        except websockets.exceptions.ConnectionClosed:
            logger.warning(f"客户端 {client_id} 断开连接")
        finally:
            self.clients.pop(client_id, None)

    async def handle_message(self, client_id: str, message: str):
        """处理客户端消息
        
        Args:
            client_id: 客户端ID
            message: 接收到的消息
        """
        logger.debug(f"收到来自 {client_id} 的消息: {message} ")
        # 这里可以添加消息处理逻辑

    async def start(self):
        """启动调度服务器"""
        self.server = await websockets.serve(
            self.handle_connection,
            self.host,
            self.port,
            ssl=None  # 可以添加SSL配置
        )
        logger.success(f"调度服务器已启动在 {self.host}:{self.port} ")

    async def stop(self):
        """停止调度服务器"""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            logger.info("调度服务器已停止")


class DispatchClient:
    """内置调度客户端实现
    
    负责连接到调度服务器并发送/接收消息
    """
    def __init__(self, server_url: str, client_id: str):
        self.server_url = server_url
        self.client_id = client_id
        self.connection: Optional[websockets.WebSocketClientProtocol] = None

    async def connect(self):
        """连接到调度服务器"""
        self.connection = await websockets.connect(
            f"{self.server_url}/{self.client_id}",
            ssl=None  # 可以添加SSL配置
        )
        logger.success(f"已连接到调度服务器 {self.server_url} ")

    async def send_message(self, message: str):
        """发送消息到调度服务器
        
        Args:
            message: 要发送的消息内容
        """
        if self.connection:
            await self.connection.send(message)
            logger.debug(f"已发送消息: {message} ")

    async def close(self):
        """关闭连接"""
        if self.connection:
            await self.connection.close()
            logger.info("已断开与调度服务器的连接")