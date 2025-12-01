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
import pytz

from pydownloader.downloader import Downloader
from ProxyCloud import ProxyCloud
import ProxyCloud
import socket
import S5Crypto
import threading

# Configurar zona horaria de Cuba
CUBA_TZ = pytz.timezone('America/Havana')

def get_cuba_time_formatted():
    """Obtiene la hora actual de Cuba en formato español"""
    cuba_time = datetime.datetime.now(CUBA_TZ)
    
    # Diccionario de meses en español
    meses = {
        1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril',
        5: 'mayo', 6: 'junio', 7: 'julio', 8: 'agosto',
        9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre'
    }
    
    # Formatear hora en 12 horas con AM/PM
    hora_12 = cuba_time.strftime("%I:%M %p").lstrip('0')  # Quitar cero inicial
    
    # Construir fecha en español
    fecha_espanol = f"{cuba_time.day} de {meses[cuba_time.month]} de {cuba_time.year} {hora_12}"
    
    return fecha_espanol

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

def format_size(size_bytes):
    """Formatea el tamaño en bytes a MB o GB automáticamente"""
    if size_bytes <= 0:
        return "0 MB"
    
    mb_size = size_bytes / (1024 * 1024)
    
    if mb_size >= 1024:  # Si es mayor a 1GB
        gb_size = mb_size / 1024
        return f"{gb_size:.2f} GB"
    else:
        return f"{mb_size:.2f} MB"

def save_upload_stats(jdb, username, file_size, original_filename, file_upload_count):
    """Guarda las estadísticas solo cuando la subida es completamente exitosa"""
    try:
        user_info = jdb.get_user(username)
        if not user_info:
            return False
            
        file_size_mb = file_size / (1024 * 1024)
        
        # ✅ OBTENER HORA DE CUBA EN ESPAÑOL
        current_time = get_cuba_time_formatted()
        
        # DATOS ESTADÍSTICOS
        user_info['total_mb_used'] = user_info.get('total_mb_used', 0) + file_size_mb
        user_info['last_upload'] = current_time
        user_info['upload_count'] = user_info.get('upload_count', 0) + 1
        
        # PRIMERA SUBIDA (solo si es la primera vez)
        if not user_info.get('first_upload'):
            user_info['first_upload'] = current_time
            
        # GUARDAR
        jdb.save_data_user(username, user_info)
        jdb.save()
        
        print(f"✅ Estadísticas guardadas para @{username}: {file_size_mb:.2f} MB - Hora Cuba: {current_time}")
        return True
        
    except Exception as e:
        print(f"❌ Error guardando estadísticas: {e}")
        return False

def get_user_stats(username, user_info):
    """Genera las estadísticas formateadas para un usuario"""
    
    # ✅ USAR .get() CON VALORES POR DEFECTO PARA USUARIOS ANTIGUOS
    total_uploads = user_info.get('upload_count', 0)
    total_mb_used = user_info.get('total_mb_used', 0)
    last_upload = user_info.get('last_upload', 'Nunca')
    first_upload = user_info.get('first_upload', 'Nunca')
    
    # Plataforma actual
    platform = get_platform_name(user_info.get('moodle_host', ''))
    
    # Construir el mensaje con formato S1
    stats_message = format_s1_message(f"📊 Estadísticas de @{username}", [
        f"📁 Total subidas: {total_uploads}",
        f"💾 Espacio usado: {format_size(total_mb_used * 1024 * 1024)}",
        f"📅 Primera subida: {first_upload}",
        f"🕐 Última subida: {last_upload}",
        f"🏫 Plataforma: {platform}"
    ])
    
    return stats_message

def get_all_users_stats(jdb, admin_username):
    """Genera estadísticas de todos los usuarios para el admin"""
    
    users_data = jdb.get_all_users()
    total_users = len(users_data)
    
    # Estadísticas globales
    total_uploads_all = 0
    total_mb_all = 0
    active_users = 0
    users_with_uploads = 0
    
    # Usuarios más activos (top 10)
    active_users_list = []
    
    for username, user_data in users_data.items():
        if username == admin_username:  # Excluir al admin del ranking
            continue
            
        uploads = user_data.get('upload_count', 0)
        mb_used = user_data.get('total_mb_used', 0)
        
        total_uploads_all += uploads
        total_mb_all += mb_used
        
        if uploads > 0:
            users_with_uploads += 1
            active_users_list.append({
                'username': username,
                'uploads': uploads,
                'mb_used': mb_used,
                'last_upload': user_data.get('last_upload', 'Nunca')
            })
            
        # Considerar usuario activo si ha subido algo en los últimos 30 días
        if user_data.get('last_upload'):
            try:
                # Convertir fecha de español a datetime para cálculo
                fecha_str = user_data['last_upload']
                for mes_num, mes_nombre in {
                    1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril',
                    5: 'mayo', 6: 'junio', 7: 'julio', 8: 'agosto',
                    9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre'
                }.items():
                    if mes_nombre in fecha_str:
                        # Extraer día, año y hora
                        partes = fecha_str.split(' de ')
                        dia = int(partes[0])
                        año = int(partes[2].split(' ')[0])
                        hora_str = partes[2].split(' ')[1] + ' ' + partes[2].split(' ')[2]
                        
                        # Convertir hora 12h a 24h
                        from datetime import datetime
                        hora_24 = datetime.strptime(hora_str, '%I:%M %p').strftime('%H:%M')
                        
                        # Crear datetime object
                        fecha_dt = datetime(año, mes_num, dia, 
                                          int(hora_24.split(':')[0]), 
                                          int(hora_24.split(':')[1]))
                        
                        days_since_upload = (datetime.now() - fecha_dt).days
                        if days_since_upload <= 30:
                            active_users += 1
                        break
            except:
                pass
    
    # Ordenar usuarios por actividad
    active_users_list.sort(key=lambda x: x['uploads'], reverse=True)
    top_users = active_users_list[:10]  # Top 10
    
    # Construir mensaje para admin
    stats_message = format_s1_message("📊 Estadísticas Globales - ADMIN", [
        f"👥 Total usuarios: {total_users}",
        f"🚀 Usuarios activos: {active_users}",
        f"📤 Usuarios con subidas: {users_with_uploads}",
        f"📁 Total subidas: {total_uploads_all}",
        f"💾 Espacio total: {format_size(total_mb_all * 1024 * 1024)}",
        f"📊 Promedio por usuario: {format_size((total_mb_all/max(users_with_uploads,1)) * 1024 * 1024) if users_with_uploads > 0 else '0 MB'}"
    ])
    
    # Agregar top usuarios si hay datos
    if top_users:
        stats_message += "\n\n🏆 Top 10 Usuarios Más Activos:\n"
        for i, user in enumerate(top_users, 1):
            stats_message += f"{i}. @{user['username']} - {user['uploads']} subidas ({format_size(user['mb_used'] * 1024 * 1024)})\n"
    
    return stats_message

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
        
        # ✅ SOLUCIÓN IMPLEMENTADA: PRIORIDAD PARA COMANDO /ZIPS
        user_configured_zips = getUser.get('zips')
        
        # Si el usuario configuró manualmente con /zips, usar ese valor
        if user_configured_zips and user_configured_zips > 0:
            max_file_size = 1024 * 1024 * user_configured_zips
        else:
            # Si no, usar los valores fijos por plataforma
            if getUser['moodle_host'] == 'https://eva.uo.edu.cu/':
                max_file_size = 1024 * 1024 * 99  # 99 MB para EVA
            elif getUser['moodle_host'] == 'https://cursos.uo.edu.cu/':
                max_file_size = 1024 * 1024 * 99  # 99 MB para CURSOS
            elif getUser['moodle_host'] == 'https://moodle.instec.cu/':  
                max_file_size = 1024 * 1024 * 100  # ✅ 100 MB para INSTEC
            else:
                max_file_size = 1024 * 1024 * 100  # 100 MB para CENED por defecto
        
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
            # Calcular cantidad de partes
            total_parts = (file_size + max_file_size - 1) // max_file_size
            
            # Mostrar información de compresión (MEJORADA con cantidad de partes)
            platform_name = get_platform_name(getUser['moodle_host'])
            
            compresingInfo = format_s1_message("🗜️ Comprimiendo Archivo", [
                f"📄 Archivo: {original_filename}",
                f"📦 Tamaño original: {sizeof_fmt(file_size)}",
                f"🗂️ Partes: {total_parts}",
                f"🏫 Plataforma: {platform_name}"
            ])
            
            bot.editMessageText(message, compresingInfo)
            
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
            
        # ✅ ELIMINADO: Guardado antiguo de estadísticas aquí
        # Los datos se guardarán SOLO al final exitoso
            
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
            
            # ✅ GUARDAR ESTADÍSTICAS SOLO AQUÍ - CUANDO TODO ESTÉ COMPLETAMENTE TERMINADO
            if not thread or not thread.getStore('stop'):
                save_upload_stats(jdb, username, file_size, original_filename, file_upload_count)

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

def test_moodle_connection(user_info):
    """Testea la conexión REAL a la Moodle configurada actualmente"""
    try:
        proxy = ProxyCloud.parse(user_info['proxy'])
        client = MoodleClient(
            user_info['moodle_user'],
            user_info['moodle_password'], 
            user_info['moodle_host'],  # ✅ Usa la Moodle actual del usuario
            user_info['moodle_repo_id'],  # ✅ Usa el repo_id actual
            proxy=proxy
        )
        
        # Intentar login REAL en la Moodle configurada
        login_success = client.login()
        
        if login_success:
            # Obtener información de la plataforma ACTUAL
            platform_name = get_platform_name(user_info['moodle_host'])
            return {
                'status': 'success',
                'message': f'✅ Conexión exitosa a {platform_name}',
                'platform': platform_name,
                'proxy_used': bool(user_info.get('proxy', '')),
                'details': 'Login y autenticación correctos',
                'moodle_host': user_info['moodle_host']  # ✅ Incluir host actual
            }
        else:
            return {
                'status': 'auth_error',
                'message': '❌ Error de autenticación en Moodle',
                'platform': get_platform_name(user_info['moodle_host']),
                'proxy_used': bool(user_info.get('proxy', '')),
                'details': 'Credenciales incorrectas o servidor no disponible',
                'moodle_host': user_info['moodle_host']  # ✅ Incluir host actual
            }
            
    except Exception as e:
        error_msg = str(e).lower()
        if 'proxy' in error_msg or 'connect' in error_msg or 'timeout' in error_msg:
            return {
                'status': 'proxy_error',
                'message': '❌ Error de conexión del proxy',
                'platform': get_platform_name(user_info['moodle_host']),
                'proxy_used': bool(user_info.get('proxy', '')),
                'details': f'No se pudo conectar a través del proxy: {str(e)}',
                'moodle_host': user_info['moodle_host']  # ✅ Incluir host actual
            }
        else:
            return {
                'status': 'unknown_error', 
                'message': '❌ Error desconocido',
                'platform': get_platform_name(user_info['moodle_host']),
                'proxy_used': bool(user_info.get('proxy', '')),
                'details': str(e),
                'moodle_host': user_info['moodle_host']  # ✅ Incluir host actual
            }

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
        
        # COMANDOS NUEVOS: ESTADÍSTICAS
        if '/mystats' in msgText:
            try:
                # Usuarios normales solo pueden ver sus stats, admin puede ver cualquier usuario
                parts = msgText.split(' ')
                target_user = username  # Por defecto el usuario actual
                
                # Si es admin y especificó un usuario, usar ese
                if isadmin and len(parts) > 1:
                    target_user = parts[1].replace('@', '')  # Quitar @ si existe
                
                user_data = jdb.get_user(target_user)
                if user_data:
                    stats_message = get_user_stats(target_user, user_data)
                    bot.sendMessage(update.message.chat.id, stats_message, parse_mode='HTML')
                else:
                    bot.sendMessage(update.message.chat.id, 
                                  f'<b>❌ Usuario @{target_user} no encontrado</b>', 
                                  parse_mode='HTML')
                    
            except Exception as e:
                print(f"Error en mystats: {e}")
                bot.sendMessage(update.message.chat.id, 
                              '<b>❌ Error obteniendo estadísticas</b>', 
                              parse_mode='HTML')
            return

        if '/stats_user' in msgText:
            if not isadmin:
                bot.sendMessage(update.message.chat.id, 
                              '<b>❌ Comando restringido a administradores</b>', 
                              parse_mode='HTML')
                return
            
            try:
                parts = msgText.split(' ')
                if len(parts) < 2:
                    bot.sendMessage(update.message.chat.id,
                                  '<b>❌ Formato incorrecto</b>\n'
                                  '<code>/stats_user @usuario</code>',
                                  parse_mode='HTML')
                    return
                
                target_user = parts[1].replace('@', '')
                user_data = jdb.get_user(target_user)
                if user_data:
                    stats_message = get_user_stats(target_user, user_data)
                    bot.sendMessage(update.message.chat.id, stats_message, parse_mode='HTML')
                else:
                    bot.sendMessage(update.message.chat.id, 
                                  f'<b>❌ Usuario @{target_user} no encontrado</b>', 
                                  parse_mode='HTML')
                    
            except Exception as e:
                print(f"Error en stats_user: {e}")
                bot.sendMessage(update.message.chat.id, 
                              '<b>❌ Error obteniendo estadísticas del usuario</b>', 
                              parse_mode='HTML')
            return

        if '/stats' in msgText:
            if not isadmin:
                bot.sendMessage(update.message.chat.id, 
                              '<b>❌ Comando restringido a administradores</b>', 
                              parse_mode='HTML')
                return
            
            try:
                stats_message = get_all_users_stats(jdb, username)
                bot.sendMessage(update.message.chat.id, stats_message, parse_mode='HTML')
            except Exception as e:
                print(f"Error en stats: {e}")
                bot.sendMessage(update.message.chat.id, 
                              '<b>❌ Error obteniendo estadísticas globales</b>', 
                              parse_mode='HTML')
            return
        
        # COMANDOS DE PROXY MEJORADOS (SOLO SOCKS)
        if '/proxy_test' in msgText:
            try:
                current_proxy = user_info.get('proxy', '')
                current_platform = get_platform_name(user_info.get('moodle_host', ''))
                
                # Mostrar información inicial del test CON PLATAFORMA ACTUAL
                if not current_proxy:
                    initial_msg = f'<b>🧪 Probando conexión directa a {current_platform}...</b>\n\n'
                else:
                    initial_msg = f'<b>🧪 Probando proxy SOCKS en {current_platform}...</b>\n<code>{current_proxy}</code>\n\n'
                
                initial_msg += '<b>🔍 Verificando:</b>\n• Conexión al servidor Moodle\n• Autenticación\n• Estado del proxy SOCKS'
                
                message = bot.sendMessage(update.message.chat.id, initial_msg, parse_mode='HTML')
                
                # Realizar test COMPLETO a la Moodle ACTUAL
                test_result = test_moodle_connection(user_info)
                
                # Construir mensaje de resultados detallado
                if test_result['status'] == 'success':
                    result_message = format_s1_message("✅ Test Completado", [
                        f"🏫 Plataforma: {test_result['platform']}",
                        f"🔌 Proxy: {'SOCKS' if test_result['proxy_used'] else 'Conexión directa'}",
                        f"📡 Estado: Conexión exitosa",
                        f"🔐 Autenticación: Correcta", 
                        f"🌐 Servidor: {test_result.get('moodle_host', 'N/A')}",
                        f"💡 Detalles: {test_result['details']}"
                    ])
                    
                elif test_result['status'] == 'auth_error':
                    result_message = format_s1_message("❌ Error de Autenticación", [
                        f"🏫 Plataforma: {test_result['platform']}",
                        f"🔌 Proxy: {'SOCKS' if test_result['proxy_used'] else 'Conexión directa'}", 
                        f"📡 Estado: Servidor accesible",
                        f"🔐 Autenticación: Falló",
                        f"🌐 Servidor: {test_result.get('moodle_host', 'N/A')}",
                        f"⚠️ Problema: {test_result['details']}",
                        f"💡 Solución: Verifica usuario/contraseña"
                    ])
                    
                elif test_result['status'] == 'proxy_error':
                    result_message = format_s1_message("❌ Error de Conexión SOCKS", [
                        f"🏫 Plataforma: {test_result['platform']}",
                        f"🔌 Proxy: {'SOCKS CONFIGURADO' if test_result['proxy_used'] else 'Conexión directa'}",
                        f"📡 Estado: Sin conexión",
                        f"🔐 Autenticación: No probada", 
                        f"🌐 Servidor: {test_result.get('moodle_host', 'N/A')}",
                        f"⚠️ Problema: {test_result['details']}",
                        f"💡 Solución: Cambia proxy SOCKS o usa /delproxy"
                    ])
                    
                else:
                    result_message = format_s1_message("❌ Error Desconocido", [
                        f"🏫 Plataforma: {test_result['platform']}",
                        f"🔌 Proxy: {'SOCKS' if test_result['proxy_used'] else 'Conexión directa'}",
                        f"📡 Estado: Error inesperado",
                        f"🔐 Autenticación: No probada",
                        f"🌐 Servidor: {test_result.get('moodle_host', 'N/A')}",
                        f"⚠️ Problema: {test_result['details']}",
                        f"💡 Solución: Contacta al administrador"
                    ])
                
                bot.editMessageText(message, result_message)
                
            except Exception as e:
                bot.sendMessage(update.message.chat.id, 
                               f'<b>❌ Error en el test:</b>\n<code>{str(e)}</code>', 
                               parse_mode='HTML')
            return

        if '/delproxy' in msgText:
            try:
                old_proxy = user_info.get('proxy', '')
                user_info['proxy'] = ''
                jdb.save_data_user(username, user_info)
                jdb.save()
                
                bot.sendMessage(update.message.chat.id,
                    '<b>✅ Proxy eliminado</b>\n\n'
                    f'<b>Proxy anterior:</b> <code>{old_proxy if old_proxy else "Ninguno"}</code>\n'
                    f'<b>Estado actual:</b> Conexión directa\n\n'
                    f'<b>Ahora se usará conexión directa al servidor</b>',
                    parse_mode='HTML'
                )
            except Exception as e:
                bot.sendMessage(update.message.chat.id, f'<b>❌ Error:</b> {str(e)}', parse_mode='HTML')
            return

        # COMANDO PROXY MEJORADO (SOLO SOCKS)
        if '/proxy' in msgText:
            try:
                parts = msgText.split(' ', 1)
                if len(parts) < 2:
                    # Mostrar ayuda ACTUALIZADA solo para SOCKS
                    current_proxy = user_info.get('proxy', '')
                    proxy_status = "✅ Configurado" if current_proxy else "❌ No configurado"
                    
                    # Obtener plataforma actual para el mensaje
                    current_platform = get_platform_name(user_info.get('moodle_host', ''))
                    
                    bot.sendMessage(update.message.chat.id,
                        '<b>🔧 Configuración de Proxy SOCKS</b>\n\n'
                        f'<b>🏫 Plataforma actual:</b> {current_platform}\n'
                        f'<b>🔌 Proxy actual:</b> <code>{current_proxy if current_proxy else "Conexión directa"}</code>\n'
                        f'<b>Estado:</b> {proxy_status}\n\n'
                        '<b>🚫 Solo se aceptan proxies SOCKS:</b>\n'
                        '<code>/proxy socks4://ip:puerto</code>\n'
                        '<code>/proxy socks5://ip:puerto</code>\n\n'
                        '<b>📋 Ejemplos SOCKS:</b>\n'
                        '<code>/proxy socks4://190.6.65.2:1080</code>\n'
                        '<code>/proxy socks5://201.234.122.100:1080</code>\n\n'
                        '<b>🔍 Otros comandos:</b>\n'
                        '<code>/proxy_test</code> - Probar proxy actual\n'
                        '<code>/delproxy</code> - Usar conexión directa',
                        parse_mode='HTML'
                    )
                    return
                
                proxy_url = parts[1].strip()
                old_proxy = user_info.get('proxy', '')
                
                # ✅ VALIDACIÓN: Solo permitir SOCKS4 y SOCKS5
                if proxy_url and not any(proto in proxy_url for proto in ['socks4://', 'socks5://']):
                    bot.sendMessage(update.message.chat.id,
                        '<b>❌ Formato de proxy NO permitido</b>\n\n'
                        '<b>🚫 Solo se aceptan proxies SOCKS:</b>\n'
                        '<code>socks4://ip:puerto</code>\n'
                        '<code>socks5://ip:puerto</code>\n\n'
                        '<b>📋 Ejemplos válidos:</b>\n'
                        '<code>socks4://190.6.65.2:1080</code>\n'
                        '<code>socks5://201.234.122.100:1080</code>\n\n'
                        '<b>❌ NO se permiten:</b>\n'
                        '<code>http://...</code>\n'
                        '<code>https://...</code>',
                        parse_mode='HTML'
                    )
                    return
                
                message = bot.sendMessage(update.message.chat.id, 
                    f'<b>🔧 Configurando proxy SOCKS...</b>\n<code>{proxy_url}</code>\n\n'
                    f'<b>🧪 Probando conexión a Moodle...</b>', 
                    parse_mode='HTML'
                )
                
                # Configurar proxy temporalmente para el test
                test_user_info = user_info.copy()
                test_user_info['proxy'] = proxy_url
                
                # Hacer test COMPLETO con el nuevo proxy SOCKS
                test_result = test_moodle_connection(test_user_info)
                
                if test_result['status'] != 'success':
                    # Si el test falla, ofrecer opciones
                    bot.editMessageText(message,
                        f'<b>❌ Proxy SOCKS no funciona</b>\n\n'
                        f'<b>🏫 Plataforma:</b> {test_result["platform"]}\n'
                        f'<b>🔌 Proxy:</b> <code>{proxy_url}</code>\n'
                        f'<b>Estado:</b> {test_result["message"]}\n'
                        f'<b>Detalles:</b> {test_result["details"]}\n\n'
                        f'<b>¿Quieres guardarlo de todas formas?</b>\n'
                        f'Responde <code>/confirm_proxy</code> para guardar\n'
                        f'o configura otro proxy SOCKS',
                        parse_mode='HTML'
                    )
                    user_info['temp_proxy'] = proxy_url
                    jdb.save_data_user(username, user_info)
                    jdb.save()
                    return
                
                # Si el test es exitoso, guardar directamente
                user_info['proxy'] = proxy_url
                if 'temp_proxy' in user_info:
                    del user_info['temp_proxy']
                jdb.save_data_user(username, user_info)
                jdb.save()
                
                bot.editMessageText(message,
                    f'<b>✅ Proxy SOCKS configurado y verificado</b>\n\n'
                    f'<b>🏫 Plataforma:</b> {test_result["platform"]}\n'
                    f'<b>🔌 Proxy anterior:</b> <code>{old_proxy if old_proxy else "Ninguno"}</code>\n'
                    f'<b>🔌 Proxy nuevo:</b> <code>{proxy_url}</code>\n'
                    f'<b>📡 Estado:</b> ✅ Funcionando correctamente\n\n'
                    f'<b>¡Proxy SOCKS listo para usar!</b>',
                    parse_mode='HTML'
                )
                
            except Exception as e:
                bot.sendMessage(update.message.chat.id, 
                               f'<b>❌ Error configurando proxy SOCKS:</b>\n<code>{str(e)}</code>', 
                               parse_mode='HTML')
            return

        # CONFIRMACIÓN DE PROXY (cuando no funciona pero se quiere guardar)
        if '/confirm_proxy' in msgText:
            try:
                temp_proxy = user_info.get('temp_proxy', '')
                if not temp_proxy:
                    bot.sendMessage(update.message.chat.id, '<b>❌ No hay proxy temporal para confirmar</b>', parse_mode='HTML')
                    return
                
                old_proxy = user_info.get('proxy', '')
                user_info['proxy'] = temp_proxy
                del user_info['temp_proxy']
                jdb.save_data_user(username, user_info)
                jdb.save()
                
                bot.sendMessage(update.message.chat.id,
                    f'<b>⚠️ Proxy SOCKS guardado (sin verificación)</b>\n\n'
                    f'<b>Proxy anterior:</b> <code>{old_proxy if old_proxy else "Ninguno"}</code>\n'
                    f'<b>Proxy nuevo:</b> <code>{temp_proxy}</code>\n'
                    f'<b>Estado:</b> ⚠️ Guardado sin verificación\n\n'
                    f'<b>Puede que no funcione. Usa /proxy_test para verificar.</b>',
                    parse_mode='HTML'
                )
            except Exception as e:
                bot.sendMessage(update.message.chat.id, f'<b>❌ Error:</b> {str(e)}', parse_mode='HTML')
            return

        # ... (el resto de tu código existente se mantiene igual)
        # COMANDOS DE CONFIGURACIÓN RÁPIDA PARA ADMIN
        if '/moodle_eva' in msgText and isadmin:
            user_info['moodle_host'] = 'https://eva.uo.edu.cu/'
            user_info['moodle_user'] = 'eric.serrano'
            user_info['moodle_password'] = 'Rulebreaker2316'
            user_info['moodle_repo_id'] = 4
            user_info['uploadtype'] = 'draft'
            user_info['cloudtype'] = 'moodle'
            user_info['zips'] = 99  # 99 MB para EVA
            jdb.save_data_user(username, user_info)
            jdb.save()
            bot.sendMessage(update.message.chat.id, '<b>✅ Configurado para EVA</b>', parse_mode='HTML')
            return

        if '/moodle_cursos' in msgText and isadmin:
            user_info['moodle_host'] = 'https://cursos.uo.edu.cu/'
            user_info['moodle_user'] = 'eric.serrano'
            user_info['moodle_password'] = 'Rulebreaker2316'
            user_info['moodle_repo_id'] = 4
            user_info['uploadtype'] = 'draft'
            user_info['cloudtype'] = 'moodle'
            user_info['zips'] = 99  # 99 MB para CURSOS
            jdb.save_data_user(username, user_info)
            jdb.save()
            bot.sendMessage(update.message.chat.id, '<b>✅ Configurado para CURSOS</b>', parse_mode='HTML')
            return

        if '/moodle_cened' in msgText and isadmin:
            user_info['moodle_host'] = 'https://aulacened.uci.cu/'
            user_info['moodle_user'] = 'eliel21'
            user_info['moodle_password'] = 'ElielThali2115.'
            user_info['moodle_repo_id'] = 5
            user_info['uploadtype'] = 'draft'
            user_info['cloudtype'] = 'moodle'
            user_info['zips'] = 100  # 100 MB para CENED
            jdb.save_data_user(username, user_info)
            jdb.save()
            bot.sendMessage(update.message.chat.id, '<b>✅ Configurado para CENED</b>', parse_mode='HTML')
            return

        # NUEVO COMANDO - CONFIGURACIÓN INSTEC
        if '/moodle_instec' in msgText and isadmin:
            user_info['moodle_host'] = 'https://moodle.instec.cu/'
            user_info['moodle_user'] = 'Kevin.cruz'
            user_info['moodle_password'] = 'Kevin10.'
            user_info['moodle_repo_id'] = 3
            user_info['uploadtype'] = 'draft'
            user_info['cloudtype'] = 'moodle'
            user_info['zips'] = 100  # ✅ 100 MB para INSTEC
            jdb.save_data_user(username, user_info)
            jdb.save()
            bot.sendMessage(update.message.chat.id, '<b>✅ Configurado para INSTEC</b>', parse_mode='HTML')
            return
        
        # COMANDO ADDUSERCONFIG MEJORADO - Agrega y configura usuarios
        if '/adduserconfig' in msgText:
            isadmin = jdb.is_admin(username)
            if isadmin:
                try:
                    # Formato: /adduserconfig usuario1,usuario2 [eva|cursos|cened|instec]
                    parts = str(msgText).split(' ', 2)
                    if len(parts) < 3:
                        bot.sendMessage(update.message.chat.id,
                                       '<b>❌ Formato incorrecto</b>\n\n'
                                       '<b>Formatos válidos:</b>\n'
                                       '<code>/adduserconfig usuario eva</code>\n'
                                       '<code>/adduserconfig usuario1,usuario2 cursos</code>\n'
                                       '<code>/adduserconfig usuario cened</code>\n'
                                       '<code>/adduserconfig usuario instec</code>',
                                       parse_mode='HTML')
                        return
                    
                    target_users_text = parts[1]
                    platform = parts[2].strip().lower()
                    
                    # CONFIGURACIONES PREDEFINIDAS
                    configs = {
                        'eva': {
                            'host': 'https://eva.uo.edu.cu/',
                            'user': 'eric.serrano',
                            'password': 'Rulebreaker2316',
                            'repo_id': 4,
                            'uptype': 'draft',
                            'name': 'EVA UO',
                            'zips': 99  # 99 MB para EVA
                        },
                        'cursos': {
                            'host': 'https://cursos.uo.edu.cu/',
                            'user': 'eric.serrano', 
                            'password': 'Rulebreaker2316',
                            'repo_id': 4,
                            'uptype': 'draft',
                            'name': 'CURSOS UO',
                            'zips': 99  # 99 MB para CURSOS
                        },
                        'cened': {
                            'host': 'https://aulacened.uci.cu/',
                            'user': 'eliel21',
                            'password': 'ElielThali2115.',
                            'repo_id': 5,
                            'uptype': 'draft',
                            'name': 'CENED',
                            'zips': 100  # 100 MB para CENED
                        },
                        'instec': {  # NUEVA CONFIGURACIÓN
                            'host': 'https://moodle.instec.cu/',
                            'user': 'Kevin.cruz',
                            'password': 'Kevin10.',
                            'repo_id': 3,
                            'uptype': 'draft',
                            'name': 'INSTEC',
                            'zips': 100  # ✅ 100 MB para INSTEC
                        }
                    }
                    
                    # Validar plataforma
                    if platform not in configs:
                        bot.sendMessage(update.message.chat.id,
                                       '<b>❌ Plataforma no válida</b>\n'
                                       '<b>Opciones:</b> eva, cursos, cened, instec',
                                       parse_mode='HTML')
                        return
                    
                    # Procesar múltiples usuarios (con @ o sin @)
                    raw_users = [user.strip() for user in target_users_text.split(',')]
                    target_users = []
                    for user in raw_users:
                        if user:
                            # Agregar @ si no lo tiene
                            if not user.startswith('@'):
                                user = '@' + user
                            target_users.append(user)
                    
                    config = configs[platform]
                    
                    configured_users = []
                    existing_users = []
                    
                    for target_user in target_users:
                        if not target_user:
                            continue
                            
                        # Prevenir auto-configuración del admin
                        if target_user == f'@{username}':
                            continue
                        
                        username_clean = target_user.replace('@', '')
                        
                        # Verificar si el usuario ya existe
                        if jdb.get_user(username_clean):
                            existing_users.append(target_user)
                            continue
                        
                        # Crear usuario nuevo
                        jdb.create_user(username_clean)
                        
                        # Obtener y configurar usuario
                        new_user_info = jdb.get_user(username_clean)
                        new_user_info['moodle_host'] = config['host']
                        new_user_info['moodle_user'] = config['user']
                        new_user_info['moodle_password'] = config['password']
                        new_user_info['moodle_repo_id'] = config['repo_id']
                        new_user_info['uploadtype'] = config['uptype']
                        new_user_info['cloudtype'] = 'moodle'
                        new_user_info['zips'] = config['zips']
                        new_user_info['tokenize'] = 0
                        new_user_info['proxy'] = ''
                        new_user_info['dir'] = '/'
                        
                        jdb.save_data_user(username_clean, new_user_info)
                        configured_users.append(target_user)
                    
                    jdb.save()
                    
                    # Construir mensaje de resultado
                    message_parts = []
                    
                    if configured_users:
                        if len(configured_users) == 1:
                            user_msg = format_s1_message("✅ Usuario Agregado y Configurado", [
                                f"👤 Usuario: {configured_users[0]}",
                                f"🏫 Plataforma: {config['name']}"
                            ])
                            message_parts.append(user_msg)
                        else:
                            users_list = ', '.join(configured_users)
                            message_parts.append(f'<b>✅ Usuarios agregados y configurados:</b> {users_list}\n<b>Plataforma:</b> {config["name"]}')
                    
                    if existing_users:
                        if len(existing_users) == 1:
                            message_parts.append(f'<b>⚠️ Usuario ya existente:</b> {existing_users[0]}')
                        else:
                            users_list = ', '.join(existing_users)
                            message_parts.append(f'<b>⚠️ Usuarios ya existentes:</b> {users_list}')
                    
                    if message_parts:
                        final_message = '\n\n'.join(message_parts)
                    else:
                        final_message = '<b>❌ No se agregaron usuarios</b>'
                        
                    bot.sendMessage(update.message.chat.id, final_message, parse_mode='HTML')
                    
                except Exception as e:
                    print(f"Error en adduserconfig: {e}")
                    bot.sendMessage(update.message.chat.id,
                                   '<b>❌ Error en el comando</b>\n'
                                   '<code>/adduserconfig usuario plataforma</code>',
                                   parse_mode='HTML')
            else:
                bot.sendMessage(update.message.chat.id,'<b>❌ No tiene permisos de administrador</b>', parse_mode='HTML')
            return

        # BLOQUEAR COMANDOS DE ADMIN PARA USUARIOS NORMALES
        if not isadmin and is_text and any(cmd in msgText for cmd in [
            '/zips', '/account', '/host', '/repoid', '/tokenize', 
            '/cloud', '/uptype', '/dir', '/myuser', 
            '/files', '/txt_', '/del_', '/delall', '/adduserconfig', 
            '/banuser', '/getdb', '/moodle_eva', '/moodle_cursos', '/moodle_cened', '/moodle_instec',
            '/stats_user', '/stats'  # ✅ NUEVOS COMANDOS BLOQUEADOS
        ]):
            bot.sendMessage(update.message.chat.id,
                           "<b>🚫 Acceso Restringido</b>\n\n"
                           "Los comandos de configuración están disponibles solo para administradores.\n\n"
                           "<b>✅ Comandos disponibles para ti:</b>\n"
                           "• /start - Información del bot\n"
                           "• /tutorial - Guía de uso completo\n"
                           "• /mystats - Tus estadísticas\n"
                           "• /proxy - Configurar proxy SOCKS\n"
                           "• /proxy_test - Probar proxy actual\n"
                           "• /delproxy - Usar conexión directa\n"
                           "• Enlaces HTTP/HTTPS para subir archivos",
                           parse_mode='HTML')
            return

        # MENSAJE PARA TEXTO SIN COMANDOS NI URLS
        if is_text and not msgText.startswith('/') and not 'http' in msgText:
            bot.sendMessage(update.message.chat.id,
                           "<b>🤖 Bot de Subida de Archivos</b>\n\n"
                           "📤 <b>Para subir archivos:</b> Envía un enlace HTTP/HTTPS\n\n"
                           "🔧 <b>Comandos de Proxy:</b>\n"
                           "• /proxy - Configurar proxy SOCKS\n"
                           "• /proxy_test - Probar conexión\n"
                           "• /delproxy - Conexión directa\n\n"
                           "📊 <b>Comandos de Estadísticas:</b>\n"
                           "• /mystats - Ver tus estadísticas\n\n"
                           "📝 <b>Para ver comandos disponibles:</b> Usa /start",
                           parse_mode='HTML')
            return

        # COMANDO BANUSER
        if '/banuser' in msgText:
            isadmin = jdb.is_admin(username)
            if isadmin:
                try:
                    users_text = str(msgText).split(' ', 1)[1]
                    
                    # Procesar múltiples usuarios (con @ o sin @)
                    raw_users = [user.strip() for user in users_text.split(',')]
                    target_users = []
                    for user in raw_users:
                        if user:
                            # Agregar @ si no lo tiene
                            if not user.startswith('@'):
                                user = '@' + user
                            target_users.append(user)
                    
                    banned_users = []
                    not_found_users = []
                    self_ban_attempt = False
                    
                    for target_user in target_users:
                        if target_user:
                            if target_user == f'@{username}':
                                self_ban_attempt = True
                                continue
                            username_clean = target_user.replace('@', '')
                            if jdb.get_user(username_clean):
                                jdb.remove(username_clean)
                                banned_users.append(target_user)
                            else:
                                not_found_users.append(target_user)
                    
                    jdb.save()
                    
                    message_parts = []
                    
                    if banned_users:
                        if len(banned_users) == 1:
                            message_parts.append(f'<b>🚫 Usuario baneado:</b> {banned_users[0]}')
                        else:
                            users_list = ', '.join(banned_users)
                            message_parts.append(f'<b>🚫 Usuarios baneados:</b> {users_list}')
                    
                    if not_found_users:
                        if len(not_found_users) == 1:
                            message_parts.append(f'<b>❌ Usuario no encontrado:</b> {not_found_users[0]}')
                        else:
                            users_list = ', '.join(not_found_users)
                            message_parts.append(f'<b>❌ Usuarios no encontrados:</b> {users_list}')
                    
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

        # COMANDO TUTORIAL (LEE DESDE ARCHIVO)
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

        # COMANDOS DE USUARIO (SOLO PARA ADMINISTRADOR)
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
            # Obtener plataforma actual
            platform_name = get_platform_name(user_info.get('moodle_host', ''))
            
            # Obtener estado del proxy
            current_proxy = user_info.get('proxy', '')
            proxy_status = f"┣⪼ 🔌 Proxy: <code>{current_proxy if current_proxy else 'Conexión directa'}</code>\n"
            
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
{proxy_status}{duration_info}┣⪼ 📤 Envía enlaces HTTP/HTTPS

┣⪼ ⚙️ CONFIGURACIÓN RÁPIDA:
┣⪼ /moodle_eva - EVA
┣⪼ /moodle_cursos - CURSOS  
┣⪼ /moodle_cened - CENED
┣⪼ /moodle_instec - INSTEC

┣⪼ 🔧 COMANDOS PROXY:
┣⪼ /proxy - Configurar proxy SOCKS
┣⪼ /proxy_test - Probar proxy
┣⪼ /delproxy - Conexión directa

┣⪼ 📊 COMANDOS ESTADÍSTICAS:
┣⪼ /mystats - Mis estadísticas
┣⪼ /stats_user @user - Stats de usuario
┣⪼ /stats - Stats globales

┣⪼ 👥 GESTIÓN DE USUARIOS:
┣⪼ /adduserconfig - Agregar y configurar
┣⪼ /banuser - Eliminar usuario(s)
┣⪼ /getdb - Base de datos

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
{proxy_status}{duration_info}┣⪼ 📤 Envía enlaces HTTP/HTTPS

┣⪼ 🔧 COMANDOS PROXY:
┣⪼ /proxy - Configurar proxy SOCKS
┣⪼ /proxy_test - Probar proxy
┣⪼ /delproxy - Conexión directa

┣⪼ 📊 COMANDOS ESTADÍSTICAS:
┣⪼ /mystats - Mis estadísticas

┣⪼ 📝 COMANDOS GENERALES:
┣⪼ /start - Información del bot
┣⪼ /tutorial - Guía completa
╰━━━━━━━━━━━━━━━➣"""
            
            bot.deleteMessage(message.chat.id, message.message_id)
            bot.sendMessage(update.message.chat.id, welcome_text, parse_mode='HTML')
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
