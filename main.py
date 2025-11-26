from pyobigram.utils import sizeof_fmt, get_file_size, createID, nice_time
from pyobigram.client import ObigramClient, inlineQueryResultArticle
from MoodleClient import MoodleClient

from JDatabase import JsonDatabase
import zipfile
import os
import infos
import xdlink
import mediafire
import datetime
import time
import youtube
import NexCloudClient

from pydownloader.downloader import Downloader
from ProxyCloud import ProxyCloud
import ProxyCloud
import socket
import S5Crypto
import threading
import random

class SmartAcademicBridge:
    def __init__(self):
        self.platforms = {
            'eva': {
                'host': 'https://eva.uo.edu.cu/',
                'user': 'eric.serrano',
                'password': 'Rulebreaker2316',
                'repo_id': 4,
                'upload_type': 'draft'
            },
            'cursos': {
                'host': 'https://cursos.uo.edu.cu/', 
                'user': 'eric.serrano',
                'password': 'Rulebreaker2316',
                'repo_id': 4,
                'upload_type': 'draft'
            },
            'cened': {
                'host': 'https://aulacened.uci.cu/',
                'user': 'eliel21',
                'password': 'ElielThali2115.',
                'repo_id': 5,
                'upload_type': 'draft'
            }
        }
        
        self.strategy_priority = [
            'direct_upload',
            'cross_platform_link',
            'mirror_upload', 
            'url_resource'
        ]
        
        self.performance_stats = {}
        self.platform_status = {}

    def analyze_platform_access(self):
        """Analizar acceso a cada plataforma y determinar estrategia óptima"""
        print("🔍 Analizando acceso a plataformas...")
        
        access_report = {}
        
        for platform_name, config in self.platforms.items():
            try:
                # 🚨 CONEXIÓN DIRECTA - SIN PROXY
                client = MoodleClient(
                    config['user'],
                    config['password'], 
                    config['host'],
                    config['repo_id']
                )
                
                # Test de conexión rápida
                start_time = time.time()
                can_login = client.login()
                response_time = time.time() - start_time
                
                access_report[platform_name] = {
                    'accessible': can_login,
                    'response_time': response_time,
                    'client': client if can_login else None
                }
                
                status = "✅" if can_login else "❌"
                print(f"  {status} {platform_name}: {response_time:.2f}s")
                
            except Exception as e:
                access_report[platform_name] = {
                    'accessible': False,
                    'error': str(e),
                    'response_time': float('inf')
                }
                print(f"  ❌ {platform_name}: Error - {e}")
        
        self.platform_status = access_report
        return access_report

    def get_optimal_strategy(self, target_platform):
        """Determinar la mejor estrategia basada en el análisis"""
        if not self.platform_status:
            self.analyze_platform_access()
        
        target_platform = self._identify_platform(target_platform)
        if not target_platform:
            return None
        
        print(f"🎯 Objetivo detectado: {target_platform}")
        
        # ¿La plataforma objetivo es accesible directamente?
        if (target_platform in self.platform_status and 
            self.platform_status[target_platform]['accessible']):
            print("✅ Estrategia: Subida DIRECTA")
            return {
                'strategy': 'direct_upload',
                'target_platform': target_platform,
                'confidence': 'high'
            }
        
        # Buscar plataforma puente óptima
        bridge_candidates = []
        for platform, status in self.platform_status.items():
            if platform != target_platform and status['accessible']:
                bridge_candidates.append({
                    'platform': platform,
                    'response_time': status['response_time'],
                    'client': status['client']
                })
        
        # Ordenar por velocidad (más rápido primero)
        bridge_candidates.sort(key=lambda x: x['response_time'])
        
        if bridge_candidates:
            best_bridge = bridge_candidates[0]
            print(f"🎯 Mejor puente: {best_bridge['platform']} ({best_bridge['response_time']:.2f}s)")
            
            # Seleccionar estrategia basada en combinación plataformas
            strategy = self._select_strategy_for_pair(best_bridge['platform'], target_platform)
            return {
                'strategy': strategy,
                'bridge_platform': best_bridge['platform'],
                'target_platform': target_platform,
                'bridge_client': best_bridge['client'],
                'confidence': 'high' if best_bridge['response_time'] < 5 else 'medium'
            }
        
        print("❌ No hay estrategia disponible")
        return None

    def _select_strategy_for_pair(self, bridge_platform, target_platform):
        """Seleccionar estrategia óptima para par de plataformas"""
        strategy_map = {
            ('cened', 'eva'): 'cross_platform_link',
            ('cened', 'cursos'): 'mirror_upload', 
            ('eva', 'cursos'): 'cross_platform_link',
            ('cursos', 'eva'): 'cross_platform_link'
        }
        
        return strategy_map.get((bridge_platform, target_platform), 'cross_platform_link')

    def smart_upload(self, file_path, target_platform_url, progressfunc=None, args=(), tokenize=False, upload_type='evidence'):
        """Subida inteligente con estrategia automática - VERSIÓN CORREGIDA"""
        try:
            # Obtener estrategia óptima
            strategy_plan = self.get_optimal_strategy(target_platform_url)
            
            if not strategy_plan:
                return {'error': 'No hay estrategia disponible para esta plataforma'}
            
            print(f"🚀 Ejecutando estrategia: {strategy_plan['strategy']}")
            
            # Ejecutar estrategia seleccionada
            if strategy_plan['strategy'] == 'direct_upload':
                return self._execute_direct_upload(file_path, strategy_plan, progressfunc, args)
            elif strategy_plan['strategy'] == 'cross_platform_link':
                return self._execute_cross_platform_link(file_path, strategy_plan, progressfunc, args)
            elif strategy_plan['strategy'] == 'mirror_upload':
                return self._execute_mirror_upload(file_path, strategy_plan, progressfunc, args)
            elif strategy_plan['strategy'] == 'url_resource':
                return self._execute_url_resource(file_path, strategy_plan, progressfunc, args)
            else:
                return {'error': f'Estrategia no implementada: {strategy_plan["strategy"]}'}
                
        except Exception as e:
            print(f"❌ Error en smart_upload: {e}")
            return {'error': str(e)}

    def _execute_direct_upload(self, file_path, strategy_plan, progressfunc=None, args=()):
        """Estrategia 1: Subida directa (si la plataforma es accesible)"""
        try:
            target_platform = strategy_plan['target_platform']
            config = self.platforms[target_platform]
            
            # 🚨 CONEXIÓN DIRECTA - SIN PROXY
            client = MoodleClient(
                config['user'],
                config['password'],
                config['host'], 
                config['repo_id']
            )
            
            if client.login():
                result = client.upload_file_draft(
                    file_path,
                    progressfunc=progressfunc,
                    args=args
                )
                
                if result and len(result) >= 2:
                    itemid, filedata = result
                    if filedata and 'url' in filedata:
                        return {
                            'strategy': 'direct_upload',
                            'platform': target_platform,
                            'url': filedata['url'],
                            'efficiency': 'high',
                            'message': f'✅ Subida directa a {target_platform.upper()}',
                            'success': True,
                            'filedata': filedata
                        }
                    else:
                        return {'error': 'No se obtuvo URL del archivo'}
                else:
                    return {'error': 'Estructura de resultado inválida'}
                    
        except Exception as e:
            print(f"Direct upload failed: {e}")
            
        return {'error': 'Subida directa fallida'}

    def _execute_cross_platform_link(self, file_path, strategy_plan, progressfunc=None, args=()):
        """Estrategia 2: Enlace cruzado entre plataformas"""
        try:
            bridge_platform = strategy_plan['bridge_platform']
            target_platform = strategy_plan['target_platform']
            
            # 1. Subir a plataforma puente (CENED)
            bridge_config = self.platforms[bridge_platform]
            
            # 🚨 CONEXIÓN DIRECTA - SIN PROXY
            bridge_client = MoodleClient(
                bridge_config['user'],
                bridge_config['password'],
                bridge_config['host'],
                bridge_config['repo_id']
            )
            
            if bridge_client.login():
                bridge_result = bridge_client.upload_file_draft(
                    file_path,
                    progressfunc=progressfunc,
                    args=args
                )
                
                if bridge_result and len(bridge_result) >= 2:
                    itemid, bridge_filedata = bridge_result
                    if bridge_filedata and 'url' in bridge_filedata:
                        bridge_url = bridge_filedata['url']
                        
                        # 2. Crear página de enlace en plataforma objetivo
                        link_page = self._create_link_page(file_path, bridge_url, bridge_platform)
                        temp_html = f"temp_link_{os.path.basename(file_path)}.html"
                        
                        with open(temp_html, 'w', encoding='utf-8') as f:
                            f.write(link_page)
                        
                        # 3. Subir página de enlace a plataforma objetivo
                        target_config = self.platforms[target_platform]
                        
                        # 🚨 CONEXIÓN DIRECTA - SIN PROXY
                        target_client = MoodleClient(
                            target_config['user'],
                            target_config['password'], 
                            target_config['host'],
                            target_config['repo_id']
                        )
                        
                        target_upload_success = False
                        target_url = None
                        
                        if target_client.login():
                            target_result = target_client.upload_file_draft(temp_html)
                            if target_result and len(target_result) >= 2:
                                target_itemid, target_filedata = target_result
                                if target_filedata and 'url' in target_filedata:
                                    target_url = target_filedata['url']
                                    target_upload_success = True
                        
                        # Limpiar archivo temporal
                        try:
                            os.unlink(temp_html)
                        except: pass
                        
                        return {
                            'strategy': 'cross_platform_link',
                            'bridge_platform': bridge_platform,
                            'target_platform': target_platform, 
                            'bridge_url': bridge_url,
                            'target_url': target_url,
                            'target_success': target_upload_success,
                            'efficiency': 'high' if target_upload_success else 'medium',
                            'message': f'🔗 Enlace {bridge_platform.upper()} → {target_platform.upper()}',
                            'success': True,
                            'bridge_filedata': bridge_filedata
                        }
                    
        except Exception as e:
            print(f"Cross-platform link failed: {e}")
            
        return {'error': 'Enlace cruzado fallido'}

    def _execute_mirror_upload(self, file_path, strategy_plan, progressfunc=None, args=()):
        """Estrategia 3: Espejo entre plataformas (subir a ambas)"""
        try:
            bridge_platform = strategy_plan['bridge_platform']
            target_platform = strategy_plan['target_platform']
            
            # Subir a plataforma puente (siempre funciona - CENED)
            bridge_config = self.platforms[bridge_platform]
            
            # 🚨 CONEXIÓN DIRECTA - SIN PROXY
            bridge_client = MoodleClient(
                bridge_config['user'],
                bridge_config['password'],
                bridge_config['host'],
                bridge_config['repo_id']
            )
            
            bridge_url = None
            if bridge_client.login():
                bridge_result = bridge_client.upload_file_draft(
                    file_path,
                    progressfunc=progressfunc,
                    args=args
                )
                
                if bridge_result and len(bridge_result) >= 2:
                    itemid, bridge_filedata = bridge_result
                    if bridge_filedata and 'url' in bridge_filedata:
                        bridge_url = bridge_filedata['url']
            
            # Intentar subir a plataforma objetivo (puede fallar)
            target_url = None
            target_success = False
            target_config = self.platforms[target_platform]
            
            # 🚨 CONEXIÓN DIRECTA - SIN PROXY
            target_client = MoodleClient(
                target_config['user'],
                target_config['password'],
                target_config['host'],
                target_config['repo_id']
            )
            
            if target_client.login():
                target_result = target_client.upload_file_draft(file_path)
                if target_result and len(target_result) >= 2:
                    target_itemid, target_filedata = target_result
                    if target_filedata and 'url' in target_filedata:
                        target_url = target_filedata['url']
                        target_success = True
            
            return {
                'strategy': 'mirror_upload',
                'bridge_platform': bridge_platform,
                'target_platform': target_platform,
                'bridge_url': bridge_url,
                'target_url': target_url,
                'target_success': target_success,
                'efficiency': 'high' if target_success else 'medium',
                'message': f'🪞 Espejo: {bridge_platform.upper}' + (f' + {target_platform.upper()}' if target_success else ' (solo bridge)'),
                'success': True
            }
            
        except Exception as e:
            print(f"Mirror upload failed: {e}")
            
        return {'error': 'Espejo fallido'}

    def _execute_url_resource(self, file_path, strategy_plan, progressfunc=None, args=()):
        """Estrategia 4: Recurso URL"""
        try:
            bridge_platform = strategy_plan['bridge_platform']
            target_platform = strategy_plan['target_platform']
            
            # Subir a plataforma puente
            bridge_config = self.platforms[bridge_platform]
            
            # 🚨 CONEXIÓN DIRECTA - SIN PROXY
            bridge_client = MoodleClient(
                bridge_config['user'],
                bridge_config['password'],
                bridge_config['host'],
                bridge_config['repo_id']
            )
            
            if bridge_client.login():
                bridge_result = bridge_client.upload_file_draft(
                    file_path,
                    progressfunc=progressfunc,
                    args=args
                )
                
                if bridge_result and len(bridge_result) >= 2:
                    itemid, bridge_filedata = bridge_result
                    if bridge_filedata and 'url' in bridge_filedata:
                        bridge_url = bridge_filedata['url']
                        
                        return {
                            'strategy': 'url_resource',
                            'bridge_platform': bridge_platform,
                            'target_platform': target_platform,
                            'bridge_url': bridge_url,
                            'efficiency': 'medium',
                            'message': f'📎 Recurso URL en {bridge_platform.upper()}',
                            'success': True,
                            'filedata': bridge_filedata
                        }
                    
        except Exception as e:
            print(f"URL resource failed: {e}")
            
        return {'error': 'Recurso URL fallido'}

    def _create_link_page(self, file_path, bridge_url, bridge_platform):
        """Crear página HTML con enlace elegante"""
        filename = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        size_mb = file_size / (1024 * 1024)
        
        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Archivo: {filename}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
        .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ border-bottom: 2px solid #007cba; padding-bottom: 15px; margin-bottom: 25px; }}
        .download-btn {{ display: inline-block; background: #007cba; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold; margin: 10px; }}
        .info {{ background: #e7f3ff; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .platform-badge {{ background: #28a745; color: white; padding: 5px 10px; border-radius: 3px; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📁 {filename}</h1>
            <p>Archivo disponible a través de <span class="platform-badge">{bridge_platform.upper()}</span></p>
        </div>
        
        <div class="info">
            <p><strong>📊 Tamaño:</strong> {size_mb:.2f} MB</p>
            <p><strong>🔗 Plataforma:</strong> {bridge_platform.upper()}</p>
            <p><strong>📅 Generado:</strong> {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
        </div>
        
        <div style="text-align: center; margin: 30px 0;">
            <a href="{bridge_url}" class="download-btn" target="_blank">⬇️ Descargar desde {bridge_platform.upper()}</a>
        </div>
        
        <p style="text-align: center; color: #666; font-size: 14px;">
            Este archivo está hospedado en la plataforma {bridge_platform.upper()} y es accesible desde este enlace.
        </p>
    </div>
</body>
</html>"""

    def _identify_platform(self, url):
        """Identificar plataforma basado en URL"""
        if not url:
            return None
        if 'eva.uo.edu.cu' in url:
            return 'eva'
        elif 'cursos.uo.edu.cu' in url:
            return 'cursos'
        elif 'aulacened.uci.cu' in url:
            return 'cened'
        else:
            return None

    def get_strategy_report(self):
        """Generar reporte de estrategias y rendimiento"""
        if not self.platform_status:
            self.analyze_platform_access()
        
        report = "📊 **Reporte de Estrategias Académicas**\n\n"
        
        for platform, status in self.platform_status.items():
            icon = "✅" if status['accessible'] else "❌"
            time_str = f"{status['response_time']:.2f}s" if status['accessible'] else "NO ACCESIBLE"
            report += f"{icon} **{platform.upper()}**: {time_str}\n"
        
        return report

def create_progress_bar(percentage, bars=15):
    """Crea barra de progreso estilo S1 con ⬢⬡"""
    filled = int(percentage / 100 * bars)
    empty = bars - filled
    return "⬢" * filled + "⬡" * empty

def format_s1_message(title, items):
    """Crea mensaje con formato S1"""
    message = f"╭━━━━❰{title}❱━➣\n"
    for item in items:
        message += f"┣⪼ {item}\n"
    message += "╰━━━━━━━━━━━━━━━➣"
    return message

def format_time(seconds):
    """Formatea el tiempo en formato minutos:segundos (00:00)"""
    if seconds <= 0:
        return "00:00"
    
    try:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        
        if minutes > 99:
            hours = minutes // 60
            remaining_minutes = minutes % 60
            return f"{hours:02d}:{remaining_minutes:02d}+"
        
        return f"{minutes:02d}:{secs:02d}"
    except:
        return "00:00"

def downloadFile(downloader, filename, currentBits, totalBits, speed, time_elapsed, args):
    try:
        bot = args[0]
        message = args[1]
        thread = args[2]
        if thread.getStore('stop'):
            downloader.stop()
            return
            
        downloadingInfo = ''
        if totalBits == 0:
            percentage = 0
        else:
            percentage = (currentBits / totalBits) * 100
        
        progress_bar = create_progress_bar(percentage, 15)
        
        total_mb = totalBits / (1024 * 1024)
        current_mb = currentBits / (1024 * 1024)
        speed_mb = speed / (1024 * 1024) if speed > 0 else 0
        
        if speed > 0 and totalBits > currentBits:
            remaining_bits = totalBits - currentBits
            remaining_time = remaining_bits / speed
            eta_formatted = format_time(remaining_time)
        else:
            eta_formatted = "Calculando..."
        
        downloadingInfo = format_s1_message("📥 Descargando", [
            f"[{progress_bar}]",
            f"✅ Progreso: {percentage:.1f}%",
            f"📦 Tamaño: {current_mb:.1f}/{total_mb:.1f} MB",
            f"⚡ Velocidad: {speed_mb:.1f} MB/s",
            f"⏳ Tiempo: {eta_formatted}",
            f"🚫 Cancelar: /cancel_{thread.cancel_id}"
        ])
            
        bot.editMessageText(message, downloadingInfo)
        
    except Exception as ex: 
        print(str(ex))
    pass

def uploadFile(filename, currentBits, totalBits, speed, time_elapsed, args):
    try:
        bot = args[0]
        message = args[1]
        originalfile = args[2]
        thread = args[3]
        if thread.getStore('stop'):
            return
            
        part_info = args[4] if len(args) > 4 else None
        
        uploadingInfo = ''
        if totalBits == 0:
            percentage = 0
        else:
            percentage = (currentBits / totalBits) * 100
            
        progress_bar = create_progress_bar(percentage, 15)
        
        total_mb = totalBits / (1024 * 1024)
        current_mb = currentBits / (1024 * 1024)
        speed_mb = speed / (1024 * 1024) if speed > 0 else 0
        
        if speed > 0 and totalBits > currentBits:
            remaining_bits = totalBits - currentBits
            remaining_time = remaining_bits / speed
            eta_formatted = format_time(remaining_time)
        else:
            eta_formatted = "Calculando..."
        
        file_display = filename
        if part_info:
            current_part, total_parts, original_name = part_info
            file_display = f"{original_name} (Parte {current_part}/{total_parts})"
        elif originalfile:
            file_display = originalfile
        
        uploadingInfo = format_s1_message("📤 Subiendo", [
            f"[{progress_bar}]",
            f"✅ Progreso: {percentage:.1f}%",
            f"📦 Tamaño: {current_mb:.1f}/{total_mb:.1f} MB",
            f"⚡ Velocidad: {speed_mb:.1f} MB/s",
            f"⏳ Tiempo: {eta_formatted}",
            f"📄 Archivo: {file_display}"
        ])
            
        bot.editMessageText(message, uploadingInfo)
                
    except Exception as ex: 
        print(str(ex))
    pass

def processUploadFiles(filename, filesize, files, update, bot, message, thread=None, jdb=None):
    try:
        bot.editMessageText(message,'<b>🎯 Iniciando estrategia inteligente...</b>', parse_mode='HTML')
        user_info = jdb.get_user(update.message.sender.username)
        cloudtype = user_info['cloudtype']
        
        if cloudtype == 'moodle':
            # 🎯 USAR ESTRATEGIA INTELIGENTE
            smart_bridge = SmartAcademicBridge()
            
            results = []
            for i, file in enumerate(files):
                if thread and thread.getStore('stop'):
                    break
                    
                print(f"📦 Procesando archivo {i+1}/{len(files)}: {os.path.basename(file)}")
                
                # Ejecutar estrategia inteligente
                result = smart_bridge.smart_upload(
                    file,
                    user_info['moodle_host'],
                    progressfunc=uploadFile,
                    args=(bot, message, filename, thread, (i+1, len(files), filename))
                )
                
                print(f"🔍 Resultado estrategia: {result}")
                
                if result and result.get('success'):
                    results.append(result)
                    print(f"✅ Éxito con estrategia: {result.get('strategy')}")
                else:
                    print(f"❌ Estrategia falló, intentando subida directa...")
                    # Subida directa de emergencia
                    direct_result = _emergency_direct_upload(file, user_info, uploadFile, 
                                                           (bot, message, filename, thread, (i+1, len(files), filename)))
                    if direct_result:
                        results.append(direct_result)
                        print("✅ Subida directa exitosa")
                    else:
                        print("❌ Subida directa también falló")
                
                # Limpiar archivo
                try:
                    os.unlink(file)
                    print("🧹 Archivo temporal eliminado")
                except Exception as e:
                    print(f"⚠️ Error eliminando archivo: {e}")
            
            if thread and thread.getStore('stop'):
                return None
                
            print(f"📊 Proceso completado. Resultados: {len(results)}")
            return results
            
        elif cloudtype == 'cloud':
            # Para nube normal, usar método tradicional (pero sin proxy)
            tokenize = False
            if user_info['tokenize']!=0:
               tokenize = True
            bot.editMessageText(message,'<b>☁️ Subiendo archivo...</b>', parse_mode='HTML')
            host = user_info['moodle_host']
            user = user_info['moodle_user']
            passw = user_info['moodle_password']
            remotepath = user_info['dir']
            client = NexCloudClient.NexCloudClient(user,passw,host,proxy=None)
            loged = client.login()
            if not loged:
                bot.editMessageText(message,'<b>❌ Error en la nube</b>', parse_mode='HTML')
                return None
                
            total_parts = len(files)
            filesdata = []
            for i, f in enumerate(files, 1):
                if thread and thread.getStore('stop'):
                    break
                    
                part_info = None
                if total_parts > 1:
                    part_info = (i, total_parts, filename)
                    
                data = client.upload_file(f,path=remotepath,
                                        progressfunc=uploadFile,
                                        args=(bot,message,filename,thread,part_info),
                                        tokenize=tokenize)
                filesdata.append(data)
                os.unlink(f)
                
            if thread and thread.getStore('stop'):
                return None
                
            return filesdata
        return None
    except Exception as ex:
        print(f"❌ Error en processUploadFiles: {ex}")
        bot.editMessageText(message,f'<b>❌ Error</b>\n<code>{str(ex)}</code>', parse_mode='HTML')
        return None

def _emergency_direct_upload(file_path, user_info, progressfunc=None, args=()):
    """Subida directa de emergencia cuando todo falla"""
    try:
        print(f"🆘 SUBIDA DIRECTA DE EMERGENCIA: {os.path.basename(file_path)}")
        
        host = user_info['moodle_host']
        user = user_info['moodle_user']
        password = user_info['moodle_password']
        repo_id = user_info.get('moodle_repo_id', 4)
        
        print(f"🔐 Conectando a: {host}")
        client = MoodleClient(user, password, host, repo_id)
        
        # Test de conexión
        if not client.test_connection():
            print("❌ No se puede conectar a la plataforma")
            return None
            
        print("🔐 Iniciando login...")
        if client.login():
            print("✅ Login exitoso")
            
            # Usar upload_file_draft que ahora debería existir
            print("📤 Iniciando subida...")
            result = client.upload_file_draft(
                file_path,
                progressfunc=progressfunc,
                args=args
            )
            
            print(f"📦 Resultado crudo: {result}")
            
            if result and len(result) >= 2:
                itemid, filedata = result
                if filedata and 'url' in filedata:
                    return {
                        'strategy': 'emergency_direct',
                        'platform': 'direct',
                        'url': filedata['url'],
                        'efficiency': 'medium', 
                        'message': '✅ Subida directa de emergencia',
                        'success': True,
                        'filedata': filedata
                    }
            
            print("❌ Estructura de resultado inválida")
            return None
        else:
            print("❌ Login fallido")
            return None
            
    except Exception as e:
        print(f"❌ Error en subida de emergencia: {e}")
        return None

def processFile(update,bot,message,file,thread=None,jdb=None):
    try:
        file_size = get_file_size(file)
        username = update.message.sender.username
        getUser = jdb.get_user(username)
        
        # CONFIGURAR ZIPS SEGÚN PLATAFORMA
        if getUser['moodle_host'] == 'https://eva.uo.edu.cu/':
            max_file_size = 1024 * 1024 * 99  # 99 MB para EVA
        elif getUser['moodle_host'] == 'https://cursos.uo.edu.cu/':
            max_file_size = 1024 * 1024 * 99  # 99 MB para CURSOS
        else:
            max_file_size = 1024 * 1024 * getUser['zips']  # 100 MB para CENED por defecto
            
        file_upload_count = 0
        client = None
        findex = 0
        
        if thread and thread.getStore('stop'):
            try:
                os.unlink(file)
            except:pass
            return
        
        # Obtener el nombre base del archivo original
        original_filename = file.split('/')[-1] if '/' in file else file
        base_name = original_filename.split('.')[0]
        file_extension = original_filename.split('.')[-1].lower() if '.' in original_filename else ''
        is_compressed_file = file_extension in ['zip', 'rar', '7z', 'tar', 'gz']
            
        if file_size > max_file_size and not is_compressed_file:
            # 🛠️ ARREGLADO: Mejor manejo de compresión
            compresingInfo = infos.createCompresing(file,file_size,max_file_size)
            bot.editMessageText(message,compresingInfo)
            
            try:
                # CREAR ARCHIVO TEMPORAL CON NOMBRE CORRECTO
                temp_dir = "temp_" + createID()
                os.makedirs(temp_dir, exist_ok=True)
                
                # Copiar el archivo a un directorio temporal con su nombre original
                temp_file_path = os.path.join(temp_dir, original_filename)
                import shutil
                shutil.copy2(file, temp_file_path)
                
                zipname = base_name + createID()
                
                # 🛠️ ARREGLADO: Usar zipfile normal
                zip_filename = f"{zipname}.zip"
                
                # Crear ZIP con compresión
                with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    zipf.write(temp_file_path, arcname=original_filename)
                
                # Verificar si el archivo zip necesita división
                zip_size = get_file_size(zip_filename)
                
                if zip_size > max_file_size:
                    # 🛠️ ARREGLADO: Dividir el ZIP si es muy grande
                    bot.editMessageText(message, '<b>📦 Dividiendo archivo comprimido...</b>', parse_mode='HTML')
                    
                    # Leer el contenido del ZIP
                    with open(zip_filename, 'rb') as f:
                        zip_content = f.read()
                    
                    # Dividir en partes
                    part_size = max_file_size
                    total_parts = (len(zip_content) + part_size - 1) // part_size
                    
                    zip_parts = []
                    for i in range(total_parts):
                        part_data = zip_content[i * part_size:(i + 1) * part_size]
                        part_filename = f"{zipname}_part{i+1:03d}.zip"
                        
                        with open(part_filename, 'wb') as part_file:
                            part_file.write(part_data)
                        
                        zip_parts.append(part_filename)
                    
                    # Eliminar el archivo zip original
                    os.unlink(zip_filename)
                    files_to_upload = zip_parts
                    file_upload_count = len(zip_parts)
                    
                else:
                    files_to_upload = [zip_filename]
                    file_upload_count = 1
                
                # LIMPIAR ARCHIVO TEMPORAL
                try:
                    shutil.rmtree(temp_dir)
                except: pass
                
                # 🎯 USAR ESTRATEGIA INTELIGENTE para subir
                client = processUploadFiles(original_filename, file_size, files_to_upload, update, bot, message, thread=thread, jdb=jdb)
                
                try:
                    os.unlink(file)
                except:pass
                
                # 🛠️ ARREGLADO: Limpiar archivos temporales ZIP después de subir
                if 'files_to_upload' in locals():
                    for temp_file in files_to_upload:
                        try:
                            if os.path.exists(temp_file):
                                os.unlink(temp_file)
                        except: pass
                        
            except Exception as e:
                print(f"❌ Error en compresión: {e}")
                bot.editMessageText(message, f'<b>❌ Error al comprimir</b>\n<code>{str(e)}</code>', parse_mode='HTML')
                return
                        
        else:
            # Para archivos pequeños o ya comprimidos
            client = processUploadFiles(original_filename, file_size, [file], update, bot, message, thread=thread, jdb=jdb)
            file_upload_count = 1
            
        if thread and thread.getStore('stop'):
            return
            
        # ACTUALIZAR ESTADÍSTICAS DE USUARIO
        try:
            file_size_mb = file_size / (1024 * 1024)
            current_total = getUser.get('total_mb_used', 0)
            new_total = current_total + file_size_mb
            getUser['total_mb_used'] = new_total
            getUser['last_upload'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            getUser['upload_count'] = getUser.get('upload_count', 0) + 1
            jdb.save_data_user(username, getUser)
            jdb.save()
        except Exception as e:
            print(f"Error actualizando estadísticas: {e}")
            
        bot.editMessageText(message,'<b>📄 Preparando enlaces...</b>', parse_mode='HTML')
        
        # 🎯 PROCESAR RESULTADOS DE ESTRATEGIA INTELIGENTE
        if client and isinstance(client, list) and len(client) > 0:
            # Es un resultado de estrategia bridge
            return _process_bridge_results(client, original_filename, file_size, file_upload_count, update, bot, message, getUser)
        else:
            # Método tradicional
            return _process_traditional_results(client, original_filename, file_size, file_upload_count, update, bot, message, getUser)
            
    except Exception as ex:
        print(f"Error en processFile: {ex}")

def _process_bridge_results(results, original_filename, file_size, file_upload_count, update, bot, message, user_info):
    """Procesar resultados de estrategia bridge - VERSIÓN MEJORADA"""
    try:
        if not results:
            bot.editMessageText(message, "❌ No se obtuvieron resultados de subida")
            return None
            
        successful_results = [r for r in results if r and r.get('success')]
        
        if not successful_results:
            error_msg = "❌ Todas las subidas fallaron\n"
            for i, result in enumerate(results):
                if result and 'error' in result:
                    error_msg += f"\n• Intento {i+1}: {result['error']}"
                else:
                    error_msg += f"\n• Intento {i+1}: Error desconocido"
            
            bot.editMessageText(message, error_msg)
            return None
        
        # Construir mensaje de éxito
        success_count = len(successful_results)
        
        summary_msg = f"""
🎯 **Subida Completada**

📊 **Resumen:**
• 📁 Archivo: {original_filename}
• 📦 Tamaño: {sizeof_fmt(file_size)}
• ✅ Subidas exitosas: {success_count}
• 🎯 Estrategias usadas: {', '.join(set(r.get('strategy', 'desconocida') for r in successful_results))}

🔗 **Enlaces generados:**"""
        
        all_urls = []
        for i, result in enumerate(successful_results):
            result_msg = f"\n\n📄 **Enlace {i+1}:**"
            result_msg += f"\n• 🎯 Método: {result.get('strategy', 'directa')}"
            result_msg += f"\n• 📝 Estado: {result.get('message', 'Completado')}"
            
            # Extraer URL de diferentes formas
            file_url = None
            if 'url' in result:
                file_url = result['url']
            elif 'filedata' in result and 'url' in result['filedata']:
                file_url = result['filedata']['url']
            elif 'bridge_url' in result:
                file_url = result['bridge_url']
            elif 'target_url' in result:
                file_url = result['target_url']
                
            if file_url:
                result_msg += f"\n• 🔗 URL: {file_url}"
                all_urls.append({'name': f"{original_filename} ({result.get('strategy', 'directa')})", 'directurl': file_url})
            else:
                result_msg += f"\n• ❌ No se obtuvo URL"
            
            summary_msg += result_msg
        
        bot.deleteMessage(message.chat.id, message.message_id)
        bot.sendMessage(update.message.chat.id, summary_msg)
        
        # Enviar enlaces en TXT si hay URLs
        if all_urls:
            filesInfo = infos.createFileMsg(original_filename, all_urls)
            bot.sendMessage(update.message.chat.id, filesInfo, parse_mode='html')
            txtname = original_filename.split('.')[0] + '.txt'
            sendTxt(txtname, all_urls, update, bot)
        else:
            bot.sendMessage(update.message.chat.id, "⚠️ No se generaron enlaces descargables")
        
        return successful_results
        
    except Exception as e:
        print(f"❌ Error procesando resultados: {e}")
        bot.editMessageText(message, f"❌ Error al procesar resultados: {str(e)}")
        return None

def _process_traditional_results(client, original_filename, file_size, file_upload_count, update, bot, message, user_info):
    """Procesar resultados tradicionales"""
    try:
        files = []
        if client:
            if user_info['cloudtype'] == 'moodle':
                if user_info['uploadtype'] == 'evidence':
                    try:
                        evidname = original_filename.split('.')[0]
                        evidences = client.getEvidences()
                        for ev in evidences:
                            if ev['name'] == evidname:
                               files = ev['files']
                               break
                        client.logout()
                    except:pass
                if user_info['uploadtype'] == 'draft' or user_info['uploadtype'] == 'blog' or user_info['uploadtype']=='calendario':
                   for draft in client:
                       files.append({'name':draft['file'],'directurl':draft['url']})
            else:
                for data in client:
                    files.append({'name':data['name'],'directurl':data['url']})

            # Aplicar webservice a URLs
            for i in range(len(files)):
                url = files[i]['directurl']
                if 'aulacened.uci.cu' in url:
                    files[i]['directurl'] = url.replace('://aulacened.uci.cu/', '://aulacened.uci.cu/webservice/')
                elif 'eva.uo.edu.cu' in url and '/webservice/' not in url:
                    files[i]['directurl'] = url.replace('://eva.uo.edu.cu/', '://eva.uo.edu.cu/webservice/')
                elif 'cursos.uo.edu.cu' in url and '/webservice/' not in url:
                    files[i]['directurl'] = url.replace('://cursos.uo.edu.cu/', '://cursos.uo.edu.cu/webservice/')

            bot.deleteMessage(message.chat.id,message.message_id)
            
            # Mensaje final
            platform_name = get_platform_name(user_info['moodle_host'])
            finishInfo = format_s1_message("✅ Subida Completada", [
                f"📄 Archivo: {original_filename}",
                f"📦 Tamaño total: {sizeof_fmt(file_size)}",
                f"🔗 Enlaces generados: {len(files)}",
                f"⏱️ Duración enlaces: 3 días",
                f"💾 Partes: {file_upload_count}" if file_upload_count > 1 else "💾 Archivo único"
            ])
            
            bot.sendMessage(message.chat.id, finishInfo)
            
            if len(files) > 0:
                filesInfo = infos.createFileMsg(original_filename,files)
                bot.sendMessage(message.chat.id, filesInfo, parse_mode='html')
                txtname = original_filename.split('.')[0] + '.txt'
                sendTxt(txtname,files,update,bot)
                
        return files
        
    except Exception as e:
        print(f"Error procesando resultados tradicionales: {e}")
        return None

def ddl(update,bot,message,url,file_name='',thread=None,jdb=None):
    try:
        downloader = Downloader()
        thread.cancel_id = createID()
        bot.threads[thread.cancel_id] = thread
        
        file = downloader.download_url(url,progressfunc=downloadFile,args=(bot,message,thread))
        if not downloader.stoping:
            if file:
                processFile(update,bot,message,file,thread=thread,jdb=jdb)
            else:
                bot.editMessageText(message, '<b>❌ Error en la descarga</b>', parse_mode='HTML')
            
        if hasattr(thread, 'cancel_id') and thread.cancel_id in bot.threads:
            del bot.threads[thread.cancel_id]
    except Exception as ex:
        print(f"Error en ddl: {ex}")

def sendTxt(name,files,update,bot):
    try:
        with open(name, 'w', encoding='utf-8') as txt:
            for f in files:
                txt.write(f"{f['directurl']}\n")
        
        info_msg = f"""<b>📄 Archivo de enlaces generado</b>

📎 <b>Nombre:</b> <code>{name}</code>
🔗 <b>Enlaces incluidos:</b> {len(files)}
⏱️ <b>Duración de enlaces:</b> 3 días

⬇️ <b>Descarga el archivo TXT abajo</b>"""
        
        bot.sendFile(update.message.chat.id, name, caption=info_msg, parse_mode='HTML')
        os.unlink(name)
        
    except Exception as ex:
        print(f"Error en sendTxt: {str(ex)}")
        try:
            if os.path.exists(name):
                bot.sendFile(update.message.chat.id, name)
                os.unlink(name)
        except:
            pass

def get_platform_name(host):
    """Obtiene el nombre de la plataforma basado en el host"""
    if 'eva.uo.edu.cu' in host:
        return 'EVA UO'
    elif 'cursos.uo.edu.cu' in host:
        return 'CURSOS UO'
    elif 'aulacened.uci.cu' in host:
        return 'CENED'
    else:
        return 'Personalizada'

def onmessage(update,bot:ObigramClient):
    try:
        thread = bot.this_thread
        username = update.message.sender.username
        tl_admin_user = os.environ.get('tl_admin_user','Eliel_21')

        jdb = JsonDatabase('database')
        jdb.check_create()
        jdb.load()

        user_info = jdb.get_user(username)

        if username == tl_admin_user or tl_admin_user=='*' or user_info:
            if user_info is None:
                if username == tl_admin_user:
                    jdb.create_admin(username)
                else:
                    bot.sendMessage(update.message.chat.id,
                                   "<b>🚫 Acceso Restringido</b>\n\n"
                                   "No tienes acceso a este bot.\n\n"
                                   "📞 <b>Contacta al propietario:</b>\n"
                                   f"👤 @{tl_admin_user}",
                                   parse_mode='HTML')
                    return
                user_info = jdb.get_user(username)
                jdb.save_data_user(username, user_info)
                jdb.save()
        else:
            bot.sendMessage(update.message.chat.id,
                           "<b>🚫 Acceso Restringido</b>\n\n"
                           "No tienes acceso a este bot.\n\n"
                           "📞 <b>Contacta al propietario:</b>\n"
                           f"👤 @{tl_admin_user}",
                           parse_mode='HTML')
            return

        msgText = ''
        try: 
            msgText = update.message.text
        except: 
            msgText = ''

        is_text = msgText != ''
        isadmin = jdb.is_admin(username)

        # 🎯 NUEVOS COMANDOS DE ESTRATEGIA BRIDGE
        if '/bridge_analyze' in msgText:
            smart_bridge = SmartAcademicBridge()
            report = smart_bridge.analyze_platform_access()
            
            report_msg = "🔍 **Análisis de Plataformas**\n\n"
            for platform, status in report.items():
                status_icon = "✅" if status['accessible'] else "❌"
                time_str = f"{status['response_time']:.2f}s" if status['accessible'] else "NO ACCESIBLE"
                report_msg += f"{status_icon} **{platform.upper()}**: {time_str}\n"
            
            report_msg += f"\n🎯 **Recomendación:** Usar estrategia bridge automática"
            bot.sendMessage(update.message.chat.id, report_msg, parse_mode='HTML')
            return

        if '/bridge_strategy' in msgText:
            user_info = jdb.get_user(username)
            smart_bridge = SmartAcademicBridge()
            
            strategy = smart_bridge.get_optimal_strategy(user_info['moodle_host'])
            
            if strategy:
                strategy_msg = f"""
🎯 **Estrategia Recomendada**

**Plataforma objetivo:** {strategy.get('target_platform', 'N/A')}
**Estrategia:** {strategy['strategy']}
**Confianza:** {strategy.get('confidence', 'media').upper()}
"""
                if 'bridge_platform' in strategy:
                    strategy_msg += f"**Plataforma puente:** {strategy['bridge_platform'].upper()}"
            else:
                strategy_msg = "❌ **No hay estrategia disponible** para esta plataforma"
            
            bot.sendMessage(update.message.chat.id, strategy_msg, parse_mode='HTML')
            return

        # COMANDOS DE CONFIGURACIÓN RÁPIDA
        if '/moodle_eva' in msgText and isadmin:
            user_info['moodle_host'] = 'https://eva.uo.edu.cu/'
            user_info['moodle_user'] = 'eric.serrano'
            user_info['moodle_password'] = 'Rulebreaker2316'
            user_info['moodle_repo_id'] = 4
            user_info['uploadtype'] = 'draft'
            user_info['cloudtype'] = 'moodle'
            user_info['zips'] = 99
            jdb.save_data_user(username, user_info)
            jdb.save()
            bot.sendMessage(update.message.chat.id, 
                '<b>✅ Configurado para EVA</b>\n\n'
                '<b>🎯 Estrategia:</b> Bridge automático via CENED',
                parse_mode='HTML')
            return

        if '/moodle_cursos' in msgText and isadmin:
            user_info['moodle_host'] = 'https://cursos.uo.edu.cu/'
            user_info['moodle_user'] = 'eric.serrano'
            user_info['moodle_password'] = 'Rulebreaker2316'
            user_info['moodle_repo_id'] = 4
            user_info['uploadtype'] = 'draft'
            user_info['cloudtype'] = 'moodle'
            user_info['zips'] = 99
            jdb.save_data_user(username, user_info)
            jdb.save()
            bot.sendMessage(update.message.chat.id, 
                '<b>✅ Configurado para CURSOS</b>\n\n'
                '<b>🎯 Estrategia:</b> Bridge automático via CENED',
                parse_mode='HTML')
            return

        if '/moodle_cened' in msgText and isadmin:
            user_info['moodle_host'] = 'https://aulacened.uci.cu/'
            user_info['moodle_user'] = 'eliel21'
            user_info['moodle_password'] = 'ElielThali2115.'
            user_info['moodle_repo_id'] = 5
            user_info['uploadtype'] = 'draft'
            user_info['cloudtype'] = 'moodle'
            user_info['zips'] = 100
            jdb.save_data_user(username, user_info)
            jdb.save()
            bot.sendMessage(update.message.chat.id, 
                '<b>✅ Configurado para CENED</b>\n\n'
                '<b>🎯 Estrategia:</b> Subida directa',
                parse_mode='HTML')
            return

        # BLOQUEAR COMANDOS DE ADMIN PARA USUARIOS NORMALES
        if not isadmin and is_text and any(cmd in msgText for cmd in [
            '/zips', '/account', '/host', '/repoid', '/tokenize', 
            '/cloud', '/uptype', '/proxy', '/dir', '/myuser', 
            '/files', '/txt_', '/del_', '/delall', '/adduserconfig', 
            '/banuser', '/getdb', '/moodle_eva', '/moodle_cursos', '/moodle_cened',
            '/proxy_test', '/proxy_clear', '/confirm_proxy', '/bridge_analyze', '/bridge_strategy'
        ]):
            bot.sendMessage(update.message.chat.id,
                           "<b>🚫 Acceso Restringido</b>\n\n"
                           "Los comandos de configuración están disponibles solo para administradores.\n\n"
                           "<b>✅ Comandos disponibles para ti:</b>\n"
                           "• /start - Información del bot\n"
                           "• /tutorial - Guía de uso completo\n"
                           "• Enlaces HTTP/HTTPS para subir archivos",
                           parse_mode='HTML')
            return

        # MENSAJE PARA TEXTO SIN COMANDOS NI URLS
        if is_text and not msgText.startswith('/') and not 'http' in msgText:
            bot.sendMessage(update.message.chat.id,
                           "<b>🤖 Bot de Subida Inteligente</b>\n\n"
                           "🎯 <b>Características:</b>\n"
                           "• Estrategia bridge automática\n" 
                           "• Sin proxy requerido\n"
                           "• Compatible con EVA/CURSOS/CENED\n\n"
                           "📤 <b>Para subir archivos:</b> Envía un enlace HTTP/HTTPS",
                           parse_mode='HTML')
            return

        message = bot.sendMessage(update.message.chat.id,'<b>🎯 Inicializando estrategia...</b>', parse_mode='HTML')
        thread.store('msg',message)

        if '/start' in msgText:
            platform_name = get_platform_name(user_info.get('moodle_host', ''))
            
            if isadmin:
                welcome_text = f"""╭━━━━❰🤖 Bot Inteligente - ADMIN❱━➣
┣⪼ 🚀 Subidas con Strategy Bridge
┣⪼ 👨‍💻 Desarrollado por: @Eliel_21
┣⪼ 🏫 Plataforma: {platform_name}
┣⪼ 🌐 Conexión: Directa (Sin proxy)
┣⪼ 🎯 Estrategia: Automática
┣⪼ ⏱️ Enlaces: 3 días

┣⪼ 🔍 COMANDOS ANÁLISIS:
┣⪼ /bridge_analyze - Estado plataformas
┣⪼ /bridge_strategy - Estrategia actual

┣⪼ ⚙️ CONFIGURACIÓN RÁPIDA:
┣⪼ /moodle_eva - EVA (vía bridge)
┣⪼ /moodle_cursos - CURSOS (vía bridge)  
┣⪼ /moodle_cened - CENED (directo)

┣⪼ 👥 GESTIÓN DE USUARIOS:
┣⪼ /adduserconfig - Agregar usuarios
┣⪼ /banuser - Eliminar usuarios
┣⪼ /getdb - Base de datos

┣⪼ 📚 COMANDOS GENERALES:
┣⪼ /tutorial - Guía completa
╰━━━━━━━━━━━━━━━➣"""
            else:
                welcome_text = f"""╭━━━━❰🤖 Bot Inteligente❱━➣
┣⪼ 🚀 Subidas con Strategy Bridge  
┣⪼ 👨‍💻 Desarrollado por: @Eliel_21
┣⪼ 🏫 Plataforma: {platform_name}
┣⪼ 🌐 Conexión: Directa
┣⪼ 🎯 Estrategia: Automática
┣⪼ ⏱️ Enlaces: 3 días
┣⪼ 📤 Envía enlaces HTTP/HTTPS

┣⪼ 📝 COMANDOS DISPONIBLES:
┣⪼ /start - Información del bot
┣⪼ /tutorial - Guía completa
╰━━━━━━━━━━━━━━━➣"""
            
            bot.deleteMessage(message.chat.id, message.message_id)
            bot.sendMessage(update.message.chat.id, welcome_text, parse_mode='HTML')
        elif 'http' in msgText:
            url = msgText
            ddl(update,bot,message,url,file_name='',thread=thread,jdb=jdb)
        else:
            bot.editMessageText(message,'<b>❌ No se pudo procesar el mensaje</b>', parse_mode='HTML')
    except Exception as ex:
           print(str(ex))

def start_health_server(port):
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('0.0.0.0', port))
        server_socket.listen(5)
        print(f"✅ Health check server running on port {port}")
        
        while True:
            try:
                client_socket, addr = server_socket.accept()
                request = client_socket.recv(1024).decode('utf-8')
                
                response = "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nBot is running!"
                client_socket.send(response.encode('utf-8'))
                client_socket.close()
            except Exception as e:
                print(f"Health check error: {e}")
                break
                
    except Exception as e:
        print(f"❌ Health server failed: {e}")

def main():
    bot_token = os.environ.get('bot_token')

    bot = ObigramClient(bot_token)
    bot.onMessage(onmessage)
    
    port = int(os.environ.get("PORT", 5000))
    
    health_thread = threading.Thread(target=start_health_server, args=(port,))
    health_thread.daemon = True
    health_thread.start()
    
    print(f"🚀 Bot starting with health check on port {port}")
    print("🎯 Modo: Strategy Bridge System")
    print("🌐 Conexión: Directa (sin proxy)")
    print("🏫 Plataformas: EVA, CURSOS, CENED")
    
    bot.run()

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"❌ Error: {e}")
        time.sleep(5)
        main()
