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

def downloadFile(downloader,filename,currentBits,totalBits,speed,time,args):
    try:
        bot = args[0]
        message = args[1]
        thread = args[2]
        if thread.getStore('stop'):
            downloader.stop()
        
        # Calcular porcentaje correctamente
        if totalBits > 0:
            percentage = (currentBits / totalBits) * 100
            progress_bar = create_progress_bar(percentage)
            
            # Formatear tamaños y velocidad
            total_mb = totalBits / (1024 * 1024)
            current_mb = currentBits / (1024 * 1024)
            speed_mb = speed / (1024 * 1024) if speed > 0 else 0
            
            # Calcular ETA si hay velocidad
            if speed > 0:
                remaining_bits = totalBits - currentBits
                eta_seconds = remaining_bits / speed
                eta_formatted = nice_time(eta_seconds)
            else:
                eta_formatted = "Calculando..."
            
            downloadingInfo = format_s1_message("📥 Descargando", [
                f"[{progress_bar}]",
                f"✅ Progreso: {percentage:.1f}%",
                f"📦 Tamaño: {current_mb:.2f} / {total_mb:.2f} MB",
                f"⚡ Velocidad: {speed_mb:.2f} MB/s",
                f"⏳ Tiempo: {eta_formatted}"
            ])
        else:
            downloadingInfo = format_s1_message("📥 Descargando", [
                "[⬡⬡⬡⬡⬡⬡⬡⬡⬡⬡]",
                "✅ Progreso: 0%",
                "📦 Tamaño: Calculando...",
                "⚡ Velocidad: 0.00 MB/s",
                "⏳ Tiempo: Calculando..."
            ])
            
        bot.editMessageText(message, downloadingInfo)
    except Exception as ex: 
        print(f"Error en downloadFile: {str(ex)}")
    pass

def uploadFile(filename,currentBits,totalBits,speed,time,args):
    try:
        bot = args[0]
        message = args[1]
        originalfile = args[2]
        thread = args[3]
        
        # Calcular porcentaje correctamente
        if totalBits > 0:
            percentage = (currentBits / totalBits) * 100
            progress_bar = create_progress_bar(percentage)
            
            # Formatear tamaños y velocidad
            total_mb = totalBits / (1024 * 1024)
            current_mb = currentBits / (1024 * 1024)
            speed_mb = speed / (1024 * 1024) if speed > 0 else 0
            
            # Calcular ETA si hay velocidad
            if speed > 0:
                remaining_bits = totalBits - currentBits
                eta_seconds = remaining_bits / speed
                eta_formatted = nice_time(eta_seconds)
            else:
                eta_formatted = "Calculando..."
            
            file_display = originalfile if originalfile else filename
            
            uploadingInfo = format_s1_message("📤 Subiendo", [
                f"[{progress_bar}]",
                f"✅ Progreso: {percentage:.1f}%",
                f"📦 Tamaño: {current_mb:.2f} / {total_mb:.2f} MB",
                f"⚡ Velocidad: {speed_mb:.2f} MB/s",
                f"⏳ Tiempo: {eta_formatted}",
                f"📄 Archivo: {file_display}"
            ])
        else:
            uploadingInfo = format_s1_message("📤 Subiendo", [
                "[⬡⬡⬡⬡⬡⬡⬡⬡⬡⬡]",
                "✅ Progreso: 0%",
                "📦 Tamaño: Calculando...",
                "⚡ Velocidad: 0.00 MB/s",
                "⏳ Tiempo: Calculando...",
                f"📄 Archivo: {filename}"
            ])
            
        bot.editMessageText(message, uploadingInfo)
    except Exception as ex: 
        print(f"Error en uploadFile: {str(ex)}")
    pass

def processUploadFiles(filename,filesize,files,update,bot,message,thread=None,jdb=None):
    try:
        uploadingInfo = format_s1_message("🔄 Preparando", [
            "📄 Iniciando subida...",
            f"📦 Archivo: {filename}",
            f"💾 Tamaño: {filesize/(1024*1024):.2f} MB",
            "⏳ Preparando para subir"
        ])
        bot.editMessageText(message, uploadingInfo)
        
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
                if len(files)>1:
                    originalfile = filename
                draftlist = []
                for f in files:
                    f_size = get_file_size(f)
                    resp = None
                    iter = 0
                    tokenize = False
                    if user_info['tokenize']!=0:
                       tokenize = True
                    while resp is None:
                          if user_info['uploadtype'] == 'evidence':
                             fileid,resp = client.upload_file(f,evidence,fileid,progressfunc=uploadFile,args=(bot,message,originalfile,thread),tokenize=tokenize)
                             draftlist.append(resp)
                          if user_info['uploadtype'] == 'draft':
                             fileid,resp = client.upload_file_draft(f,progressfunc=uploadFile,args=(bot,message,originalfile,thread),tokenize=tokenize)
                             draftlist.append(resp)
                          if user_info['uploadtype'] == 'blog':
                             fileid,resp = client.upload_file_blog(f,progressfunc=uploadFile,args=(bot,message,originalfile,thread),tokenize=tokenize)
                             draftlist.append(resp)
                          if user_info['uploadtype'] == 'calendario':
                             fileid,resp = client.upload_file_calendar(f,progressfunc=uploadFile,args=(bot,message,originalfile,thread),tokenize=tokenize)
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
                errorInfo = format_s1_message("❌ Error Plataforma", [
                    "No se pudo conectar",
                    "Verifique credenciales",
                    "Servidor no disponible"
                ])
                bot.editMessageText(message, errorInfo)
        elif cloudtype == 'cloud':
            tokenize = False
            if user_info['tokenize']!=0:
               tokenize = True
            uploadingInfo = format_s1_message("☁️ Subiendo Nube", [
                "📤 Conectando con la nube...",
                f"📦 Archivo: {filename}",
                "⏳ Iniciando subida"
            ])
            bot.editMessageText(message, uploadingInfo)
            host = user_info['moodle_host']
            user = user_info['moodle_user']
            passw = user_info['moodle_password']
            remotepath = user_info['dir']
            client = NexCloudClient.NexCloudClient(user,passw,host,proxy=proxy)
            loged = client.login()
            if loged:
               originalfile = ''
               if len(files)>1:
                    originalfile = filename
               filesdata = []
               for f in files:
                   data = client.upload_file(f,path=remotepath,progressfunc=uploadFile,args=(bot,message,originalfile,thread),tokenize=tokenize)
                   filesdata.append(data)
                   os.unlink(f)
               return filesdata
        return None
    except Exception as ex:
        errorInfo = format_s1_message("❌ Error Proceso", [
            "Error en el proceso de subida",
            f"Detalle: {str(ex)}",
            "Revise el archivo e intente nuevamente"
        ])
        bot.editMessageText(message, errorInfo)
        return None

def processFile(update,bot,message,file,thread=None,jdb=None):
    file_size = get_file_size(file)
    getUser = jdb.get_user(update.message.sender.username)
    max_file_size = 1024 * 1024 * getUser['zips']
    file_upload_count = 0
    client = None
    findex = 0
    if file_size > max_file_size:
        compresingInfo = format_s1_message("🗜️ Comprimiendo", [
            f"📦 Archivo: {file}",
            f"💾 Tamaño original: {file_size/(1024*1024):.2f} MB",
            f"📁 Tamaño por parte: {max_file_size/(1024*1024):.2f} MB",
            "⏳ Dividiendo archivo..."
        ])
        bot.editMessageText(message, compresingInfo)
        zipname = str(file).split('.')[0] + createID()
        mult_file = zipfile.MultiFile(zipname,max_file_size)
        zip = zipfile.ZipFile(mult_file,  mode='w', compression=zipfile.ZIP_DEFLATED)
        zip.write(file)
        zip.close()
        mult_file.close()
        client = processUploadFiles(file,file_size,mult_file.files,update,bot,message,jdb=jdb)
        try:
            os.unlink(file)
        except:pass
        file_upload_count = len(mult_file.files)
    else:
        client = processUploadFiles(file,file_size,[file],update,bot,message,jdb=jdb)
        file_upload_count = 1
    
    preparingInfo = format_s1_message("📄 Preparando", [
        "✅ Proceso completado",
        "📦 Finalizando subida...",
        "⏳ Generando enlaces"
    ])
    bot.editMessageText(message, preparingInfo)
    
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
        
        finishInfo = format_s1_message("✅ Completado", [
            f"🎯 Archivo: {file}",
            f"📦 Tamaño: {file_size/(1024*1024):.2f} MB",
            f"📁 Partes: {file_upload_count} archivos",
            f"📊 Evidencia: #{findex+1}",
            "⏱️ Enlaces: 8-30 minutos (en algunos casos hasta 30 minutos)"
        ])
        
        filesInfo = infos.createFileMsg(file,files)
        bot.sendMessage(message.chat.id, finishInfo + '\n\n' + filesInfo, parse_mode='html')
        if len(files)>0:
            txtname = str(file).split('/')[-1].split('.')[0] + '.txt'
            sendTxt(txtname,files,update,bot)

def ddl(update,bot,message,url,file_name='',thread=None,jdb=None):
    processingInfo = format_s1_message("🔗 Procesando Enlace", [
        "📥 Analizando URL...",
        f"🔗 Enlace: {url}",
        "⏳ Iniciando descarga"
    ])
    bot.editMessageText(message, processingInfo)
    
    downloader = Downloader()
    file = downloader.download_url(url,progressfunc=downloadFile,args=(bot,message,thread))
    if not downloader.stoping:
        if file:
            processFile(update,bot,message,file,jdb=jdb)
        else:
            megadl(update,bot,message,url,file_name,thread,jdb=jdb)

def megadl(update,bot,message,megaurl,file_name='',thread=None,jdb=None):
    # Importar y usar mega si está disponible
    # megadl = megacli.mega.Mega({'verbose': True})
    # megadl.login()
    # ... (código mega existente)
    pass

def sendTxt(name,files,update,bot):
    """Envía archivo txt con enlaces"""
    try:
        # Crear el archivo txt
        with open(name, 'w') as txt:
            for i, f in enumerate(files):
                separator = '\n' if i < len(files) - 1 else ''
                txt.write(f['directurl'] + separator)
        
        # Mensaje informativo con estilo S1
        info_msg = format_s1_message("📄 Archivo de Enlaces", [
            f"📎 Nombre: {name}",
            f"🔗 Enlaces incluidos: {len(files)}",
            "⏱️ Duración: 8-30 minutos (en algunos casos hasta 30 minutos)",
            "⬇️ Descarga el archivo TXT abajo"
        ])
        
        bot.sendMessage(update.message.chat.id, info_msg)
        
        # Enviar el archivo txt
        bot.sendFile(update.message.chat.id, name)
        
        # Limpiar archivo temporal
        os.unlink(name)
        
    except Exception as ex:
        print(f"Error en sendTxt: {str(ex)}")
        # Fallback seguro
        try:
            if os.path.exists(name):
                bot.sendFile(update.message.chat.id, name)
                os.unlink(name)
        except:
            pass

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
            '/cloud', '/uptype', '/proxy', '/dir', '/tutorial', 
            '/myuser', '/files', '/txt_', '/del_', '/delall'
        ]):
            restricted_msg = format_s1_message("🚫 Acceso Restringido", [
                "Comandos de configuración bloqueados",
                "Disponibles solo para administradores",
                "",
                "✅ Puedes usar:",
                "• Enlaces HTTP/HTTPS",
                "• Comando /start para información"
            ])
            bot.sendMessage(update.message.chat.id, restricted_msg)
            return

        # Si es un mensaje de texto normal (no comando, no enlace)
        if is_text and not msgText.startswith('/') and not 'http' in msgText:
            if isadmin:
                admin_msg = format_s1_message("👋 ¡Hola Administrador!", [
                    "📝 Comandos disponibles:",
                    "• /start - Información del bot",
                    "• /tutorial - Guía de uso", 
                    "• /myuser - Mi configuración",
                    "• /adduser @user - Agregar usuario",
                    "• /banuser @user - Eliminar usuario",
                    "• /getdb - Base de datos",
                    "",
                    "🌐 O envía enlace HTTP/HTTPS"
                ])
                bot.sendMessage(update.message.chat.id, admin_msg)
            else:
                user_msg = format_s1_message("👋 ¡Bienvenido!", [
                    "🤖 Bot de Subidas a Moodle",
                    "",
                    "📤 Para usar el bot:",
                    "1. Envía enlace HTTP/HTTPS",
                    "2. Bot lo procesará automáticamente", 
                    "3. Recibirás enlaces de descarga",
                    "",
                    "🔗 Ejemplo: https://ejemplo.com/archivo.zip",
                    "⏱️ Enlaces: 8-30 minutos (en algunos casos hasta 30 minutos)",
                    "",
                    "💡 Usa /start para más información"
                ])
                bot.sendMessage(update.message.chat.id, user_msg)
            return

        # comandos de admin (solo para administrador)
        if '/adduser' in msgText:
            isadmin = jdb.is_admin(username)
            if isadmin:
                try:
                    user = str(msgText).split(' ')[1]
                    jdb.create_user(user)
                    jdb.save()
                    success_msg = format_s1_message("✅ Usuario Agregado", [
                        f"Usuario: @{user}",
                        "Ahora tiene acceso al bot",
                        "Puede enviar enlaces para subir"
                    ])
                    bot.sendMessage(update.message.chat.id, success_msg)
                except:
                    error_msg = format_s1_message("❌ Error en Comando", [
                        "Formato correcto:",
                        "/adduser username",
                        "Ejemplo: /adduser juan123"
                    ])
                    bot.sendMessage(update.message.chat.id, error_msg)
            else:
                no_permission_msg = format_s1_message("❌ Sin Permisos", [
                    "Comando restringido",
                    "Solo para administradores",
                    "Contacta al administrador"
                ])
                bot.sendMessage(update.message.chat.id, no_permission_msg)
            return
            
        if '/banuser' in msgText:
            isadmin = jdb.is_admin(username)
            if isadmin:
                try:
                    user = str(msgText).split(' ')[1]
                    if user == username:
                        self_ban_msg = format_s1_message("❌ Error", [
                            "No puede banearse a sí mismo",
                            "Operación no permitida",
                            "Contacte a otro administrador"
                        ])
                        bot.sendMessage(update.message.chat.id, self_ban_msg)
                        return
                    jdb.remove(user)
                    jdb.save()
                    ban_msg = format_s1_message("🚫 Usuario Baneado", [
                        f"Usuario: @{user}",
                        "Acceso al bot revocado",
                        "No podrá enviar más enlaces"
                    ])
                    bot.sendMessage(update.message.chat.id, ban_msg)
                except:
                    error_msg = format_s1_message("❌ Error en Comando", [
                        "Formato correcto:",
                        "/banuser username", 
                        "Ejemplo: /banuser juan123"
                    ])
                    bot.sendMessage(update.message.chat.id, error_msg)
            else:
                no_permission_msg = format_s1_message("❌ Sin Permisos", [
                    "Comando restringido",
                    "Solo para administradores",
                    "Contacta al administrador"
                ])
                bot.sendMessage(update.message.chat.id, no_permission_msg)
            return
            
        if '/getdb' in msgText:
            isadmin = jdb.is_admin(username)
            if isadmin:
                db_msg = format_s1_message("📦 Base de Datos", [
                    "Base de datos del bot",
                    "Contiene información de usuarios",
                    "Enviando archivo..."
                ])
                bot.sendMessage(update.message.chat.id, db_msg)
                bot.sendFile(update.message.chat.id,'database.jdb')
            else:
                no_permission_msg = format_s1_message("❌ Sin Permisos", [
                    "Comando restringido",
                    "Solo para administradores",
                    "Contacta al administrador"
                ])
                bot.sendMessage(update.message.chat.id, no_permission_msg)
            return

        # comandos de usuario (solo para administrador)
        if '/tutorial' in msgText:
            if not isadmin:
                no_permission_msg = format_s1_message("❌ Comando Restringido", [
                    "Solo disponible para administradores",
                    "Contacta al administrador del bot",
                    "Para acceder a esta función"
                ])
                bot.sendMessage(update.message.chat.id, no_permission_msg)
                return
            try:
                tuto = open('tuto.txt','r')
                tutorial_content = tuto.read()
                tuto.close()
                # Si el tutorial es largo, usar estilo S1
                if len(tutorial_content.split('\n')) > 3:
                    tutorial_lines = tutorial_content.split('\n')
                    tutorial_msg = format_s1_message("📚 Tutorial", tutorial_lines[:10])  # Máximo 10 líneas
                    bot.sendMessage(update.message.chat.id, tutorial_msg)
                else:
                    bot.sendMessage(update.message.chat.id, tutorial_content)
            except:
                no_tuto_msg = format_s1_message("📚 Tutorial", [
                    "Archivo de tutorial no disponible",
                    "Contacta al administrador",
                    "Para obtener ayuda"
                ])
                bot.sendMessage(update.message.chat.id, no_tuto_msg)
            return
            
        if '/myuser' in msgText:
            if not isadmin:
                no_permission_msg = format_s1_message("❌ Comando Restringido", [
                    "Solo disponible para administradores",
                    "Contacta al administrador del bot",
                    "Para ver tu configuración"
                ])
                bot.sendMessage(update.message.chat.id, no_permission_msg)
                return
            getUser = user_info
            if getUser:
                statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                # Convertir a formato S1 si es largo
                if len(statInfo.split('\n')) > 3:
                    stat_lines = statInfo.split('\n')
                    stat_msg = format_s1_message("👤 Mi Configuración", stat_lines)
                    bot.sendMessage(update.message.chat.id, stat_msg, parse_mode='HTML')
                else:
                    bot.sendMessage(update.message.chat.id, statInfo, parse_mode='HTML')
                return
                
        if '/zips' in msgText:
            if not isadmin:
                no_permission_msg = format_s1_message("❌ Comando Restringido", [
                    "Solo disponible para administradores",
                    "Contacta al administrador del bot",
                    "Para cambiar configuración"
                ])
                bot.sendMessage(update.message.chat.id, no_permission_msg)
                return
            getUser = user_info
            if getUser:
                try:
                   size = int(str(msgText).split(' ')[1])
                   getUser['zips'] = size
                   jdb.save_data_user(username,getUser)
                   jdb.save()
                   zip_msg = format_s1_message("✅ Zips Configurados", [
                       f"Tamaño: {sizeof_fmt(size*1024*1024)}",
                       f"Por parte: {size} MB", 
                       "Configuración guardada correctamente"
                   ])
                   bot.sendMessage(update.message.chat.id, zip_msg)
                except:
                   error_msg = format_s1_message("❌ Error en Comando", [
                       "Formato incorrecto",
                       "Uso correcto:",
                       "/zips tamaño_en_mb",
                       "Ejemplo: /zips 100"
                   ])
                   bot.sendMessage(update.message.chat.id, error_msg)
                return
                
        if '/account' in msgText:
            if not isadmin:
                no_permission_msg = format_s1_message("❌ Comando Restringido", [
                    "Solo disponible para administradores",
                    "Contacta al administrador del bot",
                    "Para cambiar credenciales"
                ])
                bot.sendMessage(update.message.chat.id, no_permission_msg)
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
                    success_msg = format_s1_message("✅ Cuenta Actualizada", [
                        f"Usuario: {user}",
                        "Contraseña actualizada",
                        "Configuración guardada"
                    ])
                    bot.sendMessage(update.message.chat.id, success_msg)
            except:
                error_msg = format_s1_message("❌ Error en Comando", [
                    "Formato incorrecto",
                    "Uso correcto:",
                    "/account usuario,contraseña",
                    "Ejemplo: /account miUsuario,miPass123"
                ])
                bot.sendMessage(update.message.chat.id, error_msg)
            return
            
        if '/host' in msgText:
            if not isadmin:
                no_permission_msg = format_s1_message("❌ Comando Restringido", [
                    "Solo disponible para administradores",
                    "Contacta al administrador del bot",
                    "Para cambiar servidor"
                ])
                bot.sendMessage(update.message.chat.id, no_permission_msg)
                return
            try:
                cmd = str(msgText).split(' ',2)
                host = cmd[1]
                getUser = user_info
                if getUser:
                    getUser['moodle_host'] = host
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    success_msg = format_s1_message("✅ Servidor Actualizado", [
                        f"Host: {host}",
                        "Configuración guardada",
                        "Reinicia operaciones si es necesario"
                    ])
                    bot.sendMessage(update.message.chat.id, success_msg)
            except:
                error_msg = format_s1_message("❌ Error en Comando", [
                    "Formato incorrecto",
                    "Uso correcto:",
                    "/host url_del_moodle",
                    "Ejemplo: /host https://mi-moodle.com"
                ])
                bot.sendMessage(update.message.chat.id, error_msg)
            return
            
        if '/repoid' in msgText:
            if not isadmin:
                no_permission_msg = format_s1_message("❌ Comando Restringido", [
                    "Solo disponible para administradores",
                    "Contacta al administrador del bot",
                    "Para cambiar repositorio"
                ])
                bot.sendMessage(update.message.chat.id, no_permission_msg)
                return
            try:
                cmd = str(msgText).split(' ',2)
                repoid = int(cmd[1])
                getUser = user_info
                if getUser:
                    getUser['moodle_repo_id'] = repoid
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    success_msg = format_s1_message("✅ Repositorio Actualizado", [
                        f"ID Repositorio: {repoid}",
                        "Configuración guardada",
                        "Para próximas subidas"
                    ])
                    bot.sendMessage(update.message.chat.id, success_msg)
            except:
                error_msg = format_s1_message("❌ Error en Comando", [
                    "Formato incorrecto",
                    "Uso correcto:",
                    "/repoid id_del_repositorio",
                    "Ejemplo: /repoid 5"
                ])
                bot.sendMessage(update.message.chat.id, error_msg)
            return
            
        if '/tokenize_on' in msgText:
            if not isadmin:
                no_permission_msg = format_s1_message("❌ Comando Restringido", [
                    "Solo disponible para administradores",
                    "Contacta al administrador del bot",
                    "Para cambiar tokenización"
                ])
                bot.sendMessage(update.message.chat.id, no_permission_msg)
                return
            try:
                getUser = user_info
                if getUser:
                    getUser['tokenize'] = 1
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    success_msg = format_s1_message("✅ Tokenización Activada", [
                        "Tokenización: ACTIVADA",
                        "Archivos se tokenizarán",
                        "Configuración guardada"
                    ])
                    bot.sendMessage(update.message.chat.id, success_msg)
            except:
                error_msg = format_s1_message("❌ Error", [
                    "No se pudo activar tokenización",
                    "Intente nuevamente",
                    "Contacte soporte si persiste"
                ])
                bot.sendMessage(update.message.chat.id, error_msg)
            return
            
        if '/tokenize_off' in msgText:
            if not isadmin:
                no_permission_msg = format_s1_message("❌ Comando Restringido", [
                    "Solo disponible para administradores",
                    "Contacta al administrador del bot",
                    "Para cambiar tokenización"
                ])
                bot.sendMessage(update.message.chat.id, no_permission_msg)
                return
            try:
                getUser = user_info
                if getUser:
                    getUser['tokenize'] = 0
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    success_msg = format_s1_message("✅ Tokenización Desactivada", [
                        "Tokenización: DESACTIVADA",
                        "Archivos no se tokenizarán",
                        "Configuración guardada"
                    ])
                    bot.sendMessage(update.message.chat.id, success_msg)
            except:
                error_msg = format_s1_message("❌ Error", [
                    "No se pudo desactivar tokenización",
                    "Intente nuevamente",
                    "Contacte soporte si persiste"
                ])
                bot.sendMessage(update.message.chat.id, error_msg)
            return
            
        if '/cloud' in msgText:
            if not isadmin:
                no_permission_msg = format_s1_message("❌ Comando Restringido", [
                    "Solo disponible para administradores",
                    "Contacta al administrador del bot",
                    "Para cambiar tipo de nube"
                ])
                bot.sendMessage(update.message.chat.id, no_permission_msg)
                return
            try:
                cmd = str(msgText).split(' ',2)
                repoid = cmd[1]
                getUser = user_info
                if getUser:
                    getUser['cloudtype'] = repoid
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    success_msg = format_s1_message("✅ Tipo de Nube Actualizado", [
                        f"Tipo: {repoid}",
                        "Configuración guardada",
                        "Reinicia operaciones si es necesario"
                    ])
                    bot.sendMessage(update.message.chat.id, success_msg)
            except:
                error_msg = format_s1_message("❌ Error en Comando", [
                    "Formato incorrecto",
                    "Uso correcto:",
                    "/cloud (moodle o cloud)",
                    "Ejemplo: /cloud moodle"
                ])
                bot.sendMessage(update.message.chat.id, error_msg)
            return
            
        if '/uptype' in msgText:
            if not isadmin:
                no_permission_msg = format_s1_message("❌ Comando Restringido", [
                    "Solo disponible para administradores",
                    "Contacta al administrador del bot",
                    "Para cambiar tipo de subida"
                ])
                bot.sendMessage(update.message.chat.id, no_permission_msg)
                return
            try:
                cmd = str(msgText).split(' ',2)
                type = cmd[1]
                getUser = user_info
                if getUser:
                    getUser['uploadtype'] = type
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    success_msg = format_s1_message("✅ Tipo de Subida Actualizado", [
                        f"Tipo: {type}",
                        "Configuración guardada",
                        "Para próximas subidas"
                    ])
                    bot.sendMessage(update.message.chat.id, success_msg)
            except:
                error_msg = format_s1_message("❌ Error en Comando", [
                    "Formato incorrecto",
                    "Uso correcto:",
                    "/uptype (evidence, draft, blog, calendario)",
                    "Ejemplo: /uptype evidence"
                ])
                bot.sendMessage(update.message.chat.id, error_msg)
            return
            
        if '/proxy' in msgText:
            if not isadmin:
                no_permission_msg = format_s1_message("❌ Comando Restringido", [
                    "Solo disponible para administradores",
                    "Contacta al administrador del bot",
                    "Para cambiar proxy"
                ])
                bot.sendMessage(update.message.chat.id, no_permission_msg)
                return
            try:
                cmd = str(msgText).split(' ',2)
                proxy = cmd[1]
                getUser = user_info
                if getUser:
                    getUser['proxy'] = proxy
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    success_msg = format_s1_message("✅ Proxy Actualizado", [
                        f"Proxy: {proxy}",
                        "Configuración guardada",
                        "Para próximas conexiones"
                    ])
                    bot.sendMessage(update.message.chat.id, success_msg)
            except:
                if user_info:
                    user_info['proxy'] = ''
                    jdb.save_data_user(username,user_info)
                    jdb.save()
                    success_msg = format_s1_message("✅ Proxy Eliminado", [
                        "Proxy: ELIMINADO",
                        "Configuración guardada",
                        "Conexiones sin proxy"
                    ])
                    bot.sendMessage(update.message.chat.id, success_msg)
            return
            
        if '/dir' in msgText:
            if not isadmin:
                no_permission_msg = format_s1_message("❌ Comando Restringido", [
                    "Solo disponible para administradores",
                    "Contacta al administrador del bot",
                    "Para cambiar directorio"
                ])
                bot.sendMessage(update.message.chat.id, no_permission_msg)
                return
            try:
                cmd = str(msgText).split(' ',2)
                repoid = cmd[1]
                getUser = user_info
                if getUser:
                    getUser['dir'] = repoid + '/'
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    success_msg = format_s1_message("✅ Directorio Actualizado", [
                        f"Directorio: {repoid}/",
                        "Configuración guardada",
                        "Para próximas subidas"
                    ])
                    bot.sendMessage(update.message.chat.id, success_msg)
            except:
                error_msg = format_s1_message("❌ Error en Comando", [
                    "Formato incorrecto",
                    "Uso correcto:",
                    "/dir nombre_carpeta",
                    "Ejemplo: /dir mis_archivos"
                ])
                bot.sendMessage(update.message.chat.id, error_msg)
            return
            
        if '/cancel_' in msgText:
            try:
                cmd = str(msgText).split('_',2)
                tid = cmd[1]
                tcancel = bot.threads[tid]
                msg = tcancel.getStore('msg')
                tcancel.store('stop',True)
                time.sleep(3)
                cancel_msg = format_s1_message("❌ Tarea Cancelada", [
                    "Proceso detenido por usuario",
                    "Operación interrumpida",
                    "Puede iniciar nueva tarea"
                ])
                bot.editMessageText(msg, cancel_msg)
            except Exception as ex:
                print(str(ex))
            return

        initial_msg = format_s1_message("⏳ Procesando", [
            "Analizando solicitud...",
            "Preparando sistema",
            "Iniciando proceso"
        ])
        message = bot.sendMessage(update.message.chat.id, initial_msg)

        thread.store('msg',message)

        if '/start' in msgText:
            welcome_text = """╭━━━━❰🤖 Bot de Moodle❱━➣
┣⪼ 🚀 Subidas a Moodle  
┣⪼ 👨‍💻 Desarrollado por: @Eliel_21
┣⪼ ⏱️ Enlaces: 8-30 minutos (en algunos casos hasta 30 minutos)
┣⪼ 
┣⪼ 📤 Envía cualquier enlace HTTP/HTTPS
┣⪼ para comenzar a subir archivos
╰━━━━━━━━━━━━━━━➣"""
            
            bot.editMessageText(message, welcome_text)
            
        elif '/files' == msgText and user_info['cloudtype']=='moodle':
             if not isadmin:
                no_permission_msg = format_s1_message("❌ Comando Restringido", [
                    "Solo disponible para administradores",
                    "Contacta al administrador del bot",
                    "Para ver archivos"
                ])
                bot.sendMessage(update.message.chat.id, no_permission_msg)
                return
             
             files_msg = format_s1_message("📁 Buscando Archivos", [
                 "Conectando con Moodle...",
                 "Obteniendo lista de archivos",
                 "⏳ Espere por favor"
             ])
             bot.editMessageText(message, files_msg)
             
             proxy = ProxyCloud.parse(user_info['proxy'])
             client = MoodleClient(user_info['moodle_user'],
                                   user_info['moodle_password'],
                                   user_info['moodle_host'],
                                   user_info['moodle_repo_id'],proxy=proxy)
             loged = client.login()
             if loged:
                 files = client.getEvidences()
                 filesInfo = infos.createFilesMsg(files)
                 # Convertir a formato S1 si es largo
                 if len(filesInfo.split('\n')) > 3:
                     files_lines = filesInfo.split('\n')
                     files_msg = format_s1_message("📁 Archivos Encontrados", files_lines[:15])  # Máximo 15 líneas
                     bot.editMessageText(message, files_msg, parse_mode='HTML')
                 else:
                     bot.editMessageText(message, filesInfo, parse_mode='HTML')
                 client.logout()
             else:
                error_msg = format_s1_message("❌ Error de Conexión", [
                    "No se pudo conectar a Moodle",
                    "Verifique su cuenta y servidor",
                    f"Servidor: {client.path}"
                ])
                bot.editMessageText(message, error_msg)
                
        elif '/txt_' in msgText and user_info['cloudtype']=='moodle':
             if not isadmin:
                no_permission_msg = format_s1_message("❌ Comando Restringido", [
                    "Solo disponible para administradores",
                    "Contacta al administrador del bot",
                    "Para generar TXT"
                ])
                bot.sendMessage(update.message.chat.id, no_permission_msg)
                return
             
             txt_msg = format_s1_message("📄 Generando TXT", [
                 "Preparando archivo de enlaces...",
                 "Obteniendo información",
                 "⏳ Procesando"
             ])
             bot.editMessageText(message, txt_msg)
             
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
                 evindex = evidences[findex]
                 txtname = evindex['name']+'.txt'
                 sendTxt(txtname,evindex['files'],update,bot)
                 client.logout()
                 success_msg = format_s1_message("✅ TXT Generado", [
                     f"Archivo: {txtname}",
                     "Enlaces compilados correctamente",
                     "Descarga disponible"
                 ])
                 bot.editMessageText(message, success_msg)
             else:
                error_msg = format_s1_message("❌ Error de Conexión", [
                    "No se pudo conectar a Moodle",
                    "Verifique su cuenta y servidor",
                    f"Servidor: {client.path}"
                ])
                bot.editMessageText(message, error_msg)
             pass
             
        elif '/del_' in msgText and user_info['cloudtype']=='moodle':
            if not isadmin:
                no_permission_msg = format_s1_message("❌ Comando Restringido", [
                    "Solo disponible para administradores",
                    "Contacta al administrador del bot",
                    "Para eliminar archivos"
                ])
                bot.sendMessage(update.message.chat.id, no_permission_msg)
                return
                
            delete_msg = format_s1_message("🗑️ Eliminando", [
                "Preparando eliminación...",
                "Conectando con Moodle",
                "⏳ Procesando"
            ])
            bot.editMessageText(message, delete_msg)
            
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
                success_msg = format_s1_message("✅ Archivo Eliminado", [
                    "Eliminación completada",
                    "Archivo removido de Moodle",
                    "Operación exitosa"
                ])
                bot.editMessageText(message, success_msg)
            else:
                error_msg = format_s1_message("❌ Error de Conexión", [
                    "No se pudo conectar a Moodle",
                    "Verifique su cuenta y servidor",
                    f"Servidor: {client.path}"
                ])
                bot.editMessageText(message, error_msg)
                
        elif '/delall' in msgText and user_info['cloudtype']=='moodle':
            if not isadmin:
                no_permission_msg = format_s1_message("❌ Comando Restringido", [
                    "Solo disponible para administradores",
                    "Contacta al administrador del bot",
                    "Para eliminar archivos"
                ])
                bot.sendMessage(update.message.chat.id, no_permission_msg)
                return
                
            delete_all_msg = format_s1_message("🗑️ Eliminando Todo", [
                "Preparando eliminación total...",
                "Conectando con Moodle",
                "⏳ Esto puede tomar tiempo"
            ])
            bot.editMessageText(message, delete_all_msg)
            
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
                success_msg = format_s1_message("✅ Todos Eliminados", [
                    f"Eliminados: {len(evfiles)} archivos",
                    "Limpieza completada",
                    "Todos los archivos removidos"
                ])
                bot.editMessageText(message, success_msg)
            else:
                error_msg = format_s1_message("❌ Error de Conexión", [
                    "No se pudo conectar a Moodle",
                    "Verifique su cuenta y servidor",
                    f"Servidor: {client.path}"
                ])
                bot.editMessageText(message, error_msg)       
        elif 'http' in msgText:
            url = msgText
            ddl(update,bot,message,url,file_name='',thread=thread,jdb=jdb)
        else:
            error_msg = format_s1_message("❌ Error", [
                "No se pudo procesar el mensaje",
                "Comando no reconocido",
                "Use /start para ver opciones disponibles"
            ])
            bot.editMessageText(message, error_msg)
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
                
                # Responder con HTTP 200 OK
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

    #decomentar abajo y modificar solo si se va a poner el token del bot manual
    #bot_token = 'BOT TOKEN'

    bot = ObigramClient(bot_token)
    bot.onMessage(onmessage)
    
    # Obtener puerto de Render
    port = int(os.environ.get("PORT", 5000))
    
    # Iniciar servidor de health check en un hilo separado
    health_thread = threading.Thread(target=start_health_server, args=(port,))
    health_thread.daemon = True
    health_thread.start()
    
    print(f"🚀 Bot starting with health check on port {port}")
    
    # Ejecutar el bot
    bot.run()

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"❌ Error: {e}")
        # Reintentar después de 5 segundos
        time.sleep(5)
        main()
