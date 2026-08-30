import sqlite3
import datetime
import time
import threading
from telebot import TeleBot, types

ADMIN_ID = 1472412382
BOT_TOKEN = "8758745776:AAG5VVacBnPaq69gVOoJRGdTNTIPY_AVz00"

bot = TeleBot(BOT_TOKEN, parse_mode=None)

def keep_alive():
    while True:
        time.sleep(60)

threading.Thread(target=keep_alive, daemon=True).start()

def init_db():
    try:
        conn = sqlite3.connect('bot_data.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            role TEXT DEFAULT 'KULLANICI',
            balance INTEGER DEFAULT 0,
            reg_date TEXT
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS keys (
            key TEXT PRIMARY KEY,
            duration TEXT,
            used_by INTEGER DEFAULT NULL,
            hwid TEXT DEFAULT NULL,
            used_date TEXT DEFAULT NULL,
            expire_date TEXT DEFAULT NULL,
            status TEXT DEFAULT 'available'
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT,
            detail TEXT,
            amount INTEGER DEFAULT 0,
            date TEXT
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS favorites (
            user_id INTEGER,
            key TEXT,
            added_date TEXT,
            PRIMARY KEY (user_id, key)
        )''')
        c.execute("INSERT OR IGNORE INTO users (user_id, username, role, balance, reg_date) VALUES (?, ?, ?, ?, ?)",
                  (ADMIN_ID, "Admin", "ADMIN", 10000, datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
        conn.commit()
        conn.close()
    except Exception as e:
        print("DB İnit Hata:", e)

def get_user(user_id):
    try:
        conn = sqlite3.connect('bot_data.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        user = c.fetchone()
        conn.close()
        return user
    except:
        return None

def create_user(user_id, username):
    try:
        conn = sqlite3.connect('bot_data.db')
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO users (user_id, username, reg_date) VALUES (?, ?, ?)",
                  (user_id, username, datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
        if user_id == ADMIN_ID:
            c.execute("UPDATE users SET role='ADMIN', balance=10000 WHERE user_id=?", (ADMIN_ID,))
        conn.commit()
        conn.close()
    except Exception as e:
        print("Create User Hata:", e)

def update_balance(user_id, amount):
    try:
        conn = sqlite3.connect('bot_data.db')
        c = conn.cursor()
        c.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (amount, user_id))
        conn.commit()
        conn.close()
    except Exception as e:
        print("Update Balance Hata:", e)

def add_history(user_id, action, detail, amount=0):
    try:
        conn = sqlite3.connect('bot_data.db')
        c = conn.cursor()
        c.execute("INSERT INTO history (user_id, action, detail, amount, date) VALUES (?, ?, ?, ?, ?)",
                  (user_id, action, detail, amount, datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
        conn.commit()
        conn.close()
    except Exception as e:
        print("Add History Hata:", e)

def is_admin(user_id):
    return user_id == ADMIN_ID

def is_dealer(user_id):
    if user_id == ADMIN_ID:
        return True
    user = get_user(user_id)
    if not user:
        return False
    return user[2] in ['ADMIN', 'BAYI']

def get_stock_count(duration):
    try:
        conn = sqlite3.connect('bot_data.db')
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM keys WHERE duration=? AND status='available'", (duration,))
        count = c.fetchone()[0]
        conn.close()
        return count
    except:
        return 0

def create_main_menu(user_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    if is_dealer(user_id):
        markup.add(
            types.InlineKeyboardButton("🛒 Mağaza", callback_data="store"),
            types.InlineKeyboardButton("📦 Siparişlerim", callback_data="orders"),
            types.InlineKeyboardButton("💰 Bakiyem", callback_data="balance"),
            types.InlineKeyboardButton("⭐ Favorilerim", callback_data="favorites"),
            types.InlineKeyboardButton("🔄 Cihaz Sıfırla", callback_data="reset_device"),
            types.InlineKeyboardButton("📞 Destek", callback_data="support"),
            types.InlineKeyboardButton("📜 İşlem Geçmişi", callback_data="history"),
            types.InlineKeyboardButton("👤 @DEXTERWXP", callback_data="dexter")
        )
    else:
        markup.add(
            types.InlineKeyboardButton("📞 Destek", callback_data="support"),
            types.InlineKeyboardButton("👤 @DEXTERWXP", callback_data="dexter")
        )
    return markup

def get_user_info_text(user_id):
    user = get_user(user_id)
    if not user and user_id != ADMIN_ID:
        return "❌ Kullanıcı bulunamadı."
    role = "ADMIN" if user_id == ADMIN_ID else (user[2] if user else "KULLANICI")
    balance = 10000 if user_id == ADMIN_ID else (user[3] if user else 0)
    username = "Admin" if user_id == ADMIN_ID else (user[1] or "Belirtilmemiş")
    role_emoji = {"ADMIN": "👑", "BAYI": "🤝", "KULLANICI": "👤"}.get(role, "👤")
    if is_dealer(user_id):
        text = f"🌟 Merhaba CheetahPanel'e Hoş Geldiniz {username}! 🌟\n"
        text += f"{role_emoji} Rol: {role}\n"
        text += f"💰 Bakiye: {balance} TL\n\n📋 Lütfen bir işlem seçin:"
    else:
        text = f"🌟 Merhaba {username}! 🌟\n"
        text += f"{role_emoji} Rol: {role}\n"
        text += f"💰 Bakiye: {balance} TL\n\n"
        text += "❌ Üzgünüz, bu bot sadece bayiler ve adminler içindir!\n"
        text += "📞 İletişim için: @DEXTERWXP"
    return text

@bot.message_handler(commands=['start'])
def start_command(message):
    try:
        user_id = message.from_user.id
        username = message.from_user.username or message.from_user.first_name
        create_user(user_id, username)
        markup = create_main_menu(user_id)
        text = get_user_info_text(user_id)
        bot.send_message(user_id, text, reply_markup=markup)
    except Exception as e:
        print("Start Komut Hata:", e)

@bot.message_handler(commands=['stokekle'])
def add_stock(message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        bot.reply_to(message, "⛔ Bu komut sadece admin içindir!")
        return
    try:
        lines = message.text.split('\n')
        if len(lines) < 2:
            bot.reply_to(message, "❌ Eksik kullanım!\nÖrnek:\n/stokekle 1gun\nKEY1\nKEY2")
            return
        parts = lines[0].split()
        if len(parts) < 2:
            bot.reply_to(message, "❌ Süre belirtilmedi!\nÖrnek: /stokekle 1gun")
            return
        duration = parts[1]
        valid_durations = ['1gun', '1hafta', '1ay', '2ay']
        if duration not in valid_durations:
            bot.reply_to(message, "❌ Geçersiz süre! (1gun, 1hafta, 1ay, 2ay olmalı)")
            return
        conn = sqlite3.connect('bot_data.db')
        c = conn.cursor()
        duration_days = {'1gun': 1, '1hafta': 7, '1ay': 30, '2ay': 60}
        count = 0
        for line in lines[1:]:
            key = line.strip()
            if key and len(key) >= 5:
                expire_date = datetime.datetime.now() + datetime.timedelta(days=duration_days[duration])
                expire_date_str = expire_date.strftime("%Y-%m-%d %H:%M")
                c.execute("INSERT OR IGNORE INTO keys (key, duration, status, expire_date) VALUES (?, ?, ?, ?)",
                         (key, duration, 'available', expire_date_str))
                count += 1
        conn.commit()
        conn.close()
        bot.reply_to(message, f"✅ {count} adet {duration} süreli lisans eklendi!")
    except Exception as e:
        bot.reply_to(message, f"❌ Hata oluştu ama bot çökmedi: {str(e)}")

@bot.message_handler(commands=['bayiekle'])
def add_dealer(message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        bot.reply_to(message, "⛔ Bu komut sadece admin içindir!")
        return
    try:
        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, "❌ Eksik kullanım!\nÖrnek: /bayiekle 1472412382")
            return
        target_id = int(args[1])
        conn = sqlite3.connect('bot_data.db')
        c = conn.cursor()
        c.execute("UPDATE users SET role='BAYI' WHERE user_id=?", (target_id,))
        conn.commit()
        conn.close()
        bot.reply_to(message, f"✅ Kullanıcı {target_id} başarıyla bayi yapıldı! 🤝")
    except Exception as e:
        bot.reply_to(message, f"❌ Hata oluştu ama bot çökmedi: {str(e)}")

@bot.message_handler(commands=['bayicikar'])
def remove_dealer(message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        bot.reply_to(message, "⛔ Bu komut sadece admin içindir!")
        return
    try:
        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, "❌ Eksik kullanım!\nÖrnek: /bayicikar 1472412382")
            return
        target_id = int(args[1])
        conn = sqlite3.connect('bot_data.db')
        c = conn.cursor()
        c.execute("UPDATE users SET role='KULLANICI' WHERE user_id=?", (target_id,))
        conn.commit()
        conn.close()
        bot.reply_to(message, f"✅ Kullanıcı {target_id} bayi statüsünden çıkarıldı. 👤")
    except Exception as e:
        bot.reply_to(message, f"❌ Hata oluştu ama bot çökmedi: {str(e)}")

@bot.message_handler(commands=['bakiyeekle'])
def add_balance(message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        bot.reply_to(message, "⛔ Bu komut sadece admin içindir.")
        return
    try:
        parts = message.text.split()
        if len(parts) < 3:
            bot.reply_to(message, "❌ Eksik kullanım!\nÖrnek: /bakiyeekle 1472412382 100")
            return
        target_id = int(parts[1])
        amount = int(parts[2])
        update_balance(target_id, amount)
        add_history(target_id, "Admin Bakiye Ekleme", f"{amount} TL eklendi", amount)
        bot.reply_to(message, f"✅ {target_id} ID'li kullanıcıya {amount} TL bakiye eklendi! 💰")
        try:
            bot.send_message(target_id, f"🎉 Hesabınıza {amount} TL bakiye eklendi! 💰")
        except:
            pass
    except Exception as e:
        bot.reply_to(message, f"❌ Hata oluştu ama bot çökmedi: {str(e)}")

@bot.message_handler(commands=['keyreset'])
def reset_key(message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        bot.reply_to(message, "⛔ Bu komut sadece admin içindir!")
        return
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "❌ Eksik kullanım!\nÖrnek: /keyreset ABC123XYZ")
            return
        key = parts[1]
        conn = sqlite3.connect('bot_data.db')
        c = conn.cursor()
        c.execute("UPDATE keys SET used_by=NULL, hwid=NULL, used_date=NULL, status='available' WHERE key=?", (key,))
        conn.commit()
        conn.close()
        bot.reply_to(message, f"✅ {key} lisansı başarıyla sıfırlandı! 🔄")
    except Exception as e:
        bot.reply_to(message, f"❌ Hata oluştu ama bot çökmedi: {str(e)}")

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    try:
        user_id = call.from_user.id
        data = call.data
        
        if not is_dealer(user_id):
            bot.answer_callback_query(call.id, "❌ Bu işlem sadece bayiler içindir! @DEXTERWXP", show_alert=True)
            return
        
        if data == "main_menu":
            markup = create_main_menu(user_id)
            text = get_user_info_text(user_id)
            try:
                bot.edit_message_text(text, user_id, call.message.message_id, reply_markup=markup)
            except:
                bot.send_message(user_id, text, reply_markup=markup)
            return
        
        if data == "store":
            stock_1gun = get_stock_count("1gun")
            stock_1hafta = get_stock_count("1hafta")
            stock_1ay = get_stock_count("1ay")
            stock_2ay = get_stock_count("2ay")
            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(
                types.InlineKeyboardButton(f"1 Gün (30 TL) {'🟢' if stock_1gun>0 else '🔴 Stok Yok'}", callback_data="buy_1gun" if stock_1gun>0 else "no_stock"),
                types.InlineKeyboardButton(f"1 Hafta (100 TL) {'🟢' if stock_1hafta>0 else '🔴 Stok Yok'}", callback_data="buy_1hafta" if stock_1hafta>0 else "no_stock"),
                types.InlineKeyboardButton(f"1 Ay (220 TL) {'🟢' if stock_1ay>0 else '🔴 Stok Yok'}", callback_data="buy_1ay" if stock_1ay>0 else "no_stock"),
                types.InlineKeyboardButton(f"2 Ay (450 TL) {'🟢' if stock_2ay>0 else '🔴 Stok Yok'}", callback_data="buy_2ay" if stock_2ay>0 else "no_stock"),
                types.InlineKeyboardButton("◀️ Geri", callback_data="main_menu")
            )
            text = f"🛒 Mağaza\n\n📊 Stok Durumu:\n🟢 1 Gün: {stock_1gun} adet\n🟢 1 Hafta: {stock_1hafta} adet\n🟢 1 Ay: {stock_1ay} adet\n🟢 2 Ay: {stock_2ay} adet"
            try:
                bot.edit_message_text(text, user_id, call.message.message_id, reply_markup=markup)
            except:
                bot.send_message(user_id, text, reply_markup=markup)
            return
        
        if data.startswith("buy_"):
            duration = data.split("_")[1]
            prices = {"1gun": 30, "1hafta": 100, "1ay": 220, "2ay": 450}
            price = prices.get(duration, 0)
            stock_count = get_stock_count(duration)
            if stock_count == 0:
                bot.answer_callback_query(call.id, "❌ Stokta lisans kalmadı!", show_alert=True)
                return
            user = get_user(user_id)
            user_bal = 10000 if user_id == ADMIN_ID else (user[3] if user else 0)
            if user_bal < price:
                bot.answer_callback_query(call.id, f"❌ Yetersiz bakiye! Mevcut: {user_bal} TL", show_alert=True)
                return
            conn = sqlite3.connect('bot_data.db')
            c = conn.cursor()
            c.execute("SELECT key, expire_date FROM keys WHERE duration=? AND status='available' LIMIT 1", (duration,))
            key_data = c.fetchone()
            if not key_data:
                conn.close()
                bot.answer_callback_query(call.id, "❌ Stokta lisans kalmadı!", show_alert=True)
                return
            key = key_data[0]
            expire_date = key_data[1]
            c.execute("UPDATE keys SET used_by=?, status='used', used_date=? WHERE key=?", (user_id, datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), key))
            c.execute("UPDATE users SET balance = balance - ? WHERE user_id=?", (price, user_id))
            c.execute("INSERT INTO history (user_id, action, detail, amount, date) VALUES (?, ?, ?, ?, ?)", (user_id, "Lisans Satın Alındı", f"{duration} - {key}", -price, datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
            conn.commit()
            conn.close()
            markup = types.InlineKeyboardMarkup()
            copy_btn = types.InlineKeyboardButton("📋 Key'i Kopyala", callback_data=f"copy_{key}")
            back_btn = types.InlineKeyboardButton("◀️ Ana Menü", callback_data="main_menu")
            markup.add(copy_btn, back_btn)
            text = f"✅ Lisans satın alındı!\n\n🔑 Key: {key}\n⏱️ Süre: {duration}\n📅 Bitiş: {expire_date}"
            try:
                bot.edit_message_text(text, user_id, call.message.message_id, reply_markup=markup)
            except:
                bot.send_message(user_id, text, reply_markup=markup)
            return
        
        if data.startswith("copy_"):
            key = data.split("_")[1]
            bot.answer_callback_query(call.id, f"✅ Key kopyalandı: {key}", show_alert=True)
            return
        
        if data == "orders":
            conn = sqlite3.connect('bot_data.db')
            c = conn.cursor()
            c.execute("SELECT key, duration, used_date, expire_date FROM keys WHERE used_by=? ORDER BY used_date DESC LIMIT 10", (user_id,))
            orders = c.fetchall()
            conn.close()
            if not orders:
                text = "📦 Siparişlerim\n\n❌ Henüz siparişiniz yok."
            else:
                text = "📦 Siparişlerim\n\n"
                for idx, (key, duration, used_date, expire_date) in enumerate(orders, 1):
                    expired = False
                    if expire_date:
                        try:
                            exp = datetime.datetime.strptime(expire_date, "%Y-%m-%d %H:%M")
                            if datetime.datetime.now() > exp:
                                expired = True
                        except:
                            pass
                    status = "🔴 Süresi Doldu" if expired else "🟢 Aktif"
                    text += f"{idx}. 🔑 {key}\n   ⏱️ {duration}\n   📅 Bitiş: {expire_date}\n   📊 {status}\n\n"
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("◀️ Geri", callback_data="main_menu"))
            try:
                bot.edit_message_text(text, user_id, call.message.message_id, reply_markup=markup)
            except:
                bot.send_message(user_id, text, reply_markup=markup)
            return
        
        if data == "balance":
            user_bal = 10000 if user_id == ADMIN_ID else (get_user(user_id)[3] if get_user(user_id) else 0)
            text = f"💰 Bakiyeniz\n\n💵 Mevcut Bakiye: {user_bal} TL\n👤 Kullanıcı: Admin\n👑 Rol: ADMIN" if user_id == ADMIN_ID else f"💰 Bakiyeniz\n\n💵 Mevcut Bakiye: {user_bal} TL"
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton("💳 Bakiye Yükle", callback_data="add_balance_request"),
                types.InlineKeyboardButton("◀️ Geri", callback_data="main_menu")
            )
            try:
                bot.edit_message_text(text, user_id, call.message.message_id, reply_markup=markup)
            except:
                bot.send_message(user_id, text, reply_markup=markup)
            return
        
        if data == "add_balance_request":
            text = "💰 Bakiye Yükleme\n\n📌 Bakiye yüklemek için @DEXTERWXP ile iletişime geçin!"
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("◀️ Geri", callback_data="balance"))
            try:
                bot.edit_message_text(text, user_id, call.message.message_id, reply_markup=markup)
            except:
                bot.send_message(user_id, text, reply_markup=markup)
            return
        
        if data == "favorites":
            conn = sqlite3.connect('bot_data.db')
            c = conn.cursor()
            c.execute("SELECT key FROM favorites WHERE user_id=?", (user_id,))
            favs = c.fetchall()
            conn.close()
            if not favs:
                text = "⭐ Favorilerim\n\n❌ Henüz favori lisansınız yok."
            else:
                text = "⭐ Favori Lisanslarınız\n\n"
                for idx, (key,) in enumerate(favs, 1):
                    text += f"{idx}. 🔑 {key}\n"
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("◀️ Geri", callback_data="main_menu"))
            try:
                bot.edit_message_text(text, user_id, call.message.message_id, reply_markup=markup)
            except:
                bot.send_message(user_id, text, reply_markup=markup)
            return
        
        if data == "reset_device":
            conn = sqlite3.connect('bot_data.db')
            c = conn.cursor()
            c.execute("SELECT key, duration, expire_date FROM keys WHERE used_by=? AND status='used'", (user_id,))
            keys = c.fetchall()
            conn.close()
            if not keys:
                text = "🔄 Cihaz Sıfırla\n\n❌ Kullanımda lisansınız yok."
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton("◀️ Geri", callback_data="main_menu"))
            else:
                text = "🔄 Cihaz Sıfırla\n\nSadece süresi dolmamış lisanslar sıfırlanabilir!\n"
                markup = types.InlineKeyboardMarkup(row_width=1)
                has_valid = False
                for key, duration, expire_date in keys:
                    expired = False
                    if expire_date:
                        try:
                            exp = datetime.datetime.strptime(expire_date, "%Y-%m-%d %H:%M")
                            if datetime.datetime.now() > exp:
                                expired = True
                        except:
                            pass
                    if not expired:
                        has_valid = True
                        markup.add(types.InlineKeyboardButton(f"⏱️ {duration} - {key[:8]}... (Aktif)", callback_data=f"reset_{key}"))
                    else:
                        markup.add(types.InlineKeyboardButton(f"⏱️ {duration} - {key[:8]}... (🔴 Süresi Doldu)", callback_data="expired_key"))
                if not has_valid:
                    text += "\n❌ Sıfırlanabilecek aktif lisans yok."
                markup.add(types.InlineKeyboardButton("◀️ Geri", callback_data="main_menu"))
            try:
                bot.edit_message_text(text, user_id, call.message.message_id, reply_markup=markup)
            except:
                bot.send_message(user_id, text, reply_markup=markup)
            return
        
        if data.startswith("reset_"):
            key = data.split("_")[1]
            conn = sqlite3.connect('bot_data.db')
            c = conn.cursor()
            c.execute("SELECT expire_date FROM keys WHERE key=? AND used_by=?", (key, user_id))
            result = c.fetchone()
            if not result:
                conn.close()
                bot.answer_callback_query(call.id, "❌ Lisans bulunamadı!", show_alert=True)
                return
            expire_date = result[0]
            if expire_date:
                try:
                    exp = datetime.datetime.strptime(expire_date, "%Y-%m-%d %H:%M")
                    if datetime.datetime.now() > exp:
                        conn.close()
                        bot.answer_callback_query(call.id, "❌ Lisansın süresi dolmuş! Sıfırlanamaz!", show_alert=True)
                        return
                except:
                    pass
            c.execute("UPDATE keys SET hwid=NULL WHERE key=? AND used_by=?", (key, user_id))
            conn.commit()
            conn.close()
            bot.answer_callback_query(call.id, "✅ Cihaz sıfırlandı!", show_alert=True)
            markup = create_main_menu(user_id)
            text = get_user_info_text(user_id)
            try:
                bot.edit_message_text(text, user_id, call.message.message_id, reply_markup=markup)
            except:
                bot.send_message(user_id, text, reply_markup=markup)
            return
        
        if data == "support":
            text = "📞 Destek Merkezi\n\n💬 Yardım için: @DEXTERWXP"
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("◀️ Geri", callback_data="main_menu"))
            try:
                bot.edit_message_text(text, user_id, call.message.message_id, reply_markup=markup)
            except:
                bot.send_message(user_id, text, reply_markup=markup)
            return
        
        if data == "dexter":
            text = "👤 @DEXTERWXP\n\n🔹 Kurucu ve Baş Geliştirici\n🔹 CheetahPanel Sahibi\n🔹 PUBG Mobile Hile Uzmanı\n\n📌 İletişim: @DEXTERWXP"
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("◀️ Geri", callback_data="main_menu"))
            try:
                bot.edit_message_text(text, user_id, call.message.message_id, reply_markup=markup)
            except:
                bot.send_message(user_id, text, reply_markup=markup)
            return
        
        if data == "history":
            conn = sqlite3.connect('bot_data.db')
            c = conn.cursor()
            c.execute("SELECT action, detail, amount, date FROM history WHERE user_id=? ORDER BY date DESC LIMIT 20", (user_id,))
            history = c.fetchall()
            conn.close()
            if not history:
                text = "📜 İşlem Geçmişi\n\n❌ Henüz işlem yok."
            else:
                text = "📜 İşlem Geçmişi (son 20)\n\n"
                for action, detail, amount, date in history:
                    emoji = "🛒" if "Satın" in action else "💰" if "Ekle" in action else "📌"
                    amount_text = f"+{amount}" if amount > 0 else str(amount)
                    text += f"{emoji} {action}\n   📝 {detail}\n   💳 {amount_text} TL\n   📅 {date}\n\n"
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("◀️ Geri", callback_data="main_menu"))
            try:
                bot.edit_message_text(text, user_id, call.message.message_id, reply_markup=markup)
            except:
                bot.send_message(user_id, text, reply_markup=markup)
            return
    except Exception as e:
        print("Callback Hata:", e)

@bot.callback_query_handler(func=lambda call: call.data == "no_stock")
def no_stock_handler(call):
    try:
        bot.answer_callback_query(call.id, "❌ Stokta yok!", show_alert=True)
    except:
        pass

@bot.callback_query_handler(func=lambda call: call.data == "expired_key")
def expired_key_handler(call):
    try:
        bot.answer_callback_query(call.id, "❌ Süresi dolmuş!", show_alert=True)
    except:
        pass

if __name__ == "__main__":
    init_db()
    print("🤖 Bot başlatılıyor...")
    print("✅ Bot çalışıyor!")
    while True:
        try:
            bot.polling(none_stop=True, interval=0)
        except Exception as e:
            print(f"❌ Kritik Hata: {e}")
            time.sleep(5)
