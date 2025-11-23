from pyobigram.utils import sizeof_fmt,get_file_size,createID,nice_time
from pyobigram.client import ObigramClient,inlineQueryResultArticle
from MoodleClient import MoodleClient

from JDatabase import JsonDatabase
import zipfile
import os
import infos
import xdlink
import mediafire
#from megacli.mega import Mega
#import megacli.megafolder as megaf
#import megacli.mega
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
import json

def create_progress_bar(percentage, bars=10):
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
        
        if minutes > 99:  # Si son más de 99 minutos
            return "99:59+"
        
        return f"{minutes:02d}:{secs:02d}"
    except:
        return "00:00"

def downloadFile(downloader,filename,currentBits,totalBits,speed,time,args):
    try:
        bot = args[0]
        message = args[1]
        thread = args[2]
        download_url = args[3] if len(args) > 3 else "Unknown"
        
        if thread.getStore('stop'):
            downloader.stop()
            return
        
        # Calcular porcentaje y crear barra de progreso S1
        if totalBits > 0:
            percentage = (currentBits / totalBits) * 100
            progress_bar = create_progress_bar(percentage)
            total_mb = totalBits / (1024 * 1024)
            current_mb = currentBits / (1024 * 1024)
            speed_mb = speed / (1024 * 1024) if speed > 0 else 0
            
            # Calcular ETA con formato mejorado (minutos:segundos)
            if speed > 0:
                remaining_bits = totalBits - currentBits
                eta_seconds = remaining_bits / speed
                eta_formatted = format_time(eta_seconds)
            else:
                eta_formatted = "00:00"
            
            # Obtener thread_id para el comando de cancelación
            thread_id = thread.thread_id if hasattr(thread, 'thread_id') else id(thread)
            
            # Mensaje con estilo S1 corregido + botón de cancelar
            downloadingInfo = format_s1_message("📥 Descargando", [
                f"[{progress_bar}]",
                f"✅ Progreso: {percentage:.1f}%",
                f"📦 Tamaño: {current_mb:.2f}/{total_mb:.2f} MB",
                f"⚡ Velocidad: {speed_mb:.2f} MB/s",
                f"⏳ Tiempo: {eta_formatted}",
                f"🚫 Cancelar: /cancel_{thread_id}"
            ])
        else:
            thread_id = thread.thread_id if hasattr(thread, 'thread_id') else id(thread)
            downloadingInfo = format_s1_message("📥 Descargando", [
                "[⬡⬡⬡⬡⬡⬡⬡⬡⬡⬡]",
                "✅ Progreso: 0%",
                "📦 Tamaño: Calculando...",
                "⚡ Velocidad: 0.00 MB/s",
                "⏳ Tiempo: 00:00",
                f"🚫 Cancelar: /cancel_{thread_id}"
            ])
            
        bot.editMessageText(message, downloadingInfo)
    except Exception as ex: 
        print(str(ex))
    pass

def uploadFile(filename,currentBits,totalBits,speed,time,args):
    try:
        bot = args[0]
        message = args[1]
        originalfile = args[2]
        thread = args[3]
        part_info = args[4] if len(args) > 4 else None
        
        # Verificar si se canceló
        if thread.getStore('stop'):
            return
        
        # Calcular porcentaje y crear barra de progreso S1
        if totalBits > 0:
            percentage = (currentBits / totalBits) * 100
            progress_bar = create_progress_bar(percentage)
            total_mb = totalBits / (1024 * 1024)
            current_mb = currentBits / (1024 * 1024)
            speed_mb = speed / (1024 * 1024) if speed > 0 else 0
            
            # Calcular ETA con formato mejorado (minutos:segundos)
            if speed > 0:
                remaining_bits = totalBits - currentBits
                eta_seconds = remaining_bits / speed
                eta_formatted = format_time(eta_seconds)
            else:
                eta_formatted = "00:00"
            
            # Mostrar información de partes si está disponible
            file_display = filename
            if part_info:
                current_part, total_parts, original_name = part_info
                file_display = f"{original_name} (Parte {current_part}/{total_parts})"
            elif originalfile:
                file_display = originalfile
            
            # Obtener thread_id para el comando de cancelación
            thread_id = thread.thread_id if hasattr(thread, 'thread_id') else id(thread)
            
            # Mensaje con estilo S1 corregido + botón de cancelar
            uploadingInfo = format_s1_message("📤 Subiendo", [
                f"[{progress_bar}]",
                f"✅ Progreso: {percentage:.1f}%",
                f"📦 Tamaño: {current_mb:.2f}/{total_mb:.2f} MB",
                f"⚡ Velocidad: {speed_mb:.2f} MB/s",
                f"⏳ Tiempo: {eta_formatted}",
                f"📄 Archivo: {file_display}",
                f"🚫 Cancelar: /cancel_{thread_id}"
            ])
        else:
            file_display = filename
            if part_info:
                current_part, total_parts, original_name = part_info
                file_display = f"{original_name} (Parte {current_part}/{total_parts})"
            
            thread_id = thread.thread_id if hasattr(thread, 'thread_id') else id(thread)
            uploadingInfo = format_s1_message("📤 Subiendo", [
                "[⬡⬡⬡⬡⬡⬡⬡⬡⬡⬡]",
                "✅ Progreso: 0%",
                "📦 Tamaño: Calculando...",
                "⚡ Velocidad: 0.00 MB/s",
                "⏳ Tiempo: 00:00",
                f"📄 Archivo: {file_display}",
                f"🚫 Cancelar: /cancel_{thread_id}"
            ])
            
        bot.editMessageText(message, uploadingInfo)
    except Exception as ex: 
        print(str(ex))
    pass

def processUploadFiles(filename,filesize,files,update,bot,message,thread=None,jdb=None):
    try:
        bot.editMessageText(message,'<b>🔄 Preparando para subir...</b>', parse_mode='HTML')
        evidence = None
        fileid = None
        user_info = jdb.get_user(update.message.sender.username)
        cloudtype = user_info['cloudtype']
        proxy = ProxyCloud.parse(user_info['proxy'])
        
        if cloudtype == 'moodle':
            client = MoodleClient(user_info['moodle_user'],
                                  user_info['moodle_password'],
                                  user_info['moodle_host'],
                                  user_info['moodle_repo_id'],
                                  proxy=proxy)
            loged = client.login()
            itererr = 0
            if loged:
                if user_info['uploadtype'] == 'evidence':
                    evidences = client.getEvidences()
                    evidname = str(filename).split('.')[0]
                    for evid in evidences:
                        if evid['name'] == evidname:
                            evidence = evid
                            break
                    if evidence is None:
                        evidence = client.createEvidence(evidname)

                originalfile = ''
                total_parts = len(files)
                draftlist = []
                
                for i, f in enumerate(files, 1):
                    # Verificar cancelación antes de cada subida
                    if thread and thread.getStore('stop'):
                        bot.editMessageText(message,'<b>❌ Subida cancelada por el usuario</b>', parse_mode='HTML')
                        return None
                        
                    f_size = get_file_size(f)
                    resp = None
                    iter = 0
                    tokenize = False
                    
                    if user_info['tokenize']!=0:
                       tokenize = True
                    
                    # Información de partes para archivos múltiples
                    part_info = None
                    if total_parts > 1:
                        part_info = (i, total_parts, filename)
                    
                    while resp is None:
                          # Verificar cancelación durante la subida
                          if thread and thread.getStore('stop'):
                              bot.editMessageText(message,'<b>❌ Subida cancelada por el usuario</b>', parse_mode='HTML')
                              return None
                              
                          if user_info['uploadtype'] == 'evidence':
                             fileid,resp = client.upload_file(f,evidence,fileid,
                                                             progressfunc=uploadFile,
                                                             args=(bot,message,filename,thread,part_info),
                                                             tokenize=tokenize)
                             draftlist.append(resp)
                          if user_info['uploadtype'] == 'draft':
                             fileid,resp = client.upload_file_draft(f,
                                                                   progressfunc=uploadFile,
                                                                   args=(bot,message,filename,thread,part_info),
                                                                   tokenize=tokenize)
                             draftlist.append(resp)
                          if user_info['uploadtype'] == 'blog':
                             fileid,resp = client.upload_file_blog(f,
                                                                  progressfunc=uploadFile,
                                                                  args=(bot,message,filename,thread,part_info),
                                                                  tokenize=tokenize)
                             draftlist.append(resp)
                          if user_info['uploadtype'] == 'calendario':
                             fileid,resp = client.upload_file_calendar(f,
                                                                      progressfunc=uploadFile,
                                                                      args=(bot,message,filename,thread,part_info),
                                                                      tokenize=tokenize)
                             draftlist.append(resp)
                          iter += 1
                          if iter>=10:
                              break
                    os.unlink(f)
                    
                if user_info['uploadtype'] == 'evidence':
                    try:
                        client.saveEvidence(evidence)
                    except:pass
                return draftlist
            else:
                bot.editMessageText(message,'<b>❌ Error en la plataforma</b>', parse_mode='HTML')
        elif cloudtype == 'cloud':
            tokenize = False
            if user_info['tokenize']!=0:
               tokenize = True
            bot.editMessageText(message,'<b>☁️ Subiendo archivo...</b>', parse_mode='HTML')
            host = user_info['moodle_host']
            user = user_info['moodle_user']
            passw = user_info['moodle_password']
            remotepath = user_info['dir']
            client = NexCloudClient.NexCloudClient(user,passw,host,proxy=proxy)
            loged = client.login()
            if loged:
               total_parts = len(files)
               filesdata = []
               for i, f in enumerate(files, 1):
                   # Verificar cancelación antes de cada subida
                   if thread and thread.getStore('stop'):
                       bot.editMessageText(message,'<b>❌ Subida cancelada por el usuario</b>', parse_mode='HTML')
                       return None
                       
                   # Información de partes para archivos múltiples
                   part_info = None
                   if total_parts > 1:
                       part_info = (i, total_parts, filename)
                       
                   data = client.upload_file(f,path=remotepath,
                                            progressfunc=uploadFile,
                                            args=(bot,message,filename,thread,part_info),
                                            tokenize=tokenize)
                   filesdata.append(data)
                   os.unlink(f)
               return filesdata
        return None
    except Exception as ex:
        bot.editMessageText(message,f'<b>❌ Error</b>\n<code>{str(ex)}</code>', parse_mode='HTML')
        return None

def processFile(update,bot,message,file,thread=None,jdb=None):
    # Verificar cancelación al inicio
    if thread and thread.getStore('stop'):
        bot.editMessageText(message,'<b>❌ Proceso cancelado por el usuario</b>', parse_mode='HTML')
        try:
            if os.path.exists(file):
                os.unlink(file)
        except:
            pass
        return
        
    file_size = get_file_size(file)
    getUser = jdb.get_user(update.message.sender.username)
    max_file_size = 1024 * 1024 * getUser['zips']
    file_upload_count = 0
    client = None
    findex = 0
    if file_size > max_file_size:
        compresingInfo = infos.createCompresing(file,file_size,max_file_size)
        bot.editMessageText(message,compresingInfo)
        zipname = str(file).split('.')[0] + createID()
        mult_file = zipfile.MultiFile(zipname,max_file_size)
        zip = zipfile.ZipFile(mult_file,  mode='w', compression=zipfile.ZIP_DEFLATED)
        zip.write(file)
        zip.close()
        mult_file.close()
        client = processUploadFiles(file,file_size,mult_file.files,update,bot,message,thread=thread,jdb=jdb)
        try:
            os.unlink(file)
        except:pass
        file_upload_count = len(mult_file.files)
    else:
        client = processUploadFiles(file,file_size,[file],update,bot,message,thread=thread,jdb=jdb)
        file_upload_count = 1
        
    # Verificar cancelación después de la subida
    if thread and thread.getStore('stop'):
        bot.editMessageText(message,'<b>❌ Proceso cancelado por el usuario</b>', parse_mode='HTML')
        return
        
    bot.editMessageText(message,'<b>📄 Preparando enlaces...</b>', parse_mode='HTML')
    evidname = ''
    files = []
    if client:
        if getUser['cloudtype'] == 'moodle':
            if getUser['uploadtype'] == 'evidence':
                try:
                    evidname = str(file).split('.')[0]
                    txtname = evidname + '.txt'
                    evidences = client.getEvidences()
                    for ev in evidences:
                        if ev['name'] == evidname:
                           files = ev['files']
                           break
                        if len(ev['files'])>0:
                           findex+=1
                    client.logout()
                except:pass
            if getUser['uploadtype'] == 'draft' or getUser['uploadtype'] == 'blog' or getUser['uploadtype']=='calendario':
               for draft in client:
                   files.append({'name':draft['file'],'directurl':draft['url']})
        else:
            for data in client:
                files.append({'name':data['name'],'directurl':data['url']})

        # MODIFICAR ENLACES para que tengan /webservice
        for i in range(len(files)):
            url = files[i]['directurl']
            if 'aulacened.uci.cu' in url:
                files[i]['directurl'] = url.replace('://aulacened.uci.cu/', '://aulacened.uci.cu/webservice/')

        bot.deleteMessage(message.chat.id,message.message_id)
        
        # MENSAJE FINAL CON ESTILO S1
        original_filename = file.split('/')[-1] if '/' in file else file
        total_parts = file_upload_count
        
        if total_parts > 1:
            finish_title = f"✅ Subida Completada - {total_parts} Partes"
        else:
            finish_title = "✅ Subida Completada"
            
        finishInfo = format_s1_message(finish_title, [
            f"📄 Archivo: {original_filename}",
            f"📦 Tamaño total: {sizeof_fmt(file_size)}",
            f"🔗 Enlaces generados: {len(files)}",
            f"⏱️ Duración enlaces: 8-30 minutos",
            f"💾 Partes: {total_parts}" if total_parts > 1 else "💾 Archivo único"
        ])
        
        # Enviar mensaje final S1
        bot.sendMessage(message.chat.id, finishInfo)
        
        # ENVIAR ENLACES (MANTENIENDO LA FUNCIONALIDAD ORIGINAL)
        if len(files) > 0:
            filesInfo = infos.createFileMsg(file,files)
            bot.sendMessage(message.chat.id, filesInfo, parse_mode='html')
            txtname = str(file).split('/')[-1].split('.')[0] + '.txt'
            sendTxt(txtname,files,update,bot)
            
            # Guardar analytics de subida completada
            if not jdb.is_admin(update.message.sender.username):
                save_user_analytics(update, bot, jdb, "file_upload", {
                    "file_size": file_size,
                    "file_parts": total_parts,
                    "links_generated": len(files)
                })

def ddl(update,bot,message,url,file_name='',thread=None,jdb=None):
    downloader = Downloader()
    file = downloader.download_url(url,progressfunc=downloadFile,args=(bot,message,thread,url))
    if not downloader.stoping:
        if file:
            processFile(update,bot,message,file,thread=thread,jdb=jdb)
        else:
            megadl(update,bot,message,url,file_name,thread,jdb=jdb)

def megadl(update,bot,message,megaurl,file_name='',thread=None,jdb=None):
    megadl = megacli.mega.Mega({'verbose': True})
    megadl.login()
    try:
        info = megadl.get_public_url_info(megaurl)
        file_name = info['name']
        megadl.download_url(megaurl,dest_path=None,dest_filename=file_name,progressfunc=downloadFile,args=(bot,message,thread))
        if not megadl.stoping:
            processFile(update,bot,message,file_name,thread=thread)
    except:
        files = megaf.get_files_from_folder(megaurl)
        for f in files:
            file_name = f['name']
            megadl._download_file(f['handle'],f['key'],dest_path=None,dest_filename=file_name,is_public=False,progressfunc=downloadFile,args=(bot,message,thread),f_data=f['data'])
            if not megadl.stoping:
                processFile(update,bot,message,file_name,thread=thread)
        pass
    pass

def sendTxt(name,files,update,bot):
    """Envía archivo txt con enlaces y thumbnail personalizado"""
    try:
        # Crear el archivo txt con formato mejorado
        with open(name, 'w', encoding='utf-8') as txt:
            txt.write("📄 ENLACES DE DESCARGA\n")
            txt.write("=" * 30 + "\n\n")
            for i, f in enumerate(files, 1):
                txt.write(f"{i}. {f['name']}\n")
                txt.write(f"🔗 {f['directurl']}\n")
                txt.write("-" * 40 + "\n")
        
        # Mensaje informativo como caption
        info_msg = f"""<b>📄 Archivo de enlaces generado</b>

📎 <b>Nombre:</b> <code>{name}</code>
🔗 <b>Enlaces incluidos:</b> {len(files)}
⏱️ <b>Duración de enlaces:</b> 8-30 minutos

⬇️ <b>Descarga el archivo TXT abajo</b>"""
        
        # Intentar enviar con thumbnail personalizado
        try:
            if os.path.exists('31F5FAAF-A68A-4A49-ADDE-EA4A20CE9E58.jpg'):
                bot.sendPhoto(update.message.chat.id,
                            open('31F5FAAF-A68A-4A49-ADDE-EA4A20CE9E58.jpg', 'rb'),
                            caption=info_msg,
                            parse_mode='HTML')
                bot.sendFile(update.message.chat.id, name, caption="📁 Archivo de enlaces")
            else:
                bot.sendFile(update.message.chat.id, name, caption=info_msg, parse_mode='HTML')
                
        except Exception as e:
            print(f"Error enviando con thumbnail: {e}")
            bot.sendFile(update.message.chat.id, name, caption=info_msg, parse_mode='HTML')
        
        # Limpiar archivo temporal
        os.unlink(name)
        
    except Exception as ex:
        print(f"Error en sendTxt: {str(ex)}")
        try:
            if os.path.exists(name):
                bot.sendFile(update.message.chat.id, name)
                os.unlink(name)
        except:
            pass

def save_user_analytics(update, bot, jdb, action, details=None):
    """Guarda analytics de usuarios en archivo Johnson (excepto admin)"""
    try:
        username = update.message.sender.username
        user_id = update.message.sender.id
        first_name = update.message.sender.first_name or "Unknown"
        last_name = update.message.sender.last_name or "Unknown"
        is_admin = jdb.is_admin(username)
        
        # No guardar analytics del administrador
        if is_admin:
            return
            
        analytics_file = "johnson_analytics.json"
        analytics_data = {}
        
        # Cargar datos existentes
        if os.path.exists(analytics_file):
            with open(analytics_file, 'r', encoding='utf-8') as f:
                analytics_data = json.load(f)
        
        user_key = f"{user_id}_{username}"
        
        if user_key not in analytics_data:
            analytics_data[user_key] = {
                "username": username,
                "user_id": user_id,
                "first_name": first_name,
                "last_name": last_name,
                "first_seen": datetime.datetime.now().isoformat(),
                "last_activity": datetime.datetime.now().isoformat(),
                "total_actions": 0,
                "actions": [],
                "files_uploaded": 0,
                "total_file_size": 0,
                "cloud_type": "unknown",
                "upload_type": "unknown"
            }
        
        # Actualizar datos del usuario
        user_data = analytics_data[user_key]
        user_data["last_activity"] = datetime.datetime.now().isoformat()
        user_data["total_actions"] += 1
        
        action_data = {
            "timestamp": datetime.datetime.now().isoformat(),
            "action": action,
            "details": details or {}
        }
        user_data["actions"].append(action_data)
        
        # Limitar historial de acciones a las últimas 100
        if len(user_data["actions"]) > 100:
            user_data["actions"] = user_data["actions"][-100:]
        
        # Actualizar estadísticas específicas
        if action == "file_upload":
            user_data["files_uploaded"] += 1
            if details and "file_size" in details:
                user_data["total_file_size"] += details["file_size"]
        
        if action == "user_config" and details:
            if "cloud_type" in details:
                user_data["cloud_type"] = details["cloud_type"]
            if "upload_type" in details:
                user_data["upload_type"] = details["upload_type"]
        
        # Guardar datos
        with open(analytics_file, 'w', encoding='utf-8') as f:
            json.dump(analytics_data, f, indent=2, ensure_ascii=False)
            
    except Exception as e:
        print(f"Error en analytics: {e}")

def onmessage(update,bot:ObigramClient):
    try:
        thread = bot.this_thread
        username = update.message.sender.username
        tl_admin_user = os.environ.get('tl_admin_user','Eliel_21')

        jdb = JsonDatabase('database')
        jdb.check_create()
        jdb.load()

        user_info = jdb.get_user(username)

        if username == tl_admin_user or tl_admin_user=='*' or user_info :  # validate user
            if user_info is None:
                if username == tl_admin_user:
                    jdb.create_admin(username)
                else:
                    jdb.create_user(username)
                    # Guardar analytics de nuevo usuario
                    save_user_analytics(update, bot, jdb, "new_user", {
                        "username": username,
                        "user_id": update.message.sender.id
                    })
                user_info = jdb.get_user(username)
                jdb.save_data_user(username, user_info)
                jdb.save()
        else:
            return

        msgText = ''
        try: 
            msgText = update.message.text
        except: 
            msgText = ''

        # ✅ DETECTAR TIPO DE MENSAJE
        is_text = msgText != ''
        
        # ✅ BLOQUEAR SOLO COMANDOS DE CONFIGURACIÓN PARA USUARIOS NORMALES
        isadmin = jdb.is_admin(username)
        
        # Si NO es admin y el mensaje es un COMANDO de configuración, bloquear
        if not isadmin and is_text and any(cmd in msgText for cmd in [
            '/zips', '/account', '/host', '/repoid', '/tokenize', 
            '/cloud', '/uptype', '/proxy', '/dir', '/myuser', 
            '/files', '/txt_', '/del_', '/delall', '/adduser', '/banuser', '/getdb'
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

        # Si es un mensaje de texto normal (no comando, no enlace)
        if is_text and not msgText.startswith('/') and not 'http' in msgText:
            if isadmin:
                response_msg = """<b>👋 ¡Hola Administrador!</b>

<b>📝 Comandos de administrador:</b>
• /myuser - Mi configuración
• /zips - Tamaño de partes
• /account - Cuenta Moodle
• /host - Servidor Moodle
• /repoid - ID Repositorio
• /cloud - Tipo de nube
• /uptype - Tipo de subida
• /proxy - Configurar proxy
• /dir - Directorio cloud
• /files - Ver archivos
• /adduser - Agregar usuario
• /banuser - Eliminar usuario
• /getdb - Base de datos
• /analytics - Ver estadísticas

<b>📚 Comandos para todos:</b>
• /start - Información del bot
• /tutorial - Guía completa

<b>🌐 O envía un enlace HTTP/HTTPS para subir archivos</b>"""
            else:
                response_msg = """<b>👋 ¡Bienvenido!</b>

<b>✅ Comandos disponibles:</b>
• /start - Información del bot
• /tutorial - Guía completa de uso

<b>📤 Para subir archivos:</b>
Envía cualquier enlace HTTP/HTTPS y el bot lo procesará automáticamente.

<b>⏱️ Los enlaces generados duran 8-30 minutos</b>"""
            
            bot.sendMessage(update.message.chat.id, response_msg, parse_mode='HTML')
            return

        # COMANDO ANALYTICS - SOLO ADMIN
        if '/analytics' in msgText:
            if not isadmin:
                bot.sendMessage(update.message.chat.id,'<b>❌ Comando restringido a administradores</b>', parse_mode='HTML')
                return
            try:
                analytics_file = "johnson_analytics.json"
                if os.path.exists(analytics_file):
                    bot.sendMessage(update.message.chat.id,'<b>📊 Estadísticas de usuarios:</b>', parse_mode='HTML')
                    bot.sendFile(update.message.chat.id, analytics_file)
                else:
                    bot.sendMessage(update.message.chat.id,'<b>📊 No hay datos de analytics aún</b>', parse_mode='HTML')
            except Exception as e:
                bot.sendMessage(update.message.chat.id,f'<b>❌ Error cargando analytics:</b> {str(e)}', parse_mode='HTML')
            return

        # COMANDO ADDUSER MEJORADO - MÚLTIPLES USUARIOS
        if '/adduser' in msgText:
            isadmin = jdb.is_admin(username)
            if isadmin:
                try:
                    users_text = str(msgText).split(' ', 1)[1]
                    users = [user.strip().replace('@', '') for user in users_text.split(',')]
                    
                    added_users = []
                    existing_users = []
                    
                    for user in users:
                        if user:
                            if not jdb.get_user(user):
                                jdb.create_user(user)
                                added_users.append(user)
                            else:
                                existing_users.append(user)
                    
                    jdb.save()
                    
                    message_parts = []
                    
                    if added_users:
                        if len(added_users) == 1:
                            message_parts.append(f'<b>✅ Usuario agregado:</b> @{added_users[0]}')
                        else:
                            message_parts.append(f'<b>✅ Usuarios agregados:</b> @{", @".join(added_users)}')
                    
                    if existing_users:
                        if len(existing_users) == 1:
                            message_parts.append(f'<b>⚠️ Usuario ya existente:</b> @{existing_users[0]}')
                        else:
                            message_parts.append(f'<b>⚠️ Usuarios ya existentes:</b> @{", @".join(existing_users)}')
                    
                    if message_parts:
                        final_message = '\n\n'.join(message_parts)
                    else:
                        final_message = '<b>❌ No se proporcionaron usuarios válidos</b>'
                        
                    bot.sendMessage(update.message.chat.id, final_message, parse_mode='HTML')
                    
                except Exception as e:
                    print(f"Error en adduser: {e}")
                    bot.sendMessage(update.message.chat.id,
                                   '<b>❌ Error en el comando:</b>\n'
                                   '<code>/adduser user1, user2, user3</code>\n\n'
                                   '<b>Ejemplos:</b>\n'
                                   '<code>/adduser juan</code>\n'
                                   '<code>/adduser juan, maria, pedro</code>', 
                                   parse_mode='HTML')
            else:
                bot.sendMessage(update.message.chat.id,'<b>❌ No tiene permisos de administrador</b>', parse_mode='HTML')
            return

        # COMANDO BANUSER MEJORADO - MÚLTIPLES USUARIOS
        if '/banuser' in msgText:
            isadmin = jdb.is_admin(username)
            if isadmin:
                try:
                    users_text = str(msgText).split(' ', 1)[1]
                    users = [user.strip().replace('@', '') for user in users_text.split(',')]
                    
                    banned_users = []
                    not_found_users = []
                    self_ban_attempt = False
                    
                    for user in users:
                        if user:
                            if user == username:
                                self_ban_attempt = True
                                continue
                            if jdb.get_user(user):
                                jdb.remove(user)
                                banned_users.append(user)
                            else:
                                not_found_users.append(user)
                    
                    jdb.save()
                    
                    message_parts = []
                    
                    if banned_users:
                        if len(banned_users) == 1:
                            message_parts.append(f'<b>🚫 Usuario baneado:</b> @{banned_users[0]}')
                        else:
                            message_parts.append(f'<b>🚫 Usuarios baneados:</b> @{", @".join(banned_users)}')
                    
                    if not_found_users:
                        if len(not_found_users) == 1:
                            message_parts.append(f'<b>❌ Usuario no encontrado:</b> @{not_found_users[0]}')
                        else:
                            message_parts.append(f'<b>❌ Usuarios no encontrados:</b> @{", @".join(not_found_users)}')
                    
                    if self_ban_attempt:
                        message_parts.append('<b>⚠️ No puedes banearte a ti mismo</b>')
                    
                    if message_parts:
                        final_message = '\n\n'.join(message_parts)
                    else:
                        final_message = '<b>❌ No se proporcionaron usuarios válidos</b>'
                        
                    bot.sendMessage(update.message.chat.id, final_message, parse_mode='HTML')
                    
                except Exception as e:
                    print(f"Error en banuser: {e}")
                    bot.sendMessage(update.message.chat.id,
                                   '<b>❌ Error en el comando:</b>\n'
                                   '<code>/banuser user1, user2, user3</code>\n\n'
                                   '<b>Ejemplos:</b>\n'
                                   '<code>/banuser juan</code>\n'
                                   '<code>/banuser juan, maria, pedro</code>', 
                                   parse_mode='HTML')
            else:
                bot.sendMessage(update.message.chat.id,'<b>❌ No tiene permisos de administrador</b>', parse_mode='HTML')
            return

        if '/getdb' in msgText:
            isadmin = jdb.is_admin(username)
            if isadmin:
                bot.sendMessage(update.message.chat.id,'<b>📦 Base de datos:</b>', parse_mode='HTML')
                bot.sendFile(update.message.chat.id,'database.jdb')
            else:
                bot.sendMessage(update.message.chat.id,'<b>❌ No tiene permisos de administrador</b>', parse_mode='HTML')
            return

        # COMANDO TUTORIAL - DISPONIBLE PARA TODOS
        if '/tutorial' in msgText:
            try:
                tuto = open('tuto.txt','r', encoding='utf-8')
                tutorial_content = tuto.read()
                tuto.close()
                bot.sendMessage(update.message.chat.id, tutorial_content)
                # Analytics para tutorial
                if not isadmin:
                    save_user_analytics(update, bot, jdb, "tutorial_viewed")
            except Exception as e:
                print(f"Error cargando tutorial: {e}")
                bot.sendMessage(update.message.chat.id,'<b>📚 Archivo de tutorial no disponible</b>', parse_mode='HTML')
            return

        # comandos de usuario (solo para administrador)
        if '/myuser' in msgText:
            if not isadmin:
                bot.sendMessage(update.message.chat.id,'<b>❌ Comando restringido a administradores</b>', parse_mode='HTML')
                return
            getUser = user_info
            if getUser:
                statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                bot.sendMessage(update.message.chat.id,statInfo, parse_mode='HTML')
                return
        if '/zips' in msgText:
            if not isadmin:
                bot.sendMessage(update.message.chat.id,'<b>❌ Comando restringido a administradores</b>', parse_mode='HTML')
                return
            getUser = user_info
            if getUser:
                try:
                   size = int(str(msgText).split(' ')[1])
                   getUser['zips'] = size
                   jdb.save_data_user(username,getUser)
                   jdb.save()
                   msg = f'<b>✅ Zips configurados a</b> {sizeof_fmt(size*1024*1024)} <b>por parte</b>'
                   bot.sendMessage(update.message.chat.id,msg, parse_mode='HTML')
                except:
                   bot.sendMessage(update.message.chat.id,'<b>❌ Error:</b> <code>/zips tamaño_en_mb</code>', parse_mode='HTML')
                return
        if '/account' in msgText:
            if not isadmin:
                bot.sendMessage(update.message.chat.id,'<b>❌ Comando restringido a administradores</b>', parse_mode='HTML')
                return
            try:
                account = str(msgText).split(' ',2)[1].split(',')
                user = account[0]
                passw = account[1]
                getUser = user_info
                if getUser:
                    getUser['moodle_user'] = user
                    getUser['moodle_password'] = passw
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,statInfo, parse_mode='HTML')
                    # Analytics para configuración
                    if not isadmin:
                        save_user_analytics(update, bot, jdb, "user_config", {
                            "cloud_type": getUser['cloudtype'],
                            "upload_type": getUser['uploadtype']
                        })
            except:
                bot.sendMessage(update.message.chat.id,'<b>❌ Error:</b> <code>/account usuario,contraseña</code>', parse_mode='HTML')
            return
        if '/host' in msgText:
            if not isadmin:
                bot.sendMessage(update.message.chat.id,'<b>❌ Comando restringido a administradores</b>', parse_mode='HTML')
                return
            try:
                cmd = str(msgText).split(' ',2)
                host = cmd[1]
                getUser = user_info
                if getUser:
                    getUser['moodle_host'] = host
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,statInfo, parse_mode='HTML')
            except:
                bot.sendMessage(update.message.chat.id,'<b>❌ Error:</b> <code>/host url_del_moodle</code>', parse_mode='HTML')
            return
        if '/repoid' in msgText:
            if not isadmin:
                bot.sendMessage(update.message.chat.id,'<b>❌ Comando restringido a administradores</b>', parse_mode='HTML')
                return
            try:
                cmd = str(msgText).split(' ',2)
                repoid = int(cmd[1])
                getUser = user_info
                if getUser:
                    getUser['moodle_repo_id'] = repoid
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,statInfo, parse_mode='HTML')
            except:
                bot.sendMessage(update.message.chat.id,'<b>❌ Error:</b> <code>/repoid id_del_repositorio</code>', parse_mode='HTML')
            return
        if '/tokenize_on' in msgText:
            if not isadmin:
                bot.sendMessage(update.message.chat.id,'<b>❌ Comando restringido a administradores</b>', parse_mode='HTML')
                return
            try:
                getUser = user_info
                if getUser:
                    getUser['tokenize'] = 1
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,statInfo, parse_mode='HTML')
            except:
                bot.sendMessage(update.message.chat.id,'<b>❌ Error activando tokenize</b>', parse_mode='HTML')
            return
        if '/tokenize_off' in msgText:
            if not isadmin:
                bot.sendMessage(update.message.chat.id,'<b>❌ Comando restringido a administradores</b>', parse_mode='HTML')
                return
            try:
                getUser = user_info
                if getUser:
                    getUser['tokenize'] = 0
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,statInfo, parse_mode='HTML')
            except:
                bot.sendMessage(update.message.chat.id,'<b>❌ Error desactivando tokenize</b>', parse_mode='HTML')
            return
        if '/cloud' in msgText:
            if not isadmin:
                bot.sendMessage(update.message.chat.id,'<b>❌ Comando restringido a administradores</b>', parse_mode='HTML')
                return
            try:
                cmd = str(msgText).split(' ',2)
                repoid = cmd[1]
                getUser = user_info
                if getUser:
                    getUser['cloudtype'] = repoid
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,statInfo, parse_mode='HTML')
                    # Analytics para configuración de cloud
                    if not isadmin:
                        save_user_analytics(update, bot, jdb, "user_config", {
                            "cloud_type": repoid,
                            "upload_type": getUser['uploadtype']
                        })
            except:
                bot.sendMessage(update.message.chat.id,'<b>❌ Error:</b> <code>/cloud (moodle o cloud)</code>', parse_mode='HTML')
            return
        if '/uptype' in msgText:
            if not isadmin:
                bot.sendMessage(update.message.chat.id,'<b>❌ Comando restringido a administradores</b>', parse_mode='HTML')
                return
            try:
                cmd = str(msgText).split(' ',2)
                type = cmd[1]
                getUser = user_info
                if getUser:
                    getUser['uploadtype'] = type
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,statInfo, parse_mode='HTML')
                    # Analytics para configuración de upload type
                    if not isadmin:
                        save_user_analytics(update, bot, jdb, "user_config", {
                            "cloud_type": getUser['cloudtype'],
                            "upload_type": type
                        })
            except:
                bot.sendMessage(update.message.chat.id,'<b>❌ Error:</b> <code>/uptype (evidence, draft, blog)</code>', parse_mode='HTML')
            return
        if '/proxy' in msgText:
            if not isadmin:
                bot.sendMessage(update.message.chat.id,'<b>❌ Comando restringido a administradores</b>', parse_mode='HTML')
                return
            try:
                cmd = str(msgText).split(' ',2)
                proxy = cmd[1]
                getUser = user_info
                if getUser:
                    getUser['proxy'] = proxy
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,statInfo, parse_mode='HTML')
            except:
                if user_info:
                    user_info['proxy'] = ''
                    statInfo = infos.createStat(username,user_info,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,statInfo, parse_mode='HTML')
            return
        if '/dir' in msgText:
            if not isadmin:
                bot.sendMessage(update.message.chat.id,'<b>❌ Comando restringido a administradores</b>', parse_mode='HTML')
                return
            try:
                cmd = str(msgText).split(' ',2)
                repoid = cmd[1]
                getUser = user_info
                if getUser:
                    getUser['dir'] = repoid + '/'
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,statInfo, parse_mode='HTML')
            except:
                bot.sendMessage(update.message.chat.id,'<b>❌ Error:</b> <code>/dir nombre_carpeta</code>', parse_mode='HTML')
            return
        if '/cancel_' in msgText:
            try:
                cmd = str(msgText).split('_',2)
                tid = cmd[1]
                # Buscar el thread por ID
                for thread_id, tcancel in bot.threads.items():
                    if str(thread_id) == tid or str(id(tcancel)) == tid:
                        msg = tcancel.getStore('msg')
                        tcancel.store('stop',True)
                        # Intentar editar el mensaje
                        try:
                            bot.editMessageText(msg,'<b>❌ Tarea Cancelada</b>', parse_mode='HTML')
                        except:
                            pass
                        break
            except Exception as ex:
                print(str(ex))
            return

        message = bot.sendMessage(update.message.chat.id,'<b>⏳ Procesando...</b>', parse_mode='HTML')
        thread.store('msg',message)

        # Asignar ID único al thread para cancelación
        thread.thread_id = createID()
        thread.store('stop', False)

        if '/start' in msgText:
            welcome_text = format_s1_message("🤖 Bot de Moodle", [
                "🚀 Subidas a Moodle",
                "👨‍💻 Desarrollado por: @Eliel_21", 
                "⏱️ Enlaces: 8-30 minutos",
                "📤 Envía enlaces HTTP/HTTPS",
                "📚 Usa /tutorial para ayuda",
                "🚫 Usa /cancel_id para cancelar"
            ])
            
            bot.deleteMessage(message.chat.id, message.message_id)
            
            try:
                if os.path.exists('31F5FAAF-A68A-4A49-ADDE-EA4A20CE9E58.jpg'):
                    bot.sendPhoto(
                        update.message.chat.id,
                        open('31F5FAAF-A68A-4A49-ADDE-EA4A20CE9E58.jpg', 'rb'),
                        caption=welcome_text
                    )
                else:
                    bot.sendMessage(update.message.chat.id, welcome_text)
            except Exception as e:
                print(f"Error enviando foto de bienvenida: {e}")
                bot.sendMessage(update.message.chat.id, welcome_text)
                
            # Analytics para start
            if not isadmin:
                save_user_analytics(update, bot, jdb, "start_command")
                
        elif '/files' == msgText and user_info['cloudtype']=='moodle':
             if not isadmin:
                bot.sendMessage(update.message.chat.id,'<b>❌ Comando restringido a administradores</b>', parse_mode='HTML')
                return
             proxy = ProxyCloud.parse(user_info['proxy'])
             client = MoodleClient(user_info['moodle_user'],
                                   user_info['moodle_password'],
                                   user_info['moodle_host'],
                                   user_info['moodle_repo_id'],proxy=proxy)
             loged = client.login()
             if loged:
                 files = client.getEvidences()
                 filesInfo = infos.createFilesMsg(files)
                 bot.editMessageText(message,filesInfo, parse_mode='HTML')
                 client.logout()
             else:
                bot.editMessageText(message,'<b>❌ Error de conexión</b>\n• Verifique su cuenta\n• Servidor: '+client.path, parse_mode='HTML')
        elif '/txt_' in msgText and user_info['cloudtype']=='moodle':
             if not isadmin:
                bot.sendMessage(update.message.chat.id,'<b>❌ Comando restringido a administradores</b>', parse_mode='HTML')
                return
             findex = str(msgText).split('_')[1]
             findex = int(findex)
             proxy = ProxyCloud.parse(user_info['proxy'])
             client = MoodleClient(user_info['moodle_user'],
                                   user_info['moodle_password'],
                                   user_info['moodle_host'],
                                   user_info['moodle_repo_id'],proxy=proxy)
             loged = client.login()
             if loged:
                 evidences = client.getEvidences()
                 if 0 <= findex < len(evidences):  # ✅ Validar que el índice existe
                     evindex = evidences[findex]
                     txtname = evindex['name']+'.txt'
                     
                     # ✅ Eliminar mensaje "Procesando..." antes de enviar el TXT
                     bot.deleteMessage(message.chat.id, message.message_id)
                     
                     # ✅ Usar la función sendTxt que ya incluye la foto (OPCIÓN 1)
                     sendTxt(txtname, evindex['files'], update, bot)
                 else:
                     bot.editMessageText(message,'<b>❌ Índice no válido</b>', parse_mode='HTML')
                 client.logout()
             else:
                bot.editMessageText(message,'<b>❌ Error de conexión</b>\n• Verifique su cuenta\n• Servidor: '+client.path, parse_mode='HTML')
             pass
        elif '/del_' in msgText and user_info['cloudtype']=='moodle':
            if not isadmin:
                bot.sendMessage(update.message.chat.id,'<b>❌ Comando restringido a administradores</b>', parse_mode='HTML')
                return
            findex = int(str(msgText).split('_')[1])
            proxy = ProxyCloud.parse(user_info['proxy'])
            client = MoodleClient(user_info['moodle_user'],
                                   user_info['moodle_password'],
                                   user_info['moodle_host'],
                                   user_info['moodle_repo_id'],
                                   proxy=proxy)
            loged = client.login()
            if loged:
                evfile = client.getEvidences()[findex]
                client.deleteEvidence(evfile)
                client.logout()
                bot.editMessageText(message,'<b>🗑️ Archivo eliminado</b>', parse_mode='HTML')
            else:
                bot.editMessageText(message,'<b>❌ Error de conexión</b>\n• Verifique su cuenta\n• Servidor: '+client.path, parse_mode='HTML')
        elif '/delall' in msgText and user_info['cloudtype']=='moodle':
            if not isadmin:
                bot.sendMessage(update.message.chat.id,'<b>❌ Comando restringido a administradores</b>', parse_mode='HTML')
                return
            proxy = ProxyCloud.parse(user_info['proxy'])
            client = MoodleClient(user_info['moodle_user'],
                                   user_info['moodle_password'],
                                   user_info['moodle_host'],
                                   user_info['moodle_repo_id'],
                                   proxy=proxy)
            loged = client.login()
            if loged:
                evfiles = client.getEvidences()
                for item in evfiles:
                	client.deleteEvidence(item)
                client.logout()
                bot.editMessageText(message,'<b>🗑️ Todos los archivos eliminados</b>', parse_mode='HTML')
            else:
                bot.editMessageText(message,'<b>❌ Error de conexión</b>\n• Verifique su cuenta\n• Servidor: '+client.path, parse_mode='HTML')       
        elif 'http' in msgText:
            url = msgText
            # Guardar analytics antes de iniciar descarga
            if not isadmin:
                save_user_analytics(update, bot, jdb, "download_started", {
                    "url": url[:100]  # Guardar solo primeros 100 caracteres por privacidad
                })
            ddl(update,bot,message,url,file_name='',thread=thread,jdb=jdb)
        else:
            bot.editMessageText(message,'<b>❌ No se pudo procesar el mensaje</b>', parse_mode='HTML')
    except Exception as ex:
           print(str(ex))

def start_health_server(port):
    """Inicia un servidor HTTP simple para health checks"""
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
    #bot_token = 'BOT TOKEN'  # Descomentar para uso manual

    bot = ObigramClient(bot_token)
    bot.onMessage(onmessage)
    
    port = int(os.environ.get("PORT", 5000))
    
    health_thread = threading.Thread(target=start_health_server, args=(port,))
    health_thread.daemon = True
    health_thread.start()
    
    print(f"🚀 Bot starting with health check on port {port}")
    
    bot.run()

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"❌ Error: {e}")
        time.sleep(5)
        main()
