from pyobigram.utils import sizeof_fmt,get_file_size,createID,nice_time
from pyobigram.client import ObigramClient,inlineQueryResultArticle
from MoodleClient import MoodleClient

from JDatabase import JsonDatabase
import zipfile
import os
import infos
import xdlink
import mediafire
##from megacli.mega import Mega
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
        if thread.getStore('stop'):
            downloader.stop()
            return
            
        downloadingInfo = ''
        if totalBits == 0:
            percentage = 0
        else:
            percentage = (currentBits / totalBits) * 100
        
        progress_bar = create_progress_bar(percentage)
        total_mb = totalBits / (1024 * 1024)
        current_mb = currentBits / (1024 * 1024)
        speed_mb = speed / (1024 * 1024) if speed > 0 else 0
        
        if speed > 0 and totalBits > 0:
            remaining_bits = totalBits - currentBits
            eta_seconds = remaining_bits / speed
            eta_formatted = format_time(eta_seconds)
        else:
            eta_formatted = "00:00"
        
        downloadingInfo = format_s1_message("📥 Descargando", [
            f"[{progress_bar}]",
            f"✅ Progreso: {percentage:.1f}%",
            f"📦 Tamaño: {current_mb:.2f}/{total_mb:.2f} MB",
            f"⚡ Velocidad: {speed_mb:.2f} MB/s",
            f"⏳ Tiempo: {eta_formatted}",
            f"🚫 Cancelar: /cancel_{thread.cancel_id}"
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
        if thread.getStore('stop'):
            return
            
        part_info = args[4] if len(args) > 4 else None
        
        uploadingInfo = ''
        if totalBits == 0:
            percentage = 0
        else:
            percentage = (currentBits / totalBits) * 100
            
        progress_bar = create_progress_bar(percentage)
        total_mb = totalBits / (1024 * 1024)
        current_mb = currentBits / (1024 * 1024)
        speed_mb = speed / (1024 * 1024) if speed > 0 else 0
        
        if speed > 0 and totalBits > 0:
            remaining_bits = totalBits - currentBits
            eta_seconds = remaining_bits / speed
            eta_formatted = format_time(eta_seconds)
        else:
            eta_formatted = "00:00"
        
        file_display = filename
        if part_info:
            current_part, total_parts, original_name = part_info
            file_display = f"{original_name} (Parte {current_part}/{total_parts})"
        elif originalfile:
            file_display = originalfile
        
        uploadingInfo = format_s1_message("📤 Subiendo", [
            f"[{progress_bar}]",
            f"✅ Progreso: {percentage:.1f}%",
            f"📦 Tamaño: {current_mb:.2f}/{total_mb:.2f} MB",
            f"⚡ Velocidad: {speed_mb:.2f} MB/s",
            f"⏳ Tiempo: {eta_formatted}",
            f"📄 Archivo: {file_display}"
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
            if not loged:
                bot.editMessageText(message,'<b>❌ Error en la plataforma</b>', parse_mode='HTML')
                return None
                
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
                f_size = get_file_size(f)
                resp = None
                iter = 0
                tokenize = False
                
                if user_info['tokenize']!=0:
                   tokenize = True
                   
                part_info = None
                if total_parts > 1:
                    part_info = (i, total_parts, filename)
                
                while resp is None:
                    if thread and thread.getStore('stop'):
                        break
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
                if thread and thread.getStore('stop'):
                    break
                os.unlink(f)
                
            if thread and thread.getStore('stop'):
                return None
                
            if user_info['uploadtype'] == 'evidence':
                try:
                    client.saveEvidence(evidence)
                except:pass
            return draftlist
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
        bot.editMessageText(message,f'<b>❌ Error</b>\n<code>{str(ex)}</code>', parse_mode='HTML')
        return None

def processFile(update,bot,message,file,thread=None,jdb=None):
    try:
        file_size = get_file_size(file)
        username = update.message.sender.username
        getUser = jdb.get_user(username)
        max_file_size = 1024 * 1024 * getUser['zips']
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
            
        if file_size > max_file_size:
            compresingInfo = infos.createCompresing(file,file_size,max_file_size)
            bot.editMessageText(message,compresingInfo)
            zipname = base_name + createID()
            mult_file = zipfile.MultiFile(zipname,max_file_size)
            zip = zipfile.ZipFile(mult_file,  mode='w', compression=zipfile.ZIP_DEFLATED)
            zip.write(file)
            zip.close()
            mult_file.close()
            
            # Usar el nombre base original para la subida, no el archivo temporal
            client = processUploadFiles(original_filename,file_size,mult_file.files,update,bot,message,thread=thread,jdb=jdb)
            try:
                os.unlink(file)
            except:pass
            file_upload_count = len(mult_file.files)
        else:
            # Para archivos pequeños, usar el nombre original
            client = processUploadFiles(original_filename,file_size,[file],update,bot,message,thread=thread,jdb=jdb)
            file_upload_count = 1
            
        if thread and thread.getStore('stop'):
            return
            
        # ACTUALIZAR ESTADÍSTICAS DE USO
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
        evidname = ''
        files = []
        if client:
            if getUser['cloudtype'] == 'moodle':
                if getUser['uploadtype'] == 'evidence':
                    try:
                        evidname = base_name  # Usar el nombre base original
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

            # ✅ EXTENDER WEBSERVICE PARA EVA Y CURSOS
            for i in range(len(files)):
                url = files[i]['directurl']
                # Para Cened
                if 'aulacened.uci.cu' in url:
                    files[i]['directurl'] = url.replace('://aulacened.uci.cu/', '://aulacened.uci.cu/webservice/')
                # Para Eva
                if 'eva.uo.edu.cu' in url:
                    files[i]['directurl'] = url.replace('://eva.uo.edu.cu/', '://eva.uo.edu.cu/webservice/')
                # Para Cursos
                if 'cursos.uo.edu.cu' in url:
                    files[i]['directurl'] = url.replace('://cursos.uo.edu.cu/', '://cursos.uo.edu.cu/webservice/')

            bot.deleteMessage(message.chat.id,message.message_id)
            
            # Usar el nombre original del archivo
            total_parts = file_upload_count
            
            if total_parts > 1:
                finish_title = "✅ Subida Completada"
            else:
                finish_title = "✅ Subida Completada"
                
            # ✅ DETERMINAR MENSAJE SEGÚN LA NUBE
            host = getUser.get('moodle_host', '')
            if 'eva.uo.edu.cu' in host or 'cursos.uo.edu.cu' in host:
                # Para Eva y Cursos - NO mostrar duración
                finishInfo = format_s1_message(finish_title, [
                    f"📄 Archivo: {original_filename}",
                    f"📦 Tamaño total: {sizeof_fmt(file_size)}",
                    f"🔗 Enlaces generados: {len(files)}",
                    f"💾 Partes: {total_parts}" if total_parts > 1 else "💾 Archivo único"
                ])
            else:
                # Para Cened y otras - MOSTRAR duración
                finishInfo = format_s1_message(finish_title, [
                    f"📄 Archivo: {original_filename}",
                    f"📦 Tamaño total: {sizeof_fmt(file_size)}",
                    f"🔗 Enlaces generados: {len(files)}",
                    f"⏱️ Duración enlaces: 8-30 minutos",
                    f"💾 Partes: {total_parts}" if total_parts > 1 else "💾 Archivo único"
                ])
            
            bot.sendMessage(message.chat.id, finishInfo)
            
            if len(files) > 0:
                filesInfo = infos.createFileMsg(original_filename,files)  # Pasar nombre original
                bot.sendMessage(message.chat.id, filesInfo, parse_mode='html')
                txtname = base_name + '.txt'  # Usar nombre base para el TXT
                sendTxt(txtname,files,update,bot)
    except Exception as ex:
        print(f"Error en processFile: {ex}")

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
                megadl(update,bot,message,url,file_name,thread,jdb=jdb)
        
        if hasattr(thread, 'cancel_id') and thread.cancel_id in bot.threads:
            del bot.threads[thread.cancel_id]
    except Exception as ex:
        print(f"Error en ddl: {ex}")

def megadl(update,bot,message,megaurl,file_name='',thread=None,jdb=None):
    try:
        thread.cancel_id = createID()
        bot.threads[thread.cancel_id] = thread
        
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
        
        if hasattr(thread, 'cancel_id') and thread.cancel_id in bot.threads:
            del bot.threads[thread.cancel_id]
    except Exception as ex:
        print(f"Error en megadl: {ex}")
    pass

def sendTxt(name,files,update,bot):
    try:
        with open(name, 'w', encoding='utf-8') as txt:
            txt.write("📄 ENLACES DE DESCARGA\n")
            txt.write("=" * 30 + "\n\n")
            for i, f in enumerate(files, 1):
                txt.write(f"{i}. {f['name']}\n")
                txt.write(f"🔗 {f['directurl']}\n")
                txt.write("-" * 40 + "\n")
        
        info_msg = f"""<b>📄 Archivo de enlaces generado</b>

📎 <b>Nombre:</b> <code>{name}</code>
🔗 <b>Enlaces incluidos:</b> {len(files)}
⏱️ <b>Duración de enlaces:</b> 8-30 minutos

⬇️ <b>Descarga el archivo TXT abajo</b>"""
        
        # Enviar solo el TXT sin thumbnail
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
                    jdb.create_user(username)
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
                           "• /moodle_cened - Configurar Cened\n"
                           "• /moodle_eva - Configurar Eva\n"
                           "• /moodle_cursos - Configurar Cursos\n"
                           "• Enlaces HTTP/HTTPS para subir archivos",
                           parse_mode='HTML')
            return

        if is_text and not msgText.startswith('/') and not 'http' in msgText:
            bot.sendMessage(update.message.chat.id,
                           "<b>🤖 Bot de Subida de Archivos</b>\n\n"
                           "📤 <b>Para subir archivos:</b> Envía un enlace HTTP/HTTPS\n\n"
                           "📝 <b>Para ver comandos disponibles:</b> Usa /start",
                           parse_mode='HTML')
            return

        # ✅ NUEVOS COMANDOS PARA CONFIGURAR PLATAFORMAS
        if '/moodle_cened' in msgText:
            try:
                getUser = user_info
                if getUser:
                    getUser['moodle_host'] = 'https://aulacened.uci.cu/'
                    getUser['moodle_user'] = 'eliel21'
                    getUser['moodle_password'] = 'ElielThali15212115.'
                    getUser['moodle_repo_id'] = 5
                    getUser['uploadtype'] = 'draft'
                    getUser['cloudtype'] = 'moodle'
                    jdb.save_data_user(username, getUser)
                    jdb.save()
                    
                    bot.sendMessage(update.message.chat.id,
                                   "✅ <b>Cened establecido</b>\n\n"
                                   "🚀 <b>Ahora puedes subir archivos a Cened</b>",
                                   parse_mode='HTML')
                else:
                    bot.sendMessage(update.message.chat.id, '❌ Error al configurar Cened', parse_mode='HTML')
            except Exception as e:
                bot.sendMessage(update.message.chat.id, f'❌ Error: {str(e)}', parse_mode='HTML')
            return

        if '/moodle_eva' in msgText:
            try:
                getUser = user_info
                if getUser:
                    getUser['moodle_host'] = 'https://eva.uo.edu.cu/'
                    getUser['moodle_user'] = 'eric.serrano'
                    getUser['moodle_password'] = 'Rulebreaker2316'
                    getUser['moodle_repo_id'] = 4
                    getUser['uploadtype'] = 'draft'
                    getUser['cloudtype'] = 'moodle'
                    jdb.save_data_user(username, getUser)
                    jdb.save()
                    
                    bot.sendMessage(update.message.chat.id,
                                   "✅ <b>Eva establecida</b>\n\n"
                                   "🚀 <b>Ahora puedes subir archivos a Eva</b>",
                                   parse_mode='HTML')
                else:
                    bot.sendMessage(update.message.chat.id, '❌ Error al configurar Eva', parse_mode='HTML')
            except Exception as e:
                bot.sendMessage(update.message.chat.id, f'❌ Error: {str(e)}', parse_mode='HTML')
            return

        if '/moodle_cursos' in msgText:
            try:
                getUser = user_info
                if getUser:
                    getUser['moodle_host'] = 'https://cursos.uo.edu.cu/'
                    getUser['moodle_user'] = 'eric.serrano'
                    getUser['moodle_password'] = 'Rulebreaker2316'
                    getUser['moodle_repo_id'] = 4
                    getUser['uploadtype'] = 'draft'
                    getUser['cloudtype'] = 'moodle'
                    jdb.save_data_user(username, getUser)
                    jdb.save()
                    
                    bot.sendMessage(update.message.chat.id,
                                   "✅ <b>Cursos establecido</b>\n\n"
                                   "🚀 <b>Ahora puedes subir archivos a Cursos</b>",
                                   parse_mode='HTML')
                else:
                    bot.sendMessage(update.message.chat.id, '❌ Error al configurar Cursos', parse_mode='HTML')
            except Exception as e:
                bot.sendMessage(update.message.chat.id, f'❌ Error: {str(e)}', parse_mode='HTML')
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
                # ✅ Asegurar que el host termine con /
                if not host.endswith('/'):
                    host += '/'
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
                if tid in bot.threads:
                    tcancel = bot.threads[tid]
                    msg = tcancel.getStore('msg')
                    tcancel.store('stop',True)
                    time.sleep(2)
                    bot.editMessageText(msg,'<b>❌ Tarea Cancelada</b>', parse_mode='HTML')
                else:
                    bot.sendMessage(update.message.chat.id,'<b>❌ Proceso no encontrado o ya finalizado</b>', parse_mode='HTML')
            except Exception as ex:
                print(str(ex))
                bot.sendMessage(update.message.chat.id,'<b>❌ Error al cancelar</b>', parse_mode='HTML')
            return

        message = bot.sendMessage(update.message.chat.id,'<b>⏳ Procesando...</b>', parse_mode='HTML')

        thread.store('msg',message)

        if '/start' in msgText:
            if isadmin:
                welcome_text = """╭━━━━❰🤖 Bot de Moodle - ADMIN❱━➣
┣⪼ 🚀 Subidas a Moodle/Cloud
┣⪼ 👨‍💻 Desarrollado por: @Eliel_21
┣⪼ ⏱️ Enlaces: 8-30 minutos
┣⪼ 📤 Envía enlaces HTTP/HTTPS

┣⪼ 📝 COMANDOS ADMIN:
┣⪼ /myuser - Mi configuración
┣⪼ /zips - Tamaño de partes
┣⪼ /account - Cuenta Moodle
┣⪼ /host - Servidor Moodle
┣⪼ /repoid - ID Repositorio
┣⪼ /cloud - Tipo de nube
┣⪼ /uptype - Tipo de subida
┣⪼ /proxy - Configurar proxy
┣⪼ /dir - Directorio cloud
┣⪼ /files - Ver archivos
┣⪼ /adduser - Agregar usuario
┣⪼ /banuser - Eliminar usuario
┣⪼ /getdb - Base de datos

┣⪼ 📚 COMANDOS GENERALES:
┣⪼ /tutorial - Guía completa
┣⪼ /moodle_cened - Configurar Cened
┣⪼ /moodle_eva - Configurar Eva
┣⪼ /moodle_cursos - Configurar Cursos
╰━━━━━━━━━━━━━━━➣"""
            else:
                welcome_text = """╭━━━━❰🤖 Bot de Moodle❱━➣
┣⪼ 🚀 Subidas a Moodle/Cloud
┣⪼ 👨‍💻 Desarrollado por: @Eliel_21
┣⪼ ⏱️ Enlaces: 8-30 minutos
┣⪼ 📤 Envía enlaces HTTP/HTTPS

┣⪼ 📝 COMANDOS DISPONIBLES:
┣⪼ /start - Información del bot
┣⪼ /tutorial - Guía completa
┣⪼ /moodle_cened - Configurar Cened
┣⪼ /moodle_eva - Configurar Eva
┣⪼ /moodle_cursos - Configurar Cursos
╰━━━━━━━━━━━━━━━➣"""
            
            bot.deleteMessage(message.chat.id, message.message_id)
            bot.sendMessage(update.message.chat.id, welcome_text)
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
                 if 0 <= findex < len(evidences):
                     evindex = evidences[findex]
                     txtname = evindex['name']+'.txt'
                     
                     bot.deleteMessage(message.chat.id, message.message_id)
                     
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
    
    bot.run()

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"❌ Error: {e}")
        time.sleep(5)
        main()
