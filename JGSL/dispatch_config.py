from enum import IntEnum
from dataclasses import dataclass
from typing import Optional

@dataclass
class ServerConfig:
    """服务器配置类"""
    host: str = '0.0.0.0'
    dispatch_port: int = 8888
    http_port: int = 80
    dispatch_key: str = "grasscutter"
    encryption_key: str = "grasscutter"
    log_file: str = "logs/dispatch.log"
    log_level: str = "INFO"
    ssl_cert: Optional[str] = None
    ssl_key: Optional[str] = None

class PacketIds(IntEnum):
    """消息包ID枚举"""
    LoginNotify = 1
    TokenValidateReq = 2
    TokenValidateRsp = 3
    GachaHistoryReq = 4
    GachaHistoryRsp = 5
    GetAccountReq = 6
    GetAccountRsp = 7
    GetPlayerFieldsReq = 8
    GetPlayerFieldsRsp = 9
    GetPlayerByAccountReq = 10
    GetPlayerByAccountRsp = 11
    ServerMessageNotify = 12