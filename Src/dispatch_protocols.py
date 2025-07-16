import json

def encode_message(packet_id: int, message):
    """编码消息
    
    Args:
        packet_id: 消息包ID
        message: 消息内容
        
    Returns:
        编码后的消息对象
    """
    server_message = {
        "packetId": packet_id,
        "message": json.dumps(message) if isinstance(message, (dict, list)) else message
    }
    return server_message