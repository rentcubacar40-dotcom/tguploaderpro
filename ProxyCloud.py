class ProxyCloud(object):
    def __init__(self, ip, port, type='socks5'):
        self.ip = ip
        self.port = port
        self.default = None
        self.type = type
    
    def set_default(self, socket):
        self.default = socket
    
    def as_dict_proxy(self):
        return {
            'http': f'{self.type}://{self.ip}:{self.port}',
            'https': f'{self.type}://{self.ip}:{self.port}'
        }


def parse(text):
    """
    Versión CORREGIDA que:
    1. Intenta desencriptar (si usa S5Crypto)
    2. Si falla, usa proxy directo (no encriptado)
    3. Devuelve DICT para MoodleClient
    """
    if not text:
        return None
    
    try:
        text_str = str(text).strip()
        if not text_str:
            return None
        
        # Si YA es dict, devolverlo (compatibilidad)
        if isinstance(text, dict):
            return text
        
        # Separar protocolo
        if '://' in text_str:
            protocol, rest = text_str.split('://', 1)
        else:
            protocol = 'socks5'
            rest = text_str
        
        # Intentar desencriptar (solo si parece encriptado)
        try:
            # Solo si es largo y no tiene : (posible encriptado)
            if len(rest) > 20 and ':' not in rest:
                decrypted = S5Crypto.decrypt(rest)
                rest = decrypted
        except:
            # Si no está encriptado, usar tal cual
            pass
        
        # Extraer IP:puerto
        if ':' in rest:
            ip, port_str = rest.split(':', 1)
            try:
                port = int(port_str)
            except:
                port = 1080
        else:
            ip = rest
            port = 1080
        
        # Validar protocolo
        if protocol not in ['socks4', 'socks5', 'http', 'https']:
            protocol = 'socks5'
        
        # ✅ IMPORTANTE: Devolver DICT para MoodleClient
        return {
            'http': f'{protocol}://{ip}:{port}',
            'https': f'{protocol}://{ip}:{port}'
        }
    
    except Exception as e:
        print(f"[ProxyCloud] Error: {e}")
        # En caso de error, intentar devolver string como dict
        if text and '://' in str(text):
            return {'http': str(text), 'https': str(text)}
    
    return None
