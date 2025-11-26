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

    def get_optimal_strategy(self, target_platform_url):
        """Estrategia simplificada - Solo mirror_upload para EVA/CURSOS, directa para CENED"""
        target_platform = self._identify_platform(target_platform_url)
        
        if not target_platform:
            return {'error': 'Plataforma no identificada'}
        
        # 🎯 ESTRATEGIA SIMPLE Y EFECTIVA
        if target_platform == 'cened':
            return {
                'strategy': 'direct_upload',
                'target_platform': target_platform,
                'confidence': 'high'
            }
        else:
            # Para EVA y CURSOS, usar siempre mirror_upload con CENED
            return {
                'strategy': 'mirror_upload', 
                'bridge_platform': 'cened',
                'target_platform': target_platform,
                'confidence': 'high'
            }

    def smart_upload(self, file_path, target_platform_url, progressfunc=None, args=(), tokenize=False, upload_type='evidence'):
        """Subida inteligente simplificada"""
        try:
            # Obtener estrategia óptima
            strategy_plan = self.get_optimal_strategy(target_platform_url)
            
            if 'error' in strategy_plan:
                return strategy_plan
            
            print(f"🚀 Ejecutando estrategia: {strategy_plan['strategy']}")
            
            # Ejecutar estrategia seleccionada
            if strategy_plan['strategy'] == 'direct_upload':
                return self._execute_direct_upload(file_path, strategy_plan, progressfunc, args)
            elif strategy_plan['strategy'] == 'mirror_upload':
                return self._execute_mirror_upload(file_path, strategy_plan, progressfunc, args)
            else:
                return {'error': f'Estrategia no implementada: {strategy_plan["strategy"]}', 'success': False}
                
        except Exception as e:
            print(f"❌ Error en smart_upload: {e}")
            return {'error': str(e), 'success': False}

    def _execute_direct_upload(self, file_path, strategy_plan, progressfunc=None, args=()):
        """Subida directa simplificada"""
        try:
            target_platform = strategy_plan['target_platform']
            config = self.platforms[target_platform]
            
            print(f"🎯 Subida DIRECTA a: {target_platform.upper()}")
            
            client = MoodleClient(
                config['user'],
                config['password'],
                config['host'], 
                config['repo_id']
            )
            
            if client.login():
                print(f"✅ Login exitoso en {target_platform.upper()}")
                result = client.upload_file_draft(
                    file_path,
                    progressfunc=progressfunc,
                    args=args
                )
                
                print(f"📦 Resultado directo: {result}")
                
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
                
                return {'error': 'No se pudo obtener URL del archivo', 'success': False}
            else:
                return {'error': f'Login fallido en {target_platform.upper()}', 'success': False}
                    
        except Exception as e:
            print(f"❌ Direct upload failed: {e}")
            return {'error': f'Subida directa fallida: {str(e)}', 'success': False}

    def _execute_mirror_upload(self, file_path, strategy_plan, progressfunc=None, args=()):
        """Mirror upload - Sube a ambas plataformas (CENED + Target)"""
        try:
            bridge_platform = strategy_plan['bridge_platform']
            target_platform = strategy_plan['target_platform']
            
            print(f"🪞 MIRROR UPLOAD: {bridge_platform.upper()} -> {target_platform.upper()}")
            
            # 1. Subir a CENED (siempre funciona)
            bridge_config = self.platforms[bridge_platform]
            bridge_client = MoodleClient(
                bridge_config['user'],
                bridge_config['password'],
                bridge_config['host'],
                bridge_config['repo_id']
            )
            
            bridge_url = None
            bridge_success = False
            
            if bridge_client.login():
                print(f"✅ Login exitoso en {bridge_platform.upper()}")
                bridge_result = bridge_client.upload_file_draft(
                    file_path,
                    progressfunc=progressfunc,
                    args=args
                )
                
                if bridge_result and len(bridge_result) >= 2:
                    itemid, bridge_filedata = bridge_result
                    if bridge_filedata and 'url' in bridge_filedata:
                        bridge_url = bridge_filedata['url']
                        bridge_success = True
                        print(f"✅ Bridge URL obtenida: {bridge_url}")
            
            # 2. Intentar subir a plataforma objetivo
            target_url = None
            target_success = False
            target_config = self.platforms[target_platform]
            
            target_client = MoodleClient(
                target_config['user'],
                target_config['password'],
                target_config['host'],
                target_config['repo_id']
            )
            
            if target_client.login():
                print(f"✅ Login exitoso en {target_platform.upper()}")
                target_result = target_client.upload_file_draft(file_path)
                
                if target_result and len(target_result) >= 2:
                    target_itemid, target_filedata = target_result
                    if target_filedata and 'url' in target_filedata:
                        target_url = target_filedata['url']
                        target_success = True
                        print(f"✅ Target URL obtenida: {target_url}")
            
            # 🎯 CONSTRUIR RESULTADO
            result = {
                'strategy': 'mirror_upload',
                'bridge_platform': bridge_platform,
                'target_platform': target_platform,
                'bridge_success': bridge_success,
                'target_success': target_success,
                'efficiency': 'high' if target_success else 'medium',
                'success': bridge_success or target_success
            }
            
            # Añadir URLs disponibles (prioridad: target > bridge)
            if target_url:
                result['target_url'] = target_url
                result['url'] = target_url  # URL principal
            if bridge_url:
                result['bridge_url'] = bridge_url
                if not target_url:  # Si no hay target, usar bridge como principal
                    result['url'] = bridge_url
            
            # Mensaje informativo CORREGIDO
            if target_success and bridge_success:
                result['message'] = f'🪞 Espejo completo: {bridge_platform.upper()} + {target_platform.upper()}'
            elif target_success:
                result['message'] = f'✅ Subida directa a {target_platform.upper()}'
            elif bridge_success:
                result['message'] = f'🌉 Subida via {bridge_platform.upper()} (bridge)'
            else:
                result['message'] = '❌ Ambas subidas fallaron'
                result['success'] = False
            
            print(f"🎯 Resultado final: {result}")
            return result
            
        except Exception as e:
            print(f"❌ Error en mirror_upload: {e}")
            return {
                'error': f'Mirror upload failed: {str(e)}',
                'success': False
            }

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
            # 🎯 USAR ESTRATEGIA INTELIGENTE SIMPLIFICADA
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
                    print(f"❌ Estrategia falló: {result.get('error', 'Error desconocido')}")
                
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
            # Para nube normal, usar método tradicional
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
                zip_filename = f"{zipname}.zip"
                
                # Crear ZIP con compresión
                with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    zipf.write(temp_file_path, arcname=original_filename)
                
                # Verificar si el archivo zip necesita división
                zip_size = get_file_size(zip_filename)
                
                if zip_size > max_file_size:
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
                
                # Limpiar archivos temporales ZIP después de subir
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
            return _process_bridge_results(client, original_filename, file_size, file_upload_count, update, bot, message, getUser)
        else:
            return _process_traditional_results(client, original_filename, file_size, file_upload_count, update, bot, message, getUser)
            
    except Exception as ex:
        print(f"Error en processFile: {ex}")

def _process_bridge_results(results, original_filename, file_size, file_upload_count, update, bot, message, user_info):
    """Procesar resultados de estrategia bridge - VERSIÓN SIMPLIFICADA"""
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
            
            # EXTRACCIÓN SIMPLE DE URL
            file_url = None
            if 'url' in result:
                file_url = result['url']
            elif 'target_url' in result:
                file_url = result['target_url']
            elif 'bridge_url' in result:
                file_url = result['bridge_url']
                
            if file_url:
                result_msg += f"\n• 🔗 URL: {file_url}"
                all_urls.append({'name': f"{original_filename}", 'directurl': file_url})
            else:
                result_msg += f"\n• ❌ No se obtuvo URL (pero la subida fue exitosa)"
            
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
            bot.sendMessage(update.message.chat.id, "⚠️ Subida exitosa pero no se generaron enlaces - Contacta al administrador")
        
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
                '<b>🎯 Estrategia:</b> Mirror upload via CENED',
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
                '<b>🎯 Estrategia:</b> Mirror upload via CENED',
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
            '/proxy_test', '/proxy_clear', '/confirm_proxy'
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
                           "• Estrategia mirror automática\n" 
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
┣⪼ 🚀 Subidas con Mirror Strategy
┣⪼ 👨‍💻 Desarrollado por: @Eliel_21
┣⪼ 🏫 Plataforma: {platform_name}
┣⪼ 🌐 Conexión: Directa (Sin proxy)
┣⪼ 🎯 Estrategia: Mirror Upload
┣⪼ ⏱️ Enlaces: 3 días

┣⪼ ⚙️ CONFIGURACIÓN RÁPIDA:
┣⪼ /moodle_eva - EVA (vía CENED)
┣⪼ /moodle_cursos - CURSOS (vía CENED)  
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
┣⪼ 🚀 Subidas con Mirror Strategy  
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
    print("🎯 Modo: Mirror Strategy System")
    print("🌐 Conexión: Directa (sin proxy)")
    print("🏫 Plataformas: EVA, CURSOS, CENED")
    print("🪞 Estrategia: Mirror Upload con CENED como puente")
    
    bot.run()

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"❌ Error: {e}")
        time.sleep(5)
        main()
