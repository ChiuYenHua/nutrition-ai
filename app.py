from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

import json
import PIL.Image
import configparser
import google.generativeai as genai

# Setup
config = configparser.ConfigParser()
config.read('config.ini')

## Gemini api key
genai.configure(api_key=config.get('google-gemini', 'api_key'))

# Pretty print
def pretty_print_format(text):
    #text = text.replace('•', '  *')
    return text#textwrap.indent(text, '> ', predicate=lambda _: True)

# Gemini model
def img_to_text(path):
    img = PIL.Image.open(path)
    model = genai.GenerativeModel('gemini-pro-vision')

    try:
        response = model.generate_content(["tell me the nutrition label", img], stream=True)
        response.resolve()
        answer = pretty_print_format(response.text)
    except:
        answer = 'model no response!!'
    return answer

# Flask
app = Flask(__name__)

@app.route("/", methods=['POST'])
def linebot():
    body = request.get_data(as_text=True)                    # 取得收到的訊息內容
    try:
        json_data = json.loads(body)                         # json 格式化訊息內容
        access_token = config.get('line-bot', 'channel_access_token')          # 你的 Access Token
        secret = config.get('line-bot','channel_secret')     # 你的 Channel Secret
        line_bot_api = LineBotApi(access_token)              # 確認 token 是否正確
        handler = WebhookHandler(secret)                     # 確認 secret 是否正確
        signature = request.headers['X-Line-Signature']      # 加入回傳的 headers
        handler.handle(body, signature)                      # 綁定訊息回傳的相關資訊
        tk = json_data['events'][0]['replyToken']            # 取得回傳訊息的 Token
        type = json_data['events'][0]['message']['type']     # 取得 LINE 收到的訊息類型
        # 判斷如果是文字
        if type=='text':
            msg = json_data['events'][0]['message']['text']  # 取得 LINE 收到的文字訊息
            reply = '傳給你吃的食物就好誒'
        # 判斷如果是圖片
        elif type == 'image':
            msgID = json_data['events'][0]['message']['id']  # 取得訊息 id
            message_content = line_bot_api.get_message_content(msgID)  # 根據訊息 ID 取得訊息內容
            # 在同樣的資料夾中建立以訊息 ID 為檔名的 .jpg 檔案
            with open(f'gemini_used_image.jpg', 'wb') as fd:
                fd.write(message_content.content)             # 以二進位的方式寫入檔案
            reply = img_to_text('gemini_used_image.jpg')      # 設定要回傳的訊息
        else:
            reply = '你傳的不是文字或圖片呦～'
        print(reply)
        line_bot_api.reply_message(tk,TextSendMessage(reply))  # 回傳訊息
    except:
        print(body)                                            # 如果發生錯誤，印出收到的內容
    return 'OK'                                                # 驗證 Webhook 使用，不能省略

if __name__ == "__main__":
    app.run(port=1125)