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

def downloadFile(downloader,filename,currentBits,totalBits,speed,time_elapsed,args):
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
        
        # CÁLCULO SIMPLIFICADO Y MÁS PRECISO DEL TIEMPO
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

def uploadFile(filename,currentBits,totalBits,speed,time_elapsed,args):
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
        
        # CÁLCULO SIMPLIFICADO Y MÁS PRECISO DEL TIEMPO
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
                bot.editMessageText(message,'<b>❌ Error en la plataforma - Login falló</b>', parse_mode='HTML')
                return None
            
            # VERIFICACIÓN MEJORADA PARA EVIDENCIAS
            if user_info['uploadtype'] == 'evidence':
                evidence_name = str(filename).split('.')[0]
                print(f"🔄 Creando evidencia: {evidence_name}")
                
                evidence = client.createEvidence(evidence_name)
                
                if not evidence:
                    bot.editMessageText(message,'<b>❌ Error: No se pudo crear la evidencia</b>', parse_mode='HTML')
                    return None
                else:
                    print(f"✅ Evidencia creada exitosamente: {evidence['name']} (ID: {evidence.get('id', 'unknown')})")

            originalfile = ''
            total_parts = len(files)
            draftlist = []
            upload_success = False
            
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
                
                while resp is None and iter < 5:  # Límite de intentos
                    if thread and thread.getStore('stop'):
                        break
                        
                    try:
                        if user_info['uploadtype'] == 'evidence':
                            print(f"🔄 Subiendo archivo {i}/{total_parts} a evidencia...")
                            fileid, resp = client.upload_file(f, evidence, fileid,
                                                            progressfunc=uploadFile,
                                                            args=(bot,message,filename,thread,part_info),
                                                            tokenize=tokenize)
                            if resp:
                                draftlist.append(resp)
                                upload_success = True
                                print(f"✅ Archivo {i}/{total_parts} subido exitosamente a evidencia")
                            else:
                                print(f"❌ Intento {iter+1} falló para archivo {i}")
                                
                        if user_info['uploadtype'] == 'draft':
                            fileid,resp = client.upload_file_draft(f,
                                                                  progressfunc=uploadFile,
                                                                  args=(bot,message,filename,thread,part_info),
                                                                  tokenize=tokenize)
                            if resp:
                                draftlist.append(resp)
                                upload_success = True
                        if user_info['uploadtype'] == 'blog':
                            fileid,resp = client.upload_file_blog(f,
                                                                 progressfunc=uploadFile,
                                                                 args=(bot,message,filename,thread,part_info),
                                                                 tokenize=tokenize)
                            if resp:
                                draftlist.append(resp)
                                upload_success = True
                        if user_info['uploadtype'] == 'calendario':
                            fileid,resp = client.upload_file_calendar(f,
                                                                     progressfunc=uploadFile,
                                                                     args=(bot,message,filename,thread,part_info),
                                                                     tokenize=tokenize)
                            if resp:
                                draftlist.append(resp)
                                upload_success = True
                    except Exception as upload_error:
                        print(f"❌ Error en upload: {str(upload_error)}")
                        resp = None
                    
                    iter += 1
                    if iter >= 5:
                        print(f"🚫 Máximo de intentos alcanzado para archivo {i}")
                        break
                
                if thread and thread.getStore('stop'):
                    break
                    
                # Limpiar archivo temporal solo si se subió exitosamente
                if resp:
                    try:
                        os.unlink(f)
                        print(f"🧹 Archivo temporal {i} eliminado")
                    except:
                        pass
                else:
                    print(f"⚠️ Archivo {i} no se pudo subir, conservando temporal")
            
            # VERIFICACIÓN FINAL Y GUARDADO PARA EVIDENCIAS
            if thread and thread.getStore('stop'):
                return None
                
            if user_info['uploadtype'] == 'evidence' and upload_success:
                print(f"💾 Guardando evidencia: {evidence['name']}")
                saved_evidence = client.saveEvidence(evidence)
                if not saved_evidence:
                    bot.editMessageText(message, '<b>❌ Error: No se pudo guardar la evidencia</b>', parse_mode='HTML')
                    return None
                else:
                    print("🎉 Evidencia guardada exitosamente en la plataforma")
            
            return draftlist if upload_success else None
            
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
            upload_success = False
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
                if data:
                    filesdata.append(data)
                    upload_success = True
                    os.unlink(f)
                
            if thread and thread.getStore('stop'):
                return None
                
            return filesdata if upload_success else None
        return None
    except Exception as ex:
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
        elif getUser['moodle_host'] == 'https://moodle.instec.cu/':  # NUEVA PLATAFORMA INSTEC
            max_file_size = 1024 * 1024 * 99  # 99 MB para INSTEC
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
            
            # CREAR ARCHIVO TEMPORAL CON NOMBRE CORRECTO
            temp_dir = "temp_" + createID()
            os.makedirs(temp_dir, exist_ok=True)
            
            # Copiar el archivo a un directorio temporal con su nombre original
            temp_file_path = os.path.join(temp_dir, original_filename)
            import shutil
            shutil.copy2(file, temp_file_path)
            
            zipname = base_name + createID()
            mult_file = zipfile.MultiFile(zipname, max_file_size)
            
            # CREAR ZIP CON EL ARCHIVO Y SU NOMBRE ORIGINAL
            with zipfile.ZipFile(mult_file, mode='w', compression=zipfile.ZIP_DEFLATED) as zipf:
                # Agregar el archivo con su nombre original preservado
                zipf.write(temp_file_path, arcname=original_filename)
            
            mult_file.close()
            
            # LIMPIAR ARCHIVO TEMPORAL
            try:
                shutil.rmtree(temp_dir)
            except: pass
            
            # Usar el nombre base original para la subida
            client = processUploadFiles(original_filename, file_size, mult_file.files, update, bot, message, thread=thread, jdb=jdb)
            
            try:
                os.unlink(file)
            except:pass
            file_upload_count = len(mult_file.files)
            
            # LIMPIAR ARCHIVOS TEMPORALES ZIP
            try:
                for zip_file in mult_file.files:
                    if os.path.exists(zip_file):
                        os.unlink(zip_file)
            except:pass
                        
        else:
            # Para archivos pequeños o ya comprimidos, usar el nombre original
            client = processUploadFiles(original_filename,file_size,[file],update,bot,message,thread=thread,jdb=jdb)
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
                    except Exception as e:
                        print(f"Error obteniendo evidencias: {e}")
                if getUser['uploadtype'] == 'draft' or getUser['uploadtype'] == 'blog' or getUser['uploadtype']=='calendario':
                   for draft in client:
                       if draft and 'url' in draft:
                           files.append({'name':draft.get('file', original_filename),'directurl':draft['url']})
            else:
                for data in client:
                    if data and 'url' in data:
                        files.append({'name':data.get('name', original_filename),'directurl':data['url']})

            # COMPATIBILIDAD CON NUBES UO - Incluir webservice para todas las plataformas
            for i in range(len(files)):
                url = files[i]['directurl']
                
                # Para CENED - reemplazo existente
                if 'aulacened.uci.cu' in url:
                    files[i]['directurl'] = url.replace('://aulacened.uci.cu/', '://aulacened.uci.cu/webservice/')
                
                # Para EVA UO - agregar webservice
                elif 'eva.uo.edu.cu' in url and '/webservice/' not in url:
                    files[i]['directurl'] = url.replace('://eva.uo.edu.cu/', '://eva.uo.edu.cu/webservice/')
                
                # Para CURSOS UO - agregar webservice  
                elif 'cursos.uo.edu.cu' in url and '/webservice/' not in url:
                    files[i]['directurl'] = url.replace('://cursos.uo.edu.cu/', '://cursos.uo.edu.cu/webservice/')

            bot.deleteMessage(message.chat.id,message.message_id)
            
            # Usar el nombre original del archivo
            total_parts = file_upload_count
            
            # MENSAJE FINAL SEGÚN PLATAFORMA
            platform_name = get_platform_name(getUser['moodle_host'])
            finish_title = "✅ Subida Completada"

            if platform_name == 'CENED':
                finishInfo = format_s1_message(finish_title, [
                    f"📄 Archivo: {original_filename}",
                    f"📦 Tamaño total: {sizeof_fmt(file_size)}",
                    f"🔗 Enlaces generados: {len(files)}",
                    f"⏱️ Duración enlaces: 8-30 minutos",
                    f"💾 Partes: {total_parts}" if total_parts > 1 else "💾 Archivo único"
                ])
            elif platform_name == 'INSTEC':  # NUEVA PLATAFORMA CON CREDENCIALES
                # Obtener las credenciales del usuario actual
                user_instec = getUser['moodle_user']
                pass_instec = getUser['moodle_password']
                
                finishInfo = format_s1_message(finish_title, [
                    f"📄 Archivo: {original_filename}",
                    f"📦 Tamaño total: {sizeof_fmt(file_size)}",
                    f"🔗 Enlaces generados: {len(files)}",
                    f"⏱️ Duración enlaces: Desconocido",
                    f"💾 Partes: {total_parts}" if total_parts > 1 else "💾 Archivo único",
                    f"🔐 Descarga vía cuenta",
                    f"👤 Usuario: {user_instec}",
                    f"🔑 Contraseña: {pass_instec}"
                ])
            else:
                finishInfo = format_s1_message(finish_title, [
                    f"📄 Archivo: {original_filename}",
                    f"📦 Tamaño total: {sizeof_fmt(file_size)}",
                    f"🔗 Enlaces generados: {len(files)}",
                    f"⏱️ Duración enlaces: 3 días",
                    f"💾 Partes: {total_parts}" if total_parts > 1 else "💾 Archivo único"
                ])
            
            bot.sendMessage(message.chat.id, finishInfo)
            
            # ENVIAR ENLACES CLICKEABLES EN AZUL
            if len(files) > 0:
                # Crear mensaje con enlaces en HTML para que sean clickeables
                links_message = "╭━━━━❰ Enlaces ❱━➣\n"
                
                for i, f in enumerate(files, 1):
                    # Determinar qué nombre mostrar
                    if len(files) > 1:
                        # Si hay múltiples partes: "Nombre (Parte X)"
                        file_display = f"{original_filename} (Parte {i})"
                    else:
                        # Si es un solo archivo: Solo el nombre
                        file_display = f"{original_filename}"
                    
                    # Crear enlace HTML
                    link = f"┣⪼ <a href='{f['directurl']}'>{file_display}</a>\n"
                    links_message += link
                
                links_message += "╰━━━━━━━━━━━━━━━➣"
                
                # Enviar con parse_mode HTML para que los enlaces sean clickeables
                bot.sendMessage(message.chat.id, links_message, parse_mode='HTML')
                
                txtname = base_name + '.txt'
                sendTxt(txtname,files,update,bot)
            else:
                bot.sendMessage(message.chat.id, '<b>⚠️ No se generaron enlaces</b>', parse_mode='HTML')
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
        # SOLO ENLACES EN EL TXT - UNO POR LÍNEA, SEPARADOS CON UNA LÍNEA EN BLANCO
        with open(name, 'w', encoding='utf-8') as txt:
            for i, f in enumerate(files):
                txt.write(f"{f['directurl']}")
                # Solo agregar línea en blanco si no es el último enlace
                if i < len(files) - 1:
                    txt.write("\n\n")
            
        info_msg = f"""<b>📄 Archivo de enlaces generado</b>

📎 <b>Nombre:</b> <code>{name}</code>
🔗 <b>Enlaces incluidos:</b> {len(files)}
⏱️ <b>Duración de enlaces:</b> 8-30 minutos

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
    elif 'moodle.instec.cu' in host:  # NUEVA PLATAFORMA
        return 'INSTEC'
    else:
        return 'Personalizada'

def generate_user_stats(jdb):
    """Genera estadísticas de usuarios"""
    try:
        users = jdb.get_all_users()
        stats = {
            'total_users': 0,
            'active_users': 0,
            'total_uploads': 0,
            'total_size_mb': 0,
            'platform_stats': {},
            'user_details': []
        }
        
        for username, user_data in users.items():
            if username == 'admin':
                continue
                
            stats['total_users'] += 1
            upload_count = user_data.get('upload_count', 0)
            total_mb = user_data.get('total_mb_used', 0)
            
            if upload_count > 0:
                stats['active_users'] += 1
                stats['total_uploads'] += upload_count
                stats['total_size_mb'] += total_mb
                
                platform = get_platform_name(user_data.get('moodle_host', ''))
                last_upload = user_data.get('last_upload', 'Nunca')
                
                stats['user_details'].append({
                    'username': username,
                    'uploads': upload_count,
                    'size_mb': total_mb,
                    'last_upload': last_upload,
                    'platform': platform
                })
        
        # Ordenar por subidas
        stats['user_details'].sort(key=lambda x: x['uploads'], reverse=True)
        return stats
        
    except Exception as e:
        print(f"Error generando stats: {e}")
        return None

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
                    # Usuarios normales no se crean automáticamente, deben ser agregados por admin
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
        
        # COMANDO STAT PARA ESTADÍSTICAS
        if '/stat' in msgText:
            if not isadmin:
                bot.sendMessage(update.message.chat.id,'<b>❌ Comando solo para administradores</b>', parse_mode='HTML')
                return
                
            stats = generate_user_stats(jdb)
            if not stats:
                bot.sendMessage(update.message.chat.id,'<b>❌ Error generando estadísticas</b>', parse_mode='HTML')
                return
            
            report = format_s1_message("📊 ESTADÍSTICAS USUARIOS", [
                f"👥 Usuarios totales: {stats['total_users']}",
                f"🔥 Usuarios activos: {stats['active_users']}",
                f"📤 Total subidas: {stats['total_uploads']}",
                f"💾 Espacio usado: {stats['total_size_mb']:.2f} MB",
                f"📈 Promedio: {stats['total_uploads']/max(stats['active_users'],1):.1f} subidas/usr"
            ])
            
            # Top 5 usuarios
            if stats['user_details']:
                top_users = "\n".join([f"┣⪼ {i+1}. {u['username']}: {u['uploads']} ups, {u['size_mb']:.1f} MB" 
                                      for i, u in enumerate(stats['user_details'][:5])])
                report += f"\n🏆 TOP 5 USUARIOS:\n{top_users}"
            
            bot.sendMessage(update.message.chat.id, report)
            return
        
        # COMANDOS DE CONFIGURACIÓN RÁPIDA PARA ADMIN
        if '/moodle_eva' in msgText and isadmin:
            user_info['moodle_host'] = 'https://eva.uo.edu.cu/'
            user_info['moodle_user'] = 'eric.serrano'
            user_info['moodle_password'] = 'Rulebreaker2316'
            user_info['moodle_repo_id'] = 4
            user_info['uploadtype'] = 'evidence'  # Cambiado a evidence
            user_info['cloudtype'] = 'moodle'
            user_info['zips'] = 99  # 99 MB para EVA
            jdb.save_data_user(username, user_info)
            jdb.save()
            bot.sendMessage(update.message.chat.id, '<b>✅ Configurado para EVA (Evidence)</b>', parse_mode='HTML')
            return

        if '/moodle_cursos' in msgText and isadmin:
            user_info['moodle_host'] = 'https://cursos.uo.edu.cu/'
            user_info['moodle_user'] = 'eric.serrano'
            user_info['moodle_password'] = 'Rulebreaker2316'
            user_info['moodle_repo_id'] = 4
            user_info['uploadtype'] = 'evidence'  # Cambiado a evidence
            user_info['cloudtype'] = 'moodle'
            user_info['zips'] = 99  # 99 MB para CURSOS
            jdb.save_data_user(username, user_info)
            jdb.save()
            bot.sendMessage(update.message.chat.id, '<b>✅ Configurado para CURSOS (Evidence)</b>', parse_mode='HTML')
            return

        if '/moodle_cened' in msgText and isadmin:
            user_info['moodle_host'] = 'https://aulacened.uci.cu/'
            user_info['moodle_user'] = 'eliel21'
            user_info['moodle_password'] = 'ElielThali2115.'
            user_info['moodle_repo_id'] = 5
            user_info['uploadtype'] = 'evidence'  # Cambiado a evidence
            user_info['cloudtype'] = 'moodle'
            user_info['zips'] = 100  # 100 MB para CENED
            jdb.save_data_user(username, user_info)
            jdb.save()
            bot.sendMessage(update.message.chat.id, '<b>✅ Configurado para CENED (Evidence)</b>', parse_mode='HTML')
            return

        # NUEVO COMANDO - CONFIGURACIÓN INSTEC
        if '/moodle_instec' in msgText and isadmin:
            user_info['moodle_host'] = 'https://moodle.instec.cu/'
            user_info['moodle_user'] = 'Kevin.cruz'
            user_info['moodle_password'] = 'Kevin10.'
            user_info['moodle_repo_id'] = 4
            user_info['uploadtype'] = 'evidence'  # Cambiado a evidence
            user_info['cloudtype'] = 'moodle'
            user_info['zips'] = 99  # 99 MB para INSTEC
            jdb.save_data_user(username, user_info)
            jdb.save()
            bot.sendMessage(update.message.chat.id, '<b>✅ Configurado para INSTEC (Evidence)</b>', parse_mode='HTML')
            return
        
        # [El resto del código permanece igual...]
        # COMANDO ADDUSERCONFIG, BANUSER, etc...

        message = bot.sendMessage(update.message.chat.id,'<b>⏳ Procesando...</b>', parse_mode='HTML')

        thread.store('msg',message)

        if '/start' in msgText:
            # Obtener plataforma actual
            platform_name = get_platform_name(user_info.get('moodle_host', ''))
            
            # Mensaje según plataforma para duración de enlaces
            duration_info = ""
            if platform_name == 'CENED':
                duration_info = "┣⪼ ⏱️ Enlaces: 8-30 minutos\n"
            elif platform_name == 'INSTEC':  # NUEVA PLATAFORMA
                duration_info = "┣⪼ ⏱️ Enlaces: Desconocido\n┣⪼ 🔐 Descarga vía cuenta\n"
            else:
                duration_info = "┣⪼ ⏱️ Enlaces: 3 días\n"
            
            if isadmin:
                welcome_text = f"""╭━━━━❰🤖 Bot de Moodle - ADMIN❱━➣
┣⪼ 🚀 Subidas a Moodle/Cloud
┣⪼ 👨‍💻 Desarrollado por: @Eliel_21
┣⪼ 🏫 Plataforma: {platform_name}
{duration_info}┣⪼ 📤 Envía enlaces HTTP/HTTPS

┣⪼ ⚙️ CONFIGURACIÓN RÁPIDA:
┣⪼ /moodle_eva - EVA (Evidence)
┣⪼ /moodle_cursos - CURSOS (Evidence)  
┣⪼ /moodle_cened - CENED (Evidence)
┣⪼ /moodle_instec - INSTEC (Evidence)

┣⪼ 👥 GESTIÓN DE USUARIOS:
┣⪼ /adduserconfig - Agregar y configurar
┣⪼ /banuser - Eliminar usuario(s)
┣⪼ /getdb - Base de datos
┣⪼ /stat - Estadísticas

┣⪼ ⚡ CONFIGURACIÓN AVANZADA:
┣⪼ /myuser - Mi configuración
┣⪼ /zips - Tamaño de partes
┣⪼ /account - Cuenta Moodle
┣⪼ /host - Servidor Moodle
┣⪼ /repoid - ID Repositorio
┣⪼ /uptype - Tipo de subida

┣⪼ 📚 COMANDOS GENERALES:
┣⪼ /tutorial - Guía completa
╰━━━━━━━━━━━━━━━➣"""
            else:
                welcome_text = f"""╭━━━━❰🤖 Bot de Moodle❱━➣
┣⪼ 🚀 Subidas a Moodle/Cloud
┣⪼ 👨‍💻 Desarrollado por: @Eliel_21
┣⪼ 🏫 Plataforma: {platform_name}
{duration_info}┣⪼ 📤 Envía enlaces HTTP/HTTPS

┣⪼ 📝 COMANDOS DISPONIBLES:
┣⪼ /start - Información del bot
┣⪼ /tutorial - Guía completa
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
