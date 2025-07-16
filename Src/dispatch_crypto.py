def xor_encrypt(data: bytes, key: bytes) -> bytes:
    """简单的XOR加密"""
    if not key:
        return data
    return bytes([b ^ key[i % len(key)] 
                 for i, b in enumerate(data)])
    
def xor_decrypt(data: bytes, key: bytes) -> bytes:
    """简单的XOR解密"""
    return bytes([b ^ key[i % len(key)] 
                 for i, b in enumerate(data)])