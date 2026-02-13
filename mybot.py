import telebot
from telebot import types
import os
import sqlite3
import yt_dlp

# --- الإعدادات ---
API_TOKEN = '8282104889:AAEOS0BOW7nvEZuHZ4Us5W_cJdE50gDT87s'
# ✅ تم وضع الآي دي الخاص بك هنا بنجاح
ADMIN_ID = 5029027564 

bot = telebot.TeleBot(API_TOKEN)
DOCS_PATH = os.path.join(os.path.expanduser("~"), "Documents")

# --- قاعدة البيانات (حفظ المستخدمين) ---
def init_db():
    conn = sqlite3.connect(os.path.join(DOCS_PATH, 'users.db'))
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)''')
    conn.commit()
    conn.close()

def add_user(user_id):
    try:
        conn = sqlite3.connect(os.path.join(DOCS_PATH, 'users.db'))
        c = conn.cursor()
        c.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (user_id,))
        conn.commit()
        conn.close()
    except: pass

init_db()

# --- ميزة الإذاعة (أنت المطور الوحيد) ---
@bot.message_handler(commands=['broadcast'])
def broadcast_handler(message):
    if message.from_user.id == ADMIN_ID:
        msg = bot.reply_to(message, "📢 **أرسل نص الإذاعة الآن:**", parse_mode='Markdown')
        bot.register_next_step_handler(msg, send_broadcast)
    else:
        bot.reply_to(message, "⚠️ هذا الأمر مخصص للمطور فقط.")

def send_broadcast(message):
    conn = sqlite3.connect(os.path.join(DOCS_PATH, 'users.db'))
    c = conn.cursor()
    c.execute('SELECT user_id FROM users')
    users = c.fetchall()
    conn.close()
    
    count = 0
    for user in users:
        try:
            bot.send_message(user[0], message.text)
            count += 1
        except: continue
    bot.send_message(ADMIN_ID, f"✅ تم إرسال الإذاعة بنجاح إلى {count} مستخدم.")

# --- رسالة البداية ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    add_user(message.from_user.id)
    welcome = (
        "🚀 **أهلاً بك في بوت التحميل السريع!**\n\n"
        "🎬 تحميل فيديوهات تيك توك (بدون علامة مائية)\n"
        "🎵 استخراج الصوت بجودة عالية\n\n"
        "📥 **أرسل الرابط الآن للبدء..**"
    )
    bot.reply_to(message, welcome, parse_mode='Markdown')

# --- معالج التحميل (فيديو) ---
@bot.message_handler(func=lambda message: True)
def handle_tiktok(message):
    url = message.text
    if "tiktok.com" in url:
        add_user(message.from_user.id)
        msg = bot.reply_to(message, "⏳ **جاري التحميل...**", parse_mode='Markdown')
        try:
            video_file = os.path.join(DOCS_PATH, "video.mp4")
            ydl_opts = {
                'outtmpl': video_file,
                'format': 'bestvideo+bestaudio/best',
                'quiet': True,
                'no_warnings': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            if os.path.exists(video_file):
                markup = types.InlineKeyboardMarkup(row_width=2)
                btn_audio = types.InlineKeyboardButton("تحويل لصوت 🎵", callback_data=f"aud_{url}")
                btn_del = types.InlineKeyboardButton("حذف الرسالة 🗑️", callback_data="delete_msg")
                markup.add(btn_audio, btn_del)

                with open(video_file, 'rb') as video:
                    bot.send_video(message.chat.id, video, caption="✨ تم التحميل بنجاح", reply_markup=markup)
                
                os.remove(video_file)
                bot.delete_message(message.chat.id, msg.message_id)
        except Exception as e:
            bot.edit_message_text(f"❌ عذراً، لم أستطع تحميل هذا الفيديو.", message.chat.id, msg.message_id)
    else:
        bot.reply_to(message, "⚠️ يرجى إرسال رابط تيك توك صحيح.")

# --- معالجة الأزرار ---
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "delete_msg":
        bot.delete_message(call.message.chat.id, call.message.message_id)
    elif call.data.startswith("aud_"):
        url = call.data.replace("aud_", "")
        bot.answer_callback_query(call.id, "🎧 جاري استخراج الصوت...")
        try:
            audio_path = os.path.join(DOCS_PATH, "audio.m4a")
            ydl_opts_audio = {'outtmpl': audio_path, 'format': 'bestaudio/best', 'quiet': True}
            with yt_dlp.YoutubeDL(ydl_opts_audio) as ydl:
                ydl.download([url])
            if os.path.exists(audio_path):
                with open(audio_path, 'rb') as audio:
                    bot.send_audio(call.message.chat.id, audio, caption="🎵 الصوت المستخرج")
                os.remove(audio_path)
        except:
            bot.send_message(call.message.chat.id, "❌ فشل استخراج الصوت.")

print("🚀 البوت يعمل الآن تحت إدارتك!")
bot.polling(none_stop=True)
