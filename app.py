# app.py
import os, requests, csv, io
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, FlexSendMessage, BubbleContainer, BoxComponent, TextComponent, ButtonComponent, URIAction, SeparatorComponent
from cachetools import cached, TTLCache
from ai_engine import get_ai_response

app = Flask(__name__)

YOUR_CHANNEL_ACCESS_TOKEN = os.environ.get('YOUR_CHANNEL_ACCESS_TOKEN')
YOUR_CHANNEL_SECRET = os.environ.get('YOUR_CHANNEL_SECRET')

line_bot_api = LineBotApi(YOUR_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(YOUR_CHANNEL_SECRET)

CSV_URLS = {
    "ระเบียบ": "https://docs.google.com/spreadsheets/d/e/2PACX-1vSiImbpXO65-_Xlhlz4ORNZ2s7A89GFMnEGVzlngCe8TfJcvckmUmH8VExtvKX1qiYBvzPlnSdB3OLn/pub?gid=0&single=true&output=csv",
    "คู่มือ": "https://docs.google.com/spreadsheets/d/e/2PACX-1vSiImbpXO65-_Xlhlz4ORNZ2s7A89GFMnEGVzlngCe8TfJcvckmUmH8VExtvKX1qiYBvzPlnSdB3OLn/pub?gid=968513651&single=true&output=csv",
    "โบรชัวร์": "https://docs.google.com/spreadsheets/d/e/2PACX-1vSiImbpXO65-_Xlhlz4ORNZ2s7A89GFMnEGVzlngCe8TfJcvckmUmH8VExtvKX1qiYBvzPlnSdB3OLn/pub?gid=1584049231&single=true&output=csv"
}
VALID_CATEGORIES = list(CSV_URLS.keys())
cache = TTLCache(maxsize=10, ttl=600)

@cached(cache)
def get_sheet_data(category_name):
    url = CSV_URLS.get(category_name)
    response = requests.get(url)
    response.raise_for_status()
    csv_data = response.content.decode('utf-8')
    return list(csv.DictReader(io.StringIO(csv_data)))

def create_clean_document_bubble(records, category_name):
    new_header_component = BoxComponent(layout='vertical', paddingAll='12px', contents=[TextComponent(text=f"รายการเอกสาร: {category_name}", weight='bold', size='xl', color='#111111')])
    body_contents = []
    for record in records:
        if record.get('ชื่อเอกสาร') and record.get('ลิงก์ Google Drive'):
            row = BoxComponent(layout='vertical', paddingAll='12px', spacing='sm', contents=[TextComponent(text=record.get('ชื่อเอกสาร'), wrap=True, weight='bold', size='md', color='#333333'), ButtonComponent(action=URIAction(label='เปิดเอกสาร', uri=record.get('ลิงก์ Google Drive')), style='primary', height='sm', margin='sm', color='#5D3A8E')])
            body_contents.append(row)
            body_contents.append(SeparatorComponent())
    if body_contents: body_contents.pop()
    bubble = BubbleContainer(body=BoxComponent(layout='vertical', contents=[new_header_component] + body_contents, paddingAll='0px'))
    return FlexSendMessage(alt_text=f"รายการเอกสารในหมวด {category_name}", contents=bubble)

user_states = {}

@app.route("/webhook", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    handler.handle(body, signature)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text.strip()
    user_id = event.source.user_id

    if text == 'AI Agent':
        user_states[user_id] = 'AI_MODE'
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="AI พร้อมใช้งาน สามารถพูดคุยได้เลย (หากต้องการออกจากโหมดนี้ พิมพ์ 'ออก')"))
    elif text.lower() in ['ออก', 'exit'] and user_states.get(user_id) == 'AI_MODE':
        user_states.pop(user_id, None)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="ออกจากโหมด AI เรียบร้อยแล้ว"))
    elif user_states.get(user_id) == 'AI_MODE':
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="กำลังค้นหาข้อมูลจากเอกสาร โปรดรอสักครู่..."))
        ai_answer = get_ai_response(text)
        line_bot_api.push_message(user_id, TextSendMessage(text=ai_answer))
    elif text in VALID_CATEGORIES:
        records = get_sheet_data(text)
        reply_message = create_clean_document_bubble(records, text)
        line_bot_api.reply_message(event.reply_token, reply_message)
    else:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="กรุณาเลือกเมนูที่ต้องการ หรือกด 'AI Agent' เพื่อเริ่มการสนทนา"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)