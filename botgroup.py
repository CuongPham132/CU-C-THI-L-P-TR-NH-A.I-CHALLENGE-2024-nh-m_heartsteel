import telebot
import sqlite3
from datetime import datetime
from telebot import types
bot = telebot.TeleBot("6823471751:AAERYDhj3rvuxgL6kwzY3o2V_oq44p2CRek")

default_message_status = 1
ban_chat_enabled = False

def create_connection():
    return sqlite3.connect('members.db')

def add_member(cursor, user_id):
    cursor.execute("INSERT INTO members (user_id, message_enabled) VALUES (?, ?)",
                   (user_id, 1))

def update_message_status(cursor, user_id, message_enabled):
    cursor.execute("UPDATE members SET message_enabled=? WHERE user_id=?", (message_enabled, user_id))

def is_member_exist(cursor, user_id):
    cursor.execute("SELECT * FROM members WHERE user_id=?", (user_id,))
    return cursor.fetchone() is not None

def delete_member(cursor, user_id):
    cursor.execute("DELETE FROM members WHERE user_id=?", (user_id,))
    
def is_user_blocked(cursor, user_id):
    cursor.execute("SELECT message_enabled FROM members WHERE user_id=?", (user_id,))
    result = cursor.fetchone()
    if result:
        return result[0] == 0
    return False

@bot.message_handler(commands=['start'])
def start(message):
    items = [
        '📨  Hướng dẫn kết nối Bot',
        '📝  Sổ lệnh quản lí nhóm',
        '📲  Liên hệ quản trị viên',
        '📮  Thông báo'
    ]
    markup = types.ReplyKeyboardMarkup(row_width=1)
    buttons = [types.KeyboardButton(item) for item in items]
    markup.add(*buttons)
    current_hour = datetime.now().hour
    daytime = "sáng" if 6 <= current_hour < 12 else "chiều" if 12 <= current_hour < 18 else "tối"
    bot.send_message(message.chat.id, f"🎉 Chào buổi {daytime} {message.from_user.first_name} {message.from_user.last_name}, tôi có thể giúp gì cho bạn ?",
                     reply_markup=markup) 
     
@bot.message_handler(commands=['closechat'])
def disable_message(message):
    if message.chat.type in ["group", "supergroup"]:
        if message.from_user.id in [admin.user.id for admin in bot.get_chat_administrators(message.chat.id)]:
            try:
                command, user_id = message.text.split(maxsplit=1)
                user_id = int(user_id)
                conn = create_connection()
                cursor = conn.cursor()
                if is_member_exist(cursor, user_id):
                    if is_user_blocked(cursor, user_id):
                        bot.reply_to(message, f"Người dùng có ID {user_id} đã bị khóa tin nhắn trước đó!")
                    else:
                        update_message_status(cursor, user_id, 0)
                        conn.commit()
                        bot.reply_to(message, f"Đã đóng tin nhắn cho người dùng có ID {user_id} trong nhóm!")
                else:
                    bot.reply_to(message, f"Người dùng có ID {user_id} không tồn tại trong cơ sở dữ liệu!")
                conn.close()
            except ValueError:
                bot.reply_to(message, "❌ Vui lòng nhập user_id cần đóng tin nhắn!")
        else:
            bot.reply_to(message, "❌ Bạn không phải là admin của nhóm!")
    else:
        bot.reply_to(message, "❌ Xin lỗi, lệnh này chỉ có thể được sử dụng trong một nhóm hoặc siêu nhóm.")

@bot.message_handler(commands=['openchat'])
def enable_message(message):
    if message.chat.type in ["group", "supergroup"]:
        if message.from_user.id in [admin.user.id for admin in bot.get_chat_administrators(message.chat.id)]:
            try:
                command, user_id = message.text.split(maxsplit=1)
                user_id = int(user_id)

                conn = create_connection()
                cursor = conn.cursor()
                if is_member_exist(cursor, user_id):
                    if is_user_blocked(cursor, user_id):
                        update_message_status(cursor, user_id, 1)
                        conn.commit()
                        bot.reply_to(message, f"Đã mở tin nhắn cho người dùng có ID {user_id} trong nhóm!")
                    else:
                        bot.reply_to(message, f"Người dùng có ID {user_id} không bị khóa tin nhắn!")
                else:
                    bot.reply_to(message, f"Người dùng có ID {user_id} không tồn tại trong cơ sở dữ liệu!")
                conn.close()
            except ValueError:
                bot.reply_to(message, "❌ Vui lòng nhập user_id cần mở tin nhắn!")
        else:
            bot.reply_to(message, "❌ Bạn không phải là admin của nhóm!")
    else:
        bot.reply_to(message, "❌ Xin lỗi, lệnh này chỉ có thể được sử dụng trong một nhóm hoặc siêu nhóm.")

@bot.message_handler(commands=['groupchat']) 
def toggle_ban_chat(message):
    if message.chat.type in ["group", "supergroup"]:
        global ban_chat_enabled
        if message.from_user.id in [admin.user.id for admin in bot.get_chat_administrators(message.chat.id)]:
            ban_chat_enabled = not ban_chat_enabled
            permissions = types.ChatPermissions(can_send_messages=not ban_chat_enabled)
            bot.set_chat_permissions(message.chat.id, permissions)
            if ban_chat_enabled:
                bot.reply_to(message, "Đã bật chế độ cấm chat cho toàn bộ nhóm!")
            else:
                bot.reply_to(message, "Đã tắt chế độ cấm chat cho toàn bộ nhóm!")
        else:
            bot.reply_to(message, "❌ Bạn không phải là admin của nhóm!")
    else:
        bot.reply_to(message, "❌ Xin lỗi, lệnh này chỉ có thể được sử dụng trong một nhóm hoặc siêu nhóm.")

@bot.message_handler(commands=['block'])
def kick_user(message):
    if message.chat.type in ["group", "supergroup"]:
        if message.from_user.id in [admin.user.id for admin in bot.get_chat_administrators(message.chat.id)]:
            try:
                command, user_id = message.text.split(maxsplit=1)
                user_id = int(user_id)
                bot.kick_chat_member(message.chat.id, user_id)
                bot.reply_to(message, f"Đã kích người dùng có ID {user_id} ra khỏi nhóm!")
            except ValueError:
                bot.reply_to(message, "Vui lòng nhập đúng định dạng lệnh: /block <user_id>")
        else:
            bot.reply_to(message, "❌ Bạn không có quyền thực hiện thao tác này trong nhóm!")
    else:
        bot.reply_to(message, "❌ Xin lỗi, lệnh này chỉ có thể được sử dụng trong một nhóm hoặc siêu nhóm.")

@bot.message_handler(commands=['getid'])
def get_user_id(message):
    if message.chat.type == "group" or message.chat.type == "supergroup":
        if message.reply_to_message:
            user_id = message.reply_to_message.from_user.id
            bot.reply_to(message, f"ID của người dùng là: {user_id}")
        else:
            bot.reply_to(message, "Hãy trả lời tin nhắn của người dùng để lấy ID của họ.")
    else:
        bot.reply_to(message, "❌ Lệnh này chỉ có thể được sử dụng trong một nhóm hoặc siêu nhóm!")

@bot.message_handler(func=lambda message: True, content_types=['new_chat_members'])
def new_member_welcome(message):
    conn = create_connection()
    cursor = conn.cursor()
    for member in message.new_chat_members:
        if not is_member_exist(cursor, member.id):
            add_member(cursor, member.id)
            bot.reply_to(message, f"🎊 Chào mừng {member.first_name} đến với nhóm! 🎊")
    conn.commit()
    conn.close()

@bot.message_handler(func=lambda message: True, content_types=['left_chat_member'])
def member_left(message):
    member_id = message.left_chat_member.id
    conn = create_connection()
    cursor = conn.cursor()
    if is_member_exist(cursor, member_id):
        delete_member(cursor, member_id)
        bot.reply_to(message, f"🙈 Tiếc quá ! {member_id} đã rời đi! 🙈")
    conn.commit()
    conn.close()

@bot.message_handler(commands=['allmess'])
def send_message_to_all_members(message):
    try:
        if message.from_user.id not in [admin.user.id for admin in bot.get_chat_administrators(message.chat.id)]:
            bot.reply_to(message, "❌ Bạn không có quyền thực hiện thao tác này trong nhóm!")
            return

        if len(message.text.split()) < 2:
            bot.reply_to(message, "❌ Vui lòng cung cấp nội dung tin nhắn để gửi!")
            return

        text_to_send = ' '.join(message.text.split()[1:])

        conn = create_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT user_id FROM members")
        rows = cursor.fetchall()

        for row in rows:
            user_id = row[0]
            bot.send_message(user_id, text_to_send)

        bot.reply_to(message, "✅ Đã gửi tin nhắn hàng loạt thành công!")

        conn.close()
    except Exception as e:
        bot.reply_to(message, f"❌ Đã xảy ra lỗi: {e}")

@bot.message_handler(commands=['data'])
def print_database(message):
    if message.chat.type not in ["group", "supergroup"]:
        try:
                conn = create_connection()
                cursor = conn.cursor()

                cursor.execute("SELECT * FROM members")
                rows = cursor.fetchall()
                if len(rows) > 0:
                    response = "Danh sách thành viên:\n"
                    for row in rows:
                        response += f"{row[0]} {row[1]}\n"
                    bot.reply_to(message, response)
                else:
                    bot.reply_to(message, "Cơ sở dữ liệu trống.")
                conn.close()
        except Exception as e:
            bot.reply_to(message, f"❌ Đã xảy ra lỗi: {e}")
    else:
        bot.reply_to(message, "❌ Lệnh này chỉ có thể được sử dụng trong bot")

@bot.message_handler(commands=['menu'])
def menu_commands(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    item5 = types.InlineKeyboardButton("👉 GROUP CHAT", callback_data='groupchat')
    item4 = types.InlineKeyboardButton("👉 OPEN CHAT", callback_data='openchat')
    item3 = types.InlineKeyboardButton("👉 CLOSE CHAT", callback_data='closechat')
    item2 = types.InlineKeyboardButton("👉 BLOCK", callback_data='block')
    item1 = types.InlineKeyboardButton("👉 GETID", callback_data='getid')
    markup.add(item1, item2 ,item3, item4, item5)
    bot.send_message(message.chat.id,"🙈 Bảng menu lệnh quản lí: ",reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    if call.data == 'groupchat':
        toggle_ban_chat(call.message)
    elif call.data == 'openchat':
        enable_message(call.message)
    elif call.data == 'closechat':
        disable_message(call.message)
    elif call.data == 'block':
        kick_user(call.message)
    elif call.data == 'getid':
        get_user_id(call.message)
    else:
        pass
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if message.text == '📨  Hướng dẫn kết nối Bot':
        bot.send_message(message.chat.id, "👀 Hãy lưu ý các bước thêm tôi vào nhóm:\n"
                                          "🔖 Add tôi vào nhóm bằng cách tìm kiếm ``.\n"
                                          "🔖 Cài cho tôi quyền phó nhóm hoặc tương đương.\n"
                                          "🔖 Sử dụng các lệnh lập trình sẵn để quản lí nhóm.\n"
                                          "🔖 Bản có ' game play ' sẽ phải trả phí\n"
                                          "🌺 Thanks! 🌺",parse_mode="Markdown")
    elif message.text == '📝  Sổ lệnh quản lí nhóm':
        bot.send_message(message.chat.id,"🌺 Dưới đây là các lệnh quản lí nhóm:\n\n"
                                         "✅ `/groupchat` :Tắt hoặc mở chat toàn nhóm\n"
                                         "✅ `/closechat` :Khóa chat thành viên thông qua ID\n"
                                         "✅ `/openchat` :Mở chat thành viên thông qua ID\n"
                                         "✅ `/block` :Kích thành viên ra khỏi nhóm chat\n"
                                         "✅ `/getid` :Lấy ID thành viên thông qua reply\n"
                                         "❌ `/allmess` :Gửi tin nhắn đến tất cả thành viên trong nhóm\n"
                                         "♻ `/data` :Lấy dữ liệu nhóm , ID của các thành viên.\n\n\n"
                                         "✅  chỉ có thể dùng trong nhóm\n"
                                         "♻  chỉ có thể dùng trong bot\n"
                                         "❌  không nên dùng nhiều",parse_mode="Markdown")
    elif message.text == '📲  Liên hệ quản trị viên':
        bot.send_message(message.chat.id,"👀 Hiện tại không có quản trị viên nào online.\n🌺 Thanks! 🌺")
    elif message.text == '📮  Thông báo':
        bot.send_message(message.chat.id,"👀 Hiện tại không có thông báo nào !\n🌺 Thanks! 🌺",parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id,"👀 Xin lỗi tôi không hiểu ý bạn\n🌺 Thanks! 🌺",parse_mode="Markdown")
bot.polling()