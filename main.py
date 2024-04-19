import telebot
import re
import os
import cv2
import json
import pyttsx3
from pyzbar.pyzbar import decode
import numpy as np
import pytesseract
import requests
from bs4 import BeautifulSoup
from googletrans import Translator
from datetime import datetime
from telebot import types
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
TOKEN = '6823471751:AAERYDhj3rvuxgL6kwzY3o2V_oq44p2CRek'
IMAGE_DIRECTORY = "images"
bot = telebot.TeleBot(TOKEN)
def get_news():
    hot_news = []
    r = requests.get('https://vnexpress.net/')
    soup = BeautifulSoup(r.text, 'html.parser')
    mydivs = soup.find_all("h3", {"class": "title-news"})
    count = 0
    for new in mydivs:
        newdict = {}
        newdict["link"] = new.a.get("href")
        newdict["title"] = new.a.get("title")
        hot_news.append(newdict)
        count += 1
        if count == 2:
            break
    return hot_news
def read_qr_code(image):
    decoded_objects = decode(image)

    if decoded_objects:
        result = ""
        for obj in decoded_objects:
            result += f"Type: {obj.type}, Data: {obj.data.decode('utf-8')}\n"
        return result
    else:
        return "Không tìm thấy mã QR trong hình ảnh."

def save_database(file_path, data):
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=2)
def encode_ascii(text):
    encoded_text = []
    for char in text:
        encoded_text.append(ord(char))
    return encoded_text
def cosine_similarity(vector1, vector2):
    min_length = min(len(vector1), len(vector2))
    vector1 = vector1[:min_length]
    vector2 = vector2[:min_length]
    dot_product = np.dot(vector1, vector2)
    norm_vector1 = np.linalg.norm(vector1)
    norm_vector2 = np.linalg.norm(vector2)
    similarity = dot_product / (norm_vector1 * norm_vector2)
    return similarity
def load_database(file_path):
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
    except FileNotFoundError:
        data = {"questions": []}
    return data
database = load_database("database.json")
def save_new_answer(message, user_input):
    new_answer = message.text
    encoded_text = encode_ascii(user_input)
    if new_answer.lower() != "skip":
        database["questions"].append({"question": user_input, "answer": new_answer, "encoded": encoded_text})
        save_database("database.json", database)
        bot.send_message(message.chat.id," Cảm ơn bạn ! Có thể đáp án này chưa chính xác nhưng tôi sẽ ghi nhận \n 🫶 Iu Bạn Nhìu Nhìu Nhìu !!!! 🫶")
    else:
        bot.send_message(message.chat.id, "Đã bỏ qua việc thêm câu trả lời.")
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton('🎊 ALL READY 🎊', callback_data='button_ready'))
    bot.send_message(message.chat.id,"⚠️ Khi bạn dùng Bot phải tuân thủ điều khoản của chúng tôi !\n", reply_markup=markup)

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    if message.caption and "/imgtext" in message.caption:
        bot.send_message(message.chat.id, "♻ Đang lọc chữ từ ảnh...")
        user_id = message.from_user.id
        image_path = os.path.join(IMAGE_DIRECTORY, f"{user_id}.jpg")
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        with open(image_path, 'wb') as new_file:
            new_file.write(downloaded_file)
        extracted_text = extract_text_from_image(image_path)
        bot.reply_to(message, extracted_text)
        os.remove(image_path)
    elif message.caption and "/qr" in message.caption:
        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        nparr = np.frombuffer(downloaded_file, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        qr_result = read_qr_code(image)
        bot.reply_to(message, qr_result)
    else:
        bot.reply_to(message, "❌ Hãy sử dụng lệnh /imgtext")
def extract_text_from_image(image_path):
    image = cv2.imread(image_path)
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    extracted_text = pytesseract.image_to_string(gray_image, lang='eng')
    return extracted_text
@bot.message_handler(commands=['trans'])
def handle_trans_command(message):
    bot.send_message(message.chat.id, "♻ Loading...")
    translator = Translator()
    text_to_translate = ' '.join(message.text.split()[1:])
    try:
        result = translator.detect(text_to_translate)
        if result is not None and hasattr(result, 'lang'):
            if result.lang == 'vi':
                translated_text = translator.translate(text_to_translate, src='vi', dest='en').text
                text = re.sub(r'\s+', ' ', translated_text).strip()
                bot.send_message(message.chat.id, 
                                 "📝 Đoạn văn được tôi ' phiên dịch ' như sau :\n"
                                 f"`{text}`\n"
                                 "", parse_mode="Markdown")
            elif result.lang == 'en':
                translation = translator.translate(text_to_translate, src='en', dest='vi')
                text = re.sub(r'\s+', ' ', translation.text).strip()
                bot.send_message(message.chat.id, 
                                 "📝 Đoạn văn được tôi ' phiên dịch ' như sau :\n"
                                 f"`{text}`\n"
                                 "", parse_mode="Markdown")
            else:
                bot.reply_to(message, "⚠️ Chúng tôi chưa hỗ trợ ngôn ngữ này.")
        else:
            bot.reply_to(message, "⚠️ Không thể xác định ngôn ngữ.")
    except Exception as e:
        print(e)
        bot.reply_to(message, "⚠️ Đã xảy ra lỗi trong quá trình dịch.")
@bot.message_handler(commands=['news'])    
def return_news(message):
    data = get_news()
    for article in data:
        bot.send_message(message.chat.id, f"📝 Tin tức mới nhất cập nhập từ vnexpress :\n"
                         f"{article['title']}\n"
                         f"{article['link']}\n")
        if 'image_link' in article:
            bot.send_photo(message.chat.id, article['image_link'])
def text_to_audio(text, output_file):
    engine = pyttsx3.init()
    engine.save_to_file(text, output_file)
    engine.runAndWait()
@bot.message_handler(commands=['voice'])
def handle_message(message):
    bot.send_message(message.chat.id, "♻ Loading...")

    text = ' '.join(message.text.split()[1:])
    output_file = f"{message.chat.id}.mp3"

    text_to_audio(text, output_file)

    with open(output_file, 'rb') as audio:
        bot.send_audio(message.chat.id, audio)
    os.remove(output_file)

def menu(message):
    items = [
        '📸  Hình ảnh',
        '🌐  Ngôn ngữ',
        '📥  Tin tức mới nhất',
        '📨  Bot nhóm chat',
        '📈  Bot giao dịch',
        '📲  Liên hệ quản trị viên',
        '📮  Thông báo'
    ]
    markup = types.ReplyKeyboardMarkup(row_width=2)
    buttons = [types.KeyboardButton(item) for item in items]
    markup.add(*buttons)
    current_hour = datetime.now().hour
    daytime = "sáng" if 6 <= current_hour < 12 else "chiều" if 12 <= current_hour < 18 else "tối"
    bot.send_message(message.chat.id, f"🎉 Chào buổi {daytime} {message.from_user.first_name} {message.from_user.last_name}, tôi có thể giúp gì cho bạn ?",
                     reply_markup=markup)
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if message.text == '📸  Hình ảnh':
        markup = types.InlineKeyboardMarkup(row_width=1)
        item1 = types.InlineKeyboardButton("👀 Lọc chữ từ ảnh", callback_data='imgtext')
        item2 = types.InlineKeyboardButton("👀 Quét QRCODE", callback_data='qr')

        markup.add(item1, item2)
        bot.send_message(message.chat.id,"🙈 Hãy gửi cho tôi một bức ảnh, tôi có thể giúp bạn :\n"
                                        "✅ Lọc chữ từ ảnh\n"
                                        "✅ Quét QRCode",reply_markup=markup)
    elif message.text == '🌐  Ngôn ngữ':
        markup = types.InlineKeyboardMarkup(row_width=1)
        item1 = types.InlineKeyboardButton("📝 Tiếng Việt -English", callback_data='transT')
        item2 = types.InlineKeyboardButton("📝 Chuyển văn bản thành giọng nói", callback_data='transV')

        markup.add(item1, item2)
        bot.send_message(message.chat.id,"🙈 Hãy gửi cho tôi một đoạn văn, tôi có thể giúp bạn :\n"
                                        "✅ Dịch ngôn ngữ\n"
                                        "✅ Chuyển văn bản thành giọng nói\n"
                                        "♻ Tính năng đang phát triển", reply_markup=markup)
    elif message.text == '📨  Bot nhóm chat':
        markup = types.InlineKeyboardMarkup(row_width=1)
        item1 = types.InlineKeyboardButton("👀 Control Telegram Group", callback_data='botT')
        item2 = types.InlineKeyboardButton("👀 Control Messenger Group", callback_data='botM')
        markup.add(item1, item2)
        bot.send_message(message.chat.id,"🙈 Ú òa , tôi có thể giúp bạn quản lí nhóm , lưu ý :\n"
                                        "📨 Add tôi vào nhóm , nhớ là cấp quyền phó nhóm...\n"
                                        "📨 Chọn đúng loại nhóm chat nhé !!!!!\n"
                                        "📨 Hãy lưu lại danh sách lệnh để quản lí nhóm !\n",reply_markup=markup)
    elif message.text == '📥  Tin tức mới nhất':
        markup = types.InlineKeyboardMarkup(row_width=1)
        item1 = types.InlineKeyboardButton("Đọc tin mới nhất từ vnexpress", callback_data='newsT')
        item2 = types.InlineKeyboardButton("Xem Kết Quả Sổ Xố", callback_data='newsX')
        markup.add(item1, item2)
        bot.send_message(message.chat.id,"🙈 Cập nhập tin tức cùng tôi nào :\n",reply_markup=markup)
    elif message.text == '📮  Thông báo':
        bot.send_message(message.chat.id, "🎊 Bạn không có thông báo nào .🎊")
    elif message.text == '📈  Bot giao dịch':
        bot.send_message(message.chat.id, "🎊 Chưa có bot nào được thành lập🎊")
    elif message.text == '📲  Liên hệ quản trị viên':
        bot.send_message(message.chat.id,"👀 Hiện tại không có quản trị viên nào online.\n🌺 Thanks! 🌺")
    else:
        user_input = (message.text).lower()
        encoded_text = encode_ascii(user_input)
        response = None
        found_answer = False  
        for qa_pair in database["questions"]:
            question_text = qa_pair["question"].lower()
            encoded_question = encode_ascii(question_text)
            similarity_score = cosine_similarity(encoded_text, encoded_question)
            print(similarity_score)
            if user_input in question_text and similarity_score >= 0.9:
                response = qa_pair["answer"]
                found_answer = True
                break
        if found_answer:
            bot.send_message(message.chat.id, response)
        else:
            markup = types.InlineKeyboardMarkup(row_width=1)
            bot.send_message(message.chat.id, 
                            "👀 Xin lỗi tôi chưa được dạy về câu hỏi này\n"
                            "👀 Hãy cho tôi biết đáp án.\n"
                            "👀 Ghi 'skip' để bỏ qua.")
            bot.register_next_step_handler(message, save_new_answer, user_input)
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    if call.data == "button_ready":
        menu(call.message)
    elif call.data == "imgtext":
        bot.send_message(call.message.chat.id, "👀 Hãy gửi cho tôi bức ảnh kèm caption /imgtext")
    elif call.data == "transT":
        bot.send_message(call.message.chat.id, "♻ Hãy gửi văn bản kèm theo cú pháp /trans.")
    elif call.data == "transV":
        bot.send_message(call.message.chat.id, "♻ Send text with /voice syntax.")
    elif call.data == "botT":
        bot.send_message(call.message.chat.id,"♻ Được , tôi có thể giúp bạn quản lí nhóm TELEGRAM.\n"
                                            "♻ Truy cập vào bot @Heartsteel_Group_bot để bắt sử dụng.")
    elif call.data == "botM":
        bot.send_message(call.message.chat.id,"⚠️ Chúng tôi đang phát triển chức năng này.")
    elif call.data == "newsT":
        return_news(call.message)
    elif call.data == "qr":
        bot.send_message(call.message.chat.id, "👀 Hãy gửi cho tôi bức ảnh kèm caption /qr")
bot.polling()
