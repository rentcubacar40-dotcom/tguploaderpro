import requests
import os
import textwrap
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
import socket
import socks
import asyncio
import threading
import S5Crypto

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

class AcademicSessionManager:
    """Gestor inteligente de sesiones académicas"""
    def __init__(self):
        self.academic_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
        }
        
        self.cuban_referers = [
            'https://eva.uo.edu.cu/',
            'https://cursos.uo.edu.cu/',
            'https://aulacened.uci.cu/',
            'https://www.uo.edu.cu/',
        ]
    
    def get_academic_headers(self, host):
        """Obtener headers que simulan navegador académico legítimo"""
        headers = self.academic_headers.copy()
        headers['Referer'] = random.choice(self.cuban_referers)
        headers['Origin'] = urllib.parse.urlparse(host).scheme + '://' + urllib.parse.urlparse(host).hostname
        return headers

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
        
        # 🎯 NUEVO: Gestor de sesiones académicas
        self.session_manager = AcademicSessionManager()
        
        # 🚨 CONEXIÓN DIRECTA - Sin proxy forzado
        self.proxy_config = None
        self.current_proxy_url = "DIRECT_CONNECTION"
        
        # Configurar headers académicos
        self.baseheaders = self.session_manager.get_academic_headers(self.path)
        
        # Configurar session para ser más "humana"
        self.session.headers.update(self.baseheaders)
        self.session.trust_env = False  # Evitar usar proxies del sistema

    def getsession(self):
        return self.session

    def _make_request(self, method, url, **kwargs):
        """Método mejorado para requests académicas"""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                # 🎯 Simular delay humano entre intentos
                if attempt > 0:
                    time.sleep(random.uniform(2, 4))
                
                # Asegurar headers académicos
                if 'headers' not in kwargs:
                    kwargs['headers'] = self.baseheaders
                else:
                    kwargs['headers'] = {**self.baseheaders, **kwargs['headers']}
                
                # 🚨 NO usar proxy - Conexión directa
                if 'proxies' in kwargs:
                    del kwargs['proxies']
                
                # Timeout extendido para conexiones académicas
                if 'timeout' not in kwargs:
                    kwargs['timeout'] = 30
                
                # Headers específicos para Moodle
                moodle_headers = {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Sec-Fetch-Dest': 'empty',
                    'Sec-Fetch-Mode': 'cors',
                    'Sec-Fetch-Site': 'same-origin',
                }
                kwargs['headers'].update(moodle_headers)
                
                print(f"🌐 Request [{attempt + 1}/{max_retries}] to: {urllib.parse.urlparse(url).hostname}")
                
                response = self.session.request(method, url, **kwargs)
                
                # Verificar respuesta válida de Moodle
                if self._is_valid_moodle_response(response):
                    return response
                else:
                    print(f"⚠️ Respuesta Moodle inusual, reintentando...")
                    continue
                    
            except requests.exceptions.Timeout:
                print(f"⏰ Timeout en intento {attempt + 1}")
                if attempt < max_retries - 1:
                    continue
                raise
            except requests.exceptions.ConnectionError as e:
                print(f"🔌 Connection error en intento {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(5)
                    continue
                raise
            except requests.exceptions.RequestException as e:
                print(f"❌ Request error en intento {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    continue
                raise
        
        raise requests.exceptions.RequestException("Todos los intentos fallaron")

    def _is_valid_moodle_response(self, response):
        """Verificar si la respuesta es válida de Moodle"""
        # Verificar código de estado
        if response.status_code != 200:
            return False
        
        # Verificar contenido típico de Moodle
        content = response.text.lower()
        moodle_indicators = [
            'moodle',
            'login',
            'sesskey',
            'repository',
            'webservice/pluginfile.php'
        ]
        
        return any(indicator in content for indicator in moodle_indicators)

    def test_connection(self):
        """Test mejorado de conexión a Moodle"""
        try:
            test_url = f"{self.path}login/index.php"
            response = self._make_request('GET', test_url, timeout=15)
            
            # Verificar que es realmente Moodle
            if 'moodle' in response.text.lower() and 'login' in response.text.lower():
                print("✅ Conexión Moodle exitosa")
                return True
            else:
                print("❌ Respuesta no parece ser Moodle")
                return False
                
        except Exception as e:
            print(f"❌ Error de conexión: {e}")
            return False

    def getUserData(self):
        """Obtener datos de usuario via token service"""
        try:
            tokenUrl = self.path + 'login/token.php?service=moodle_mobile_app&username=' + urllib.parse.quote(self.username) + '&password=' + urllib.parse.quote(self.password)
            resp = self._make_request('GET', tokenUrl)
            data = self.parsejson(resp.text)
            
            # Generar token seguro
            if 'token' in data:
                data['s5token'] = S5Crypto.tokenize([self.username, self.password, data['token']])
            else:
                data['s5token'] = S5Crypto.tokenize([self.username, self.password])
                
            return data
        except Exception as e:
            print(f"Error in getUserData: {e}")
            return None

    def getDirectUrl(self, url):
        """Convertir URL normal a URL directa con token"""
        try:
            tokens = str(url).split('/')
            if len(tokens) >= 6:
                direct = self.path + 'webservice/pluginfile.php/' + tokens[4] + '/user/private/' + tokens[-1]
                if self.userdata and 'token' in self.userdata:
                    direct += '?token=' + self.userdata['token']
                return direct
        except:
            pass
        return url

    def getSessKey(self):
        """Obtener clave de sesión de Moodle"""
        try:
            fileurl = self.path + 'my/'
            resp = self._make_request('GET', fileurl)
            soup = BeautifulSoup(resp.text, 'html.parser')
            sesskey = soup.find('input', attrs={'name': 'sesskey'})
            if sesskey:
                return sesskey['value']
        except:
            pass
        return ''

    def login(self):
        """Login mejorado a Moodle con manejo de errores"""
        try:
            print(f"🔐 Intentando login en: {urllib.parse.urlparse(self.path).hostname}")
            
            login_url = self.path + 'login/index.php'
            resp = self._make_request('GET', login_url)
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Extraer tokens necesarios
            logintoken = ''
            try:
                logintoken_input = soup.find('input', attrs={'name': 'logintoken'})
                if logintoken_input:
                    logintoken = logintoken_input['value']
            except:
                pass

            anchor = ''
            try:
                anchor_input = soup.find('input', attrs={'name': 'anchor'})
                if anchor_input:
                    anchor = anchor_input['value']
            except:
                pass

            # Preparar datos de login
            payload = {
                'anchor': anchor,
                'logintoken': logintoken,
                'username': self.username,
                'password': self.password,
                'rememberusername': 1
            }
            
            # Headers específicos para login
            login_headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Referer': login_url,
                'Origin': urllib.parse.urlparse(self.path).scheme + '://' + urllib.parse.urlparse(self.path).hostname
            }
            
            # Realizar login
            resp2 = self._make_request('POST', login_url, data=payload, headers=login_headers)
            
            # Verificar login exitoso
            if self._is_login_successful(resp2):
                print("✅ Login exitoso")
                
                # Obtener userid
                self._extract_user_id(resp2.text)
                
                # Obtener datos de usuario
                self.userdata = self.getUserData()
                
                # Obtener sesskey
                self.sesskey = self.getSessKey()
                
                return True
            else:
                print("❌ Login fallido - Credenciales incorrectas o plataforma no accesible")
                return False
                
        except Exception as ex:
            print(f"❌ Error en login: {ex}")
            return False

    def _is_login_successful(self, response):
        """Verificar si el login fue exitoso"""
        content_lower = response.text.lower()
        
        # Indicadores de login exitoso
        success_indicators = [
            'dashboard',
            'my/home',
            'userid',
            'sesskey'
        ]
        
        # Indicadores de login fallido
        failure_indicators = [
            'loginerrors',
            'invalid login',
            'usuario o contraseña incorrectos',
            'acceso denegado'
        ]
        
        # Verificar éxito
        if any(indicator in content_lower for indicator in success_indicators):
            return True
            
        # Verificar fallo
        if any(indicator in content_lower for indicator in failure_indicators):
            return False
            
        # Por defecto, considerar fallo
        return False

    def _extract_user_id(self, html_content):
        """Extraer user ID de la página de Moodle"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Buscar userid en diferentes ubicaciones
            userid_selectors = [
                'div[data-userid]',
                'a[data-userid]',
                'input[name="userid"]',
                '[data-userid]'
            ]
            
            for selector in userid_selectors:
                element = soup.select_one(selector)
                if element and 'data-userid' in element.attrs:
                    self.userid = element['data-userid']
                    print(f"👤 UserID encontrado: {self.userid}")
                    return
                    
            # Fallback: buscar en scripts
            script_pattern = r'\"userid\"\s*:\s*\"?(\d+)\"?'
            matches = re.findall(script_pattern, html_content)
            if matches:
                self.userid = matches[0]
                print(f"👤 UserID encontrado en script: {self.userid}")
                
        except Exception as e:
            print(f"⚠️ No se pudo extraer userid: {e}")
            self.userid = ''

    def createEvidence(self, name, desc=''):
        """Crear evidencia de usuario"""
        try:
            evidenceurl = self.path + 'admin/tool/lp/user_evidence_edit.php?userid=' + self.userid
            resp = self._make_request('GET', evidenceurl)
            soup = BeautifulSoup(resp.text, 'html.parser')

            # Obtener sesskey si no está disponible
            if not self.sesskey:
                self.sesskey = self.getSessKey()

            # Extraer itemid del objeto
            query = self.extractQuery(soup.find('object')['data'])
            files = query['itemid']

            saveevidence = self.path + 'admin/tool/lp/user_evidence_edit.php?id=&userid=' + self.userid + '&return='
            payload = {
                'userid': self.userid,
                'sesskey': self.sesskey,
                '_qf__tool_lp_form_user_evidence': 1,
                'name': name,
                'description[text]': desc,
                'description[format]': 1,
                'url': '',
                'files': files,
                'submitbutton': 'Guardar cambios'
            }
            
            resp = self._make_request('POST', saveevidence, data=payload)

            # Extraer ID de evidencia
            evidenceid = str(resp.url).split('?')[1].split('=')[1]

            return {'name': name, 'desc': desc, 'id': evidenceid, 'url': resp.url, 'files': []}
            
        except Exception as e:
            print(f"Error creating evidence: {e}")
            return None

    def createBlog(self, name, itemid, desc="<p dir='ltr' style='text-align: left;'>Contenido del blog</p>"):
        """Crear entrada de blog"""
        try:
            post_attach = f'{self.path}blog/edit.php?action=add&userid=' + self.userid
            resp = self._make_request('GET', post_attach)
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            attachment_filemanager = soup.find('input', {'id': 'id_attachment_filemanager'})['value']
            post_url = f'{self.path}blog/edit.php'
            
            payload = {
                'action': 'add',
                'entryid': '',
                'modid': 0,
                'courseid': 0,
                'sesskey': self.sesskey,
                '_qf__blog_edit_form': 1,
                'mform_isexpanded_id_general': 1,
                'mform_isexpanded_id_tagshdr': 1,
                'subject': name,
                'summary_editor[text]': desc,
                'summary_editor[format]': 1,
                'summary_editor[itemid]': itemid,
                'attachment_filemanager': attachment_filemanager,
                'publishstate': 'site',
                'tags': '_qf__force_multiselect_submission',
                'submitbutton': 'Guardar cambios'
            }
            
            resp = self._make_request('POST', post_url, data=payload)
            return resp
            
        except Exception as e:
            print(f"Error creating blog: {e}")
            return None

    def saveEvidence(self, evidence):
        """Guardar evidencia existente"""
        try:
            evidenceurl = self.path + 'admin/tool/lp/user_evidence_edit.php?id=' + evidence['id'] + '&userid=' + self.userid + '&return=list'
            resp = self._make_request('GET', evidenceurl)
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            sesskey = soup.find('input', attrs={'name': 'sesskey'})['value']
            files = evidence['files']
            
            saveevidence = self.path + 'admin/tool/lp/user_evidence_edit.php?id=' + evidence['id'] + '&userid=' + self.userid + '&return=list'
            payload = {
                'userid': self.userid,
                'sesskey': sesskey,
                '_qf__tool_lp_form_user_evidence': 1,
                'name': evidence['name'],
                'description[text]': evidence['desc'],
                'description[format]': 1,
                'url': '',
                'files': files,
                'submitbutton': 'Guardar cambios'
            }
            
            resp = self._make_request('POST', saveevidence, data=payload)
            return evidence
            
        except Exception as e:
            print(f"Error saving evidence: {e}")
            return evidence

    def getEvidences(self):
        """Obtener lista de evidencias del usuario"""
        try:
            evidencesurl = self.path + 'admin/tool/lp/user_evidence_list.php?userid=' + self.userid
            resp = self._make_request('GET', evidencesurl)
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            nodes = soup.find_all('tr', {'data-region': 'user-evidence-node'})
            evidence_list = []
            
            for n in nodes:
                nodetd = n.find_all('td')
                evurl = nodetd[0].find('a')['href']
                evname = n.find('a').text.strip()
                evid = evurl.split('?')[1].split('=')[1]
                
                nodefiles = nodetd[1].find_all('a')
                nfilelist = []
                
                for f in nodefiles:
                    url = str(f['href'])
                    directurl = self.getDirectUrl(url)
                    
                    nfilelist.append({
                        'name': f.text.strip(),
                        'url': url,
                        'directurl': directurl
                    })
                
                evidence_list.append({
                    'name': evname,
                    'desc': '',
                    'id': evid,
                    'url': evurl,
                    'files': nfilelist
                })
                
            return evidence_list
            
        except Exception as e:
            print(f"Error getting evidences: {e}")
            return []

    def deleteEvidence(self, evidence):
        """Eliminar evidencia"""
        try:
            evidencesurl = self.path + 'admin/tool/lp/user_evidence_edit.php?userid=' + self.userid
            resp = self._make_request('GET', evidencesurl)
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            sesskey = soup.find('input', attrs={'name': 'sesskey'})['value']
            deleteUrl = self.path + 'lib/ajax/service.php?sesskey=' + sesskey + '&info=core_competency_delete_user_evidence,tool_lp_data_for_user_evidence_list_page'
            
            savejson = [
                {"index": 0, "methodname": "core_competency_delete_user_evidence", "args": {"id": evidence['id']}},
                {"index": 1, "methodname": "tool_lp_data_for_user_evidence_list_page", "args": {"userid": self.userid}}
            ]
            
            headers = {
                'Content-type': 'application/json',
                'Accept': 'application/json, text/javascript, */*; q=0.01',
            }
            
            resp = self._make_request('POST', deleteUrl, json=savejson, headers=headers)
            return True
            
        except Exception as e:
            print(f"Error deleting evidence: {e}")
            return False

    def _upload_file_generic(self, file, itemid=None, progressfunc=None, args=(), tokenize=False, upload_type='evidence'):
        """Método genérico mejorado para subida de archivos"""
        try:
            # Determinar URL según tipo de subida
            if upload_type == 'evidence':
                fileurl = self.path + 'admin/tool/lp/user_evidence_edit.php?userid=' + self.userid
            elif upload_type == 'blog':
                fileurl = self.path + 'blog/edit.php?action=add&userid=' + self.userid
            elif upload_type == 'draft':
                fileurl = f'{self.path}user/files.php'
            elif upload_type == 'calendario':
                fileurl = f'{self.path}calendar/managesubscriptions.php'
            else:
                fileurl = self.path + 'admin/tool/lp/user_evidence_edit.php?userid=' + self.userid

            # Obtener página de upload
            resp = self._make_request('GET', fileurl)
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Obtener sesskey
            sesskey = self.sesskey
            if not sesskey:
                sesskey_input = soup.find('input', attrs={'name': 'sesskey'})
                if sesskey_input:
                    sesskey = sesskey_input['value']
                else:
                    sesskey = self.getSessKey()
            
            # Extraer parámetros del objeto
            query = self.extractQuery(soup.find('object', attrs={'type': 'text/html'})['data'])
            client_id = self.getclientid(resp.text)

            itempostid = query['itemid']
            if itemid:
                itempostid = itemid

            # Preparar upload
            of = open(file, 'rb')
            boundary = uuid.uuid4().hex
            
            try:
                areamaxbyttes = query.get('areamaxbytes', '-1')
                if areamaxbyttes == '0':
                    areamaxbyttes = '-1'
            except:
                areamaxbyttes = '-1'

            # Datos del upload
            upload_data = {
                'title': (None, ''),
                'author': (None, 'Academic User'),
                'license': (None, 'allrightsreserved'),
                'itemid': (None, itempostid),
                'repo_id': (None, str(self.repo_id)),
                'p': (None, ''),
                'page': (None, ''),
                'env': (None, query['env']),
                'sesskey': (None, sesskey),
                'client_id': (None, client_id),
                'maxbytes': (None, query['maxbytes']),
                'areamaxbytes': (None, areamaxbyttes),
                'ctx_id': (None, query['ctx_id']),
                'savepath': (None, '/')
            }
            
            upload_file = {
                'repo_upload_file': (os.path.basename(file), of, 'application/octet-stream'),
                **upload_data
            }
            
            # Realizar upload
            post_file_url = self.path + 'repository/repository_ajax.php?action=upload'
            
            encoder = rt.MultipartEncoder(upload_file, boundary=boundary)
            progrescall = CallingUpload(progressfunc, file, args)
            callback = partial(progrescall)
            monitor = MultipartEncoderMonitor(encoder, callback=callback)
            
            upload_headers = {
                "Content-Type": "multipart/form-data; boundary=" + boundary,
                "X-Requested-With": "XMLHttpRequest",
                "Referer": fileurl
            }
            
            resp2 = self._make_request('POST', post_file_url, data=monitor, headers=upload_headers)
            of.close()

            # Procesar respuesta
            data = self.parsejson(resp2.text)
            data['url'] = str(data['url']).replace('\\', '')
            data['normalurl'] = data['url']
            
            # Aplicar tokenización si es necesario
            if self.userdata:
                if 'token' in self.userdata and not tokenize:
                    # Convertir a URL de webservice
                    data['url'] = str(data['url']).replace('pluginfile.php/', 'webservice/pluginfile.php/')
                    if 'token=' not in data['url']:
                        data['url'] += '?token=' + self.userdata['token']
                if tokenize:
                    data['url'] = self.host_tokenize + S5Crypto.encrypt(data['url']) + '/' + self.userdata['s5token']

            return itempostid, data
            
        except Exception as e:
            print(f"Error in _upload_file_generic: {e}")
            return None, None

    # Métodos específicos de upload
    def upload_file(self, file, evidence=None, itemid=None, progressfunc=None, args=(), tokenize=False):
        return self._upload_file_generic(file, itemid, progressfunc, args, tokenize, 'evidence')

    def upload_file_blog(self, file, blog=None, itemid=None, progressfunc=None, args=(), tokenize=False):
        return self._upload_file_generic(file, itemid, progressfunc, args, tokenize, 'blog')

    def upload_file_draft(self, file, progressfunc=None, args=(), tokenize=False):
        return self._upload_file_generic(file, None, progressfunc, args, tokenize, 'draft')

    def upload_file_calendar(self, file, progressfunc=None, args=(), tokenize=False):
        return self._upload_file_generic(file, None, progressfunc, args, tokenize, 'calendario')

    def parsejson(self, json_text):
        """Parsear JSON de respuesta de Moodle"""
        data = {}
        try:
            # Limpiar y parsear JSON
            json_text = json_text.strip()
            if json_text.startswith('{') and json_text.endswith('}'):
                data = json.loads(json_text)
            else:
                # Fallback: parsing manual
                tokens = str(json_text).replace('{', '').replace('}', '').split(',')
                for t in tokens:
                    split = str(t).split(':', 1)
                    if len(split) == 2:
                        key = str(split[0]).replace('"', '').strip()
                        value = str(split[1]).replace('"', '').strip()
                        data[key] = value
        except Exception as e:
            print(f"Error parsing JSON: {e}")
        return data

    def getclientid(self, html):
        """Extraer client_id del HTML"""
        try:
            index = str(html).index('client_id')
            max_len = 25
            ret = html[index:(index + max_len)]
            return str(ret).replace('client_id":"', '').replace('"', '')
        except:
            return ''

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
                    else:
                        retQuery[qspl[0]] = None
        except Exception as e:
            print(f"Error extracting query: {e}")
        return retQuery

    def getFiles(self):
        """Obtener archivos del usuario"""
        try:
            urlfiles = self.path + 'user/files.php'
            resp = self._make_request('GET', urlfiles)
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            sesskey = soup.find('input', attrs={'name': 'sesskey'})['value']
            client_id = self.getclientid(resp.text)
            filepath = '/'
            
            query = self.extractQuery(soup.find('object', attrs={'type': 'text/html'})['data'])
            
            payload = {
                'sesskey': sesskey,
                'client_id': client_id,
                'filepath': filepath,
                'itemid': query['itemid']
            }
            
            postfiles = self.path + 'repository/draftfiles_ajax.php?action=list'
            resp = self._make_request('POST', postfiles, data=payload)
            
            file_data = json.loads(resp.text)
            return file_data['list']
            
        except Exception as e:
            print(f"Error getting files: {e}")
            return []

    def logout(self):
        """Cerrar sesión en Moodle"""
        try:
            if self.sesskey:
                logouturl = self.path + 'login/logout.php?sesskey=' + self.sesskey
                self._make_request('POST', logouturl)
                print("✅ Sesión cerrada correctamente")
        except Exception as e:
            print(f"Error logging out: {e}")

    def get_connection_info(self):
        """Obtener información de conexión actual"""
        return {
            'host': self.path,
            'user': self.username,
            'proxy': self.current_proxy_url,
            'userid': self.userid,
            'platform': urllib.parse.urlparse(self.path).hostname
        }
