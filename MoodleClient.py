import requests
import os
import re
import json
import urllib
from bs4 import BeautifulSoup
import requests_toolbelt as rt
from requests_toolbelt import MultipartEncoderMonitor
from requests_toolbelt import MultipartEncoder
from functools import partial
import uuid
import time
from ProxyCloud import ProxyCloud
import S5Crypto
import random

class CallingUpload:
    def __init__(self, func, filename, args):
        self.func = func
        self.args = args
        self.filename = filename
        self.time_start = time.time()
        self.time_total = 0
        self.speed = 0
        self.last_read_byte = 0
        
    def __call__(self, monitor):
        try:
            self.speed += monitor.bytes_read - self.last_read_byte
            self.last_read_byte = monitor.bytes_read
            tcurrent = time.time() - self.time_start
            self.time_total += tcurrent
            self.time_start = time.time()
            if self.time_total >= 1:
                clock_time = (monitor.len - monitor.bytes_read) / (self.speed) if self.speed > 0 else 0
                if self.func:
                    self.func(self.filename, monitor.bytes_read, monitor.len, self.speed, clock_time, self.args)
                self.time_total = 0
                self.speed = 0
        except Exception as e:
            print(f"Error in CallingUpload: {e}")

class MoodleClient(object):
    def __init__(self, user, passw, host='', repo_id=4, proxy: ProxyCloud = None):
        self.username = user
        self.password = passw
        self.session = requests.Session()
        self.path = 'https://moodle.uclv.edu.cu/'
        self.host_tokenize = 'https://tguploader.url/'
        if host != '':
            self.path = host
        self.userdata = None
        self.userid = ''
        self.repo_id = repo_id
        self.sesskey = ''
        
        # 🎯 DETECCIÓN DE PLATAFORMA
        self.platform_type = self._detect_platform()
        
        # 🚨 CONEXIÓN DIRECTA - Sin proxy
        self.proxy_config = None
        self.current_proxy_url = "DIRECT_CONNECTION"
        
        # Headers básicos
        self.baseheaders = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
        }
        
        self.session.headers.update(self.baseheaders)
        self.session.trust_env = False

    def _detect_platform(self):
        """Detectar tipo de plataforma basado en URL"""
        host = self.path.lower()
        if 'eva.uo.edu.cu' in host:
            return 'eva'
        elif 'cursos.uo.edu.cu' in host:
            return 'cursos' 
        elif 'aulacened.uci.cu' in host:
            return 'cened'
        else:
            return 'generic'

    def _make_request(self, method, url, **kwargs):
        """Método simplificado para requests"""
        max_retries = 2
        
        for attempt in range(max_retries):
            try:
                # Simular delay humano
                if attempt > 0:
                    time.sleep(random.uniform(1, 3))
                
                # Headers básicos
                if 'headers' not in kwargs:
                    kwargs['headers'] = self.baseheaders
                
                # 🚨 NO usar proxy
                if 'proxies' in kwargs:
                    del kwargs['proxies']
                
                # Timeout
                if 'timeout' not in kwargs:
                    kwargs['timeout'] = 30
                
                print(f"🌐 Request to: {urllib.parse.urlparse(url).hostname}")
                
                response = self.session.request(method, url, **kwargs)
                
                if response.status_code == 200:
                    return response
                else:
                    print(f"⚠️ Status code {response.status_code}, reintentando...")
                    continue
                    
            except requests.exceptions.Timeout:
                print(f"⏰ Timeout en intento {attempt + 1}")
                continue
            except requests.exceptions.ConnectionError as e:
                print(f"🔌 Connection error: {e}")
                if attempt < max_retries - 1:
                    time.sleep(3)
                    continue
                raise
            except Exception as e:
                print(f"❌ Request error: {e}")
                continue
        
        raise Exception("Todos los intentos fallaron")

    def test_connection(self):
        """Test básico de conexión"""
        try:
            test_url = f"{self.path}login/index.php"
            response = self._make_request('GET', test_url, timeout=15)
            return 'moodle' in response.text.lower()
        except:
            return False

    def getUserData(self):
        """Obtener datos de usuario"""
        try:
            tokenUrl = self.path + 'login/token.php?service=moodle_mobile_app&username=' + urllib.parse.quote(self.username) + '&password=' + urllib.parse.quote(self.password)
            resp = self._make_request('GET', tokenUrl)
            data = self.parsejson(resp.text)
            
            if 'token' in data:
                data['s5token'] = S5Crypto.tokenize([self.username, self.password, data['token']])
            else:
                data['s5token'] = S5Crypto.tokenize([self.username, self.password])
                
            return data
        except Exception as e:
            print(f"Error in getUserData: {e}")
            return None

    def getSessKey(self):
        """Obtener clave de sesión"""
        try:
            # 🎯 URL ESPECÍFICA POR PLATAFORMA
            if self.platform_type in ['eva', 'cursos']:
                fileurl = self.path + 'user/files.php'
            else:
                fileurl = self.path + 'my/'
                
            resp = self._make_request('GET', fileurl)
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Buscar sesskey en múltiples ubicaciones
            sesskey_selectors = [
                'input[name="sesskey"]',
                '[name="sesskey"]',
                'input[name="sesskey"]',
                '#sesskey'
            ]
            
            for selector in sesskey_selectors:
                sesskey = soup.select_one(selector)
                if sesskey and sesskey.get('value'):
                    return sesskey['value']
                    
            # Buscar en scripts
            script_pattern = r'\"sesskey\"\s*:\s*\"([a-zA-Z0-9]+)\"'
            matches = re.findall(script_pattern, resp.text)
            if matches:
                return matches[0]
                
        except Exception as e:
            print(f"Error getting sesskey: {e}")
        return ''

    def login(self):
        """Login simplificado"""
        try:
            print(f"🔐 Login en: {urllib.parse.urlparse(self.path).hostname} ({self.platform_type.upper()})")
            
            login_url = self.path + 'login/index.php'
            resp = self._make_request('GET', login_url)
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Extraer tokens
            logintoken = ''
            try:
                logintoken_input = soup.find('input', attrs={'name': 'logintoken'})
                if logintoken_input:
                    logintoken = logintoken_input['value']
            except:
                pass

            # Preparar login
            payload = {
                'logintoken': logintoken,
                'username': self.username,
                'password': self.password,
                'rememberusername': 1
            }
            
            login_headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Referer': login_url,
            }
            
            resp2 = self._make_request('POST', login_url, data=payload, headers=login_headers)
            
            # Verificar login
            if self._is_login_successful(resp2):
                print("✅ Login exitoso")
                
                # Obtener userid
                self._extract_user_id(resp2.text)
                
                # Obtener datos
                self.userdata = self.getUserData()
                self.sesskey = self.getSessKey()
                
                print(f"🎯 Plataforma: {self.platform_type.upper()}")
                print(f"🔑 SessKey: {self.sesskey}")
                print(f"👤 UserID: {self.userid}")
                
                return True
            else:
                print("❌ Login fallido")
                return False
                
        except Exception as ex:
            print(f"❌ Error en login: {ex}")
            return False

    def _is_login_successful(self, response):
        """Verificar login exitoso"""
        content_lower = response.text.lower()
        
        success_indicators = ['dashboard', 'my/home', 'userid', 'mis cursos', 'my courses']
        failure_indicators = ['loginerrors', 'invalid login', 'usuario o contraseña incorrectos', 'invalidusername']
        
        if any(indicator in content_lower for indicator in success_indicators):
            return True
        if any(indicator in content_lower for indicator in failure_indicators):
            return False
            
        # Verificar redirección
        if len(response.history) > 0:
            return True
            
        return False

    def _extract_user_id(self, html_content):
        """Extraer user ID"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Buscar userid
            userid_selectors = [
                'div[data-userid]',
                'a[data-userid]', 
                '[data-userid]',
                '.userid',
                '#userid'
            ]
            
            for selector in userid_selectors:
                element = soup.select_one(selector)
                if element and 'data-userid' in element.attrs:
                    self.userid = element['data-userid']
                    return
                    
            # Buscar en scripts
            script_patterns = [
                r'\"userid\"\s*:\s*\"?(\d+)\"?',
                r'M\.cfg\s*=\s*{[^}]*\"userid\"\s*:\s*(\d+)',
                r'userid["\']?\s*:\s*["\']?(\d+)'
            ]
            
            for pattern in script_patterns:
                matches = re.findall(pattern, html_content)
                if matches:
                    self.userid = matches[0]
                    return
                    
        except Exception as e:
            print(f"⚠️ No se pudo extraer userid: {e}")
            self.userid = ''

    def _get_upload_urls(self):
        """Obtener URLs específicas para upload según plataforma"""
        if self.platform_type == 'eva':
            return {
                'file_page': f'{self.path}user/files.php',
                'upload_endpoint': f'{self.path}repository/repository_ajax.php?action=upload'
            }
        elif self.platform_type == 'cursos':
            return {
                'file_page': f'{self.path}user/files.php', 
                'upload_endpoint': f'{self.path}repository/repository_ajax.php?action=upload'
            }
        elif self.platform_type == 'cened':
            return {
                'file_page': f'{self.path}user/files.php',
                'upload_endpoint': f'{self.path}repository/repository_ajax.php?action=upload'
            }
        else:
            return {
                'file_page': f'{self.path}user/files.php',
                'upload_endpoint': f'{self.path}repository/repository_ajax.php?action=upload'
            }

    def _upload_file_generic(self, file, itemid=None, progressfunc=None, args=(), tokenize=False, upload_type='draft'):
        """Método principal de upload - MEJORADO"""
        try:
            # 🎯 OBTENER URLs ESPECÍFICAS
            urls = self._get_upload_urls()
            file_page_url = urls['file_page']
            upload_endpoint = urls['upload_endpoint']
            
            print(f"📤 Preparando upload a: {self.platform_type.upper()} ({upload_type})")
            print(f"📄 Archivo: {os.path.basename(file)}")
            
            # Obtener página de archivos
            resp = self._make_request('GET', file_page_url)
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Obtener sesskey
            sesskey = self.sesskey
            if not sesskey:
                sesskey_input = soup.find('input', attrs={'name': 'sesskey'})
                if sesskey_input:
                    sesskey = sesskey_input['value']
                else:
                    sesskey = self.getSessKey()
                    if not sesskey:
                        raise Exception("No se pudo obtener sesskey")

            # Extraer parámetros del repositorio
            repo_data = self._extract_repository_data(resp.text)
            if not repo_data:
                raise Exception("No se pudieron extraer datos del repositorio")
            
            itempostid = repo_data.get('itemid', '')
            if itemid:
                itempostid = itemid

            # Preparar upload
            of = open(file, 'rb')
            boundary = uuid.uuid4().hex
            
            # 🎯 DATOS DE UPLOAD MEJORADOS
            upload_data = {
                'title': (None, ''),
                'author': (None, 'Academic User'),
                'license': (None, 'allrightsreserved'),
                'itemid': (None, itempostid),
                'repo_id': (None, str(self.repo_id)),
                'env': (None, repo_data.get('env', '')),
                'sesskey': (None, sesskey),
                'client_id': (None, repo_data.get('client_id', '')),
                'maxbytes': (None, repo_data.get('maxbytes', '209715200')),
                'ctx_id': (None, repo_data.get('ctx_id', '')),
                'savepath': (None, '/')
            }
            
            upload_file = {
                'repo_upload_file': (os.path.basename(file), of, 'application/octet-stream'),
                **upload_data
            }
            
            # Realizar upload
            encoder = rt.MultipartEncoder(upload_file, boundary=boundary)
            
            # Callback de progreso
            if progressfunc:
                progrescall = CallingUpload(progressfunc, file, args)
                callback = partial(progrescall)
                monitor = MultipartEncoderMonitor(encoder, callback=callback)
            else:
                monitor = encoder
            
            upload_headers = {
                "Content-Type": "multipart/form-data; boundary=" + boundary,
                "X-Requested-With": "XMLHttpRequest",
                "Referer": file_page_url
            }
            
            print(f"🚀 Enviando upload a: {upload_endpoint}")
            resp2 = self._make_request('POST', upload_endpoint, data=monitor, headers=upload_headers)
            of.close()

            # Procesar respuesta
            data = self.parsejson(resp2.text)
            
            if not data or 'url' not in data:
                print(f"❌ Respuesta del servidor: {resp2.text}")
                raise Exception("Upload falló - respuesta inválida del servidor")
            
            data['url'] = str(data['url']).replace('\\', '')
            data['normalurl'] = data['url']
            
            # 🎯 APLICAR WEBSERVICE CORRECTAMENTE
            if self.userdata and 'token' in self.userdata and not tokenize:
                if '/pluginfile.php/' in data['url']:
                    data['url'] = data['url'].replace('/pluginfile.php/', '/webservice/pluginfile.php/')
                if 'token=' not in data['url']:
                    data['url'] += ('&' if '?' in data['url'] else '?') + 'token=' + self.userdata['token']

            print(f"✅ Upload exitoso a {self.platform_type.upper()}")
            print(f"🔗 URL generada: {data['url'][:100]}...")
            
            return itempostid, data
            
        except Exception as e:
            print(f"❌ Error en upload a {self.platform_type.upper()}: {e}")
            return None, None

    def _extract_repository_data(self, html_content):
        """Extraer datos del repositorio mejorado"""
        try:
            # Buscar en scripts
            patterns = [
                r'M\.cfg\s*=\s*({[^}]+})',
                r'var\s+repository_upload_data\s*=\s*({[^}]+})',
                r'repository_upload_data\s*=\s*({[^}]+})'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, html_content)
                if matches:
                    try:
                        data = json.loads(matches[0])
                        return {
                            'itemid': str(data.get('itemid', '')),
                            'env': data.get('env', 'filepicker'),
                            'client_id': data.get('client_id', ''),
                            'maxbytes': str(data.get('maxbytes', '209715200')),
                            'ctx_id': str(data.get('ctx_id', ''))
                        }
                    except:
                        continue
            
            # Fallback: extraer de elementos HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            filemanager = soup.find('div', {'data-type': 'filemanager'})
            if filemanager and filemanager.get('data'):
                try:
                    data = json.loads(filemanager['data'])
                    return {
                        'itemid': str(data.get('itemid', '')),
                        'env': data.get('env', 'filepicker'),
                        'client_id': data.get('client_id', ''),
                        'maxbytes': str(data.get('maxbytes', '209715200')),
                        'ctx_id': str(data.get('ctx_id', ''))
                    }
                except:
                    pass
            
            # Último fallback
            return {
                'itemid': str(int(time.time())),
                'env': 'filepicker',
                'client_id': 'filepicker',
                'maxbytes': '209715200',
                'ctx_id': '1'
            }
            
        except Exception as e:
            print(f"Error extracting repository data: {e}")
            return {
                'itemid': str(int(time.time())),
                'env': 'filepicker',
                'client_id': 'filepicker',
                'maxbytes': '209715200',
                'ctx_id': '1'
            }

    # 🎯 MÉTODOS PRINCIPALES - MEJORADOS
    def upload_file_draft(self, file, progressfunc=None, args=(), tokenize=False):
        """Subida a draft - MÉTODO PRINCIPAL"""
        print(f"📤 Subiendo a DRAFT en {self.platform_type.upper()}: {os.path.basename(file)}")
        return self._upload_file_generic(
            file=file,
            itemid=None,
            progressfunc=progressfunc,
            args=args,
            tokenize=tokenize,
            upload_type='draft'
        )

    def upload_file_evidence(self, file, progressfunc=None, args=(), tokenize=False):
        """Subida a evidence"""
        print(f"📤 Subiendo a EVIDENCE en {self.platform_type.upper()}: {os.path.basename(file)}")
        return self._upload_file_generic(
            file=file,
            itemid=None,
            progressfunc=progressfunc,
            args=args,
            tokenize=tokenize,
            upload_type='evidence'
        )

    # Método de compatibilidad
    def upload_file(self, file, evidence=None, itemid=None, progressfunc=None, args=(), tokenize=False):
        """Método original mantenido por compatibilidad"""
        return self.upload_file_draft(file, progressfunc, args, tokenize)

    def parsejson(self, json_text):
        """Parsear JSON"""
        data = {}
        try:
            json_text = json_text.strip()
            if json_text.startswith('{') and json_text.endswith('}'):
                data = json.loads(json_text)
            else:
                # Fallback para respuestas no estándar
                tokens = str(json_text).replace('{', '').replace('}', '').split(',')
                for t in tokens:
                    split = str(t).split(':', 1)
                    if len(split) == 2:
                        key = str(split[0]).replace('"', '').strip()
                        value = str(split[1]).replace('"', '').strip()
                        data[key] = value
        except Exception as e:
            print(f"Error parsing JSON: {e}")
            # Intentar extraer URL manualmente
            if 'url' in json_text.lower():
                url_match = re.search(r'\"url\"\s*:\s*\"([^\"]+)\"', json_text)
                if url_match:
                    data['url'] = url_match.group(1)
        return data

    def getclientid(self, html):
        """Extraer client_id"""
        try:
            index = str(html).index('client_id')
            max_len = 25
            ret = html[index:(index + max_len)]
            return str(ret).replace('client_id":"', '').replace('"', '')
        except:
            return 'filepicker'

    def extractQuery(self, url):
        """Extraer parámetros de query string"""
        retQuery = {}
        try:
            if '?' in url:
                query_string = url.split('?')[1]
                tokens = query_string.split('&')
                for q in tokens:
                    qspl = q.split('=')
                    if len(qspl) == 2:
                        retQuery[qspl[0]] = qspl[1]
        except Exception as e:
            print(f"Error extracting query: {e}")
        return retQuery

    def logout(self):
        """Cerrar sesión"""
        try:
            if self.sesskey:
                logouturl = self.path + 'login/logout.php?sesskey=' + self.sesskey
                self._make_request('POST', logouturl)
                print("✅ Sesión cerrada")
        except Exception as e:
            print(f"Error logging out: {e}")
