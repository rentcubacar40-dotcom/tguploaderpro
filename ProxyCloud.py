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
    Versión COMPATIBLE que:
    1. Devuelve dict para MoodleClient (principal)
    2. Mantiene clase ProxyCloud para compatibilidad
    """
    if not text:
        return None
    
    try:
        text_str = str(text).strip()
        if not text_str:
            return None
        
        # Si YA es dict (compatibilidad futura), devolverlo
        if isinstance(text, dict):
            return text
        
        # Separar protocolo
        if text_str.startswith('socks4://'):
            protocol = 'socks4'
            rest = text_str[9:]
        elif text_str.startswith('socks5://'):
            protocol = 'socks5'
            rest = text_str[9:]
        elif text_str.startswith('http://'):
            protocol = 'http'
            rest = text_str[7:]
        elif text_str.startswith('https://'):
            protocol = 'https'
            rest = text_str[8:]
        else:
            protocol = 'socks5'
            rest = text_str
        
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
        
        # ✅ DEVOLVER DICT (compatible con MoodleClient)
        return {
            'http': f'{protocol}://{ip}:{port}',
            'https': f'{protocol}://{ip}:{port}'
        }
    
    except Exception as e:
        print(f"[ProxyCloud] Error: {e}")
        # Fallback: devolver string como dict
        if text and isinstance(text, str):
            return {'http': text, 'https': text}
    
    return None
