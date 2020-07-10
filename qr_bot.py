from telegram.ext import Updater, Filters, MessageHandler, CommandHandler
from telegram.ext.dispatcher import run_async
from pyzbar import pyzbar
import cv2
import os
import uuid
import logging
import traceback
import html
import sys

PORT = int(os.getenv('PORT', 88))
SERVER_IP = os.getenv('SERVER_IP', None)
TOKEN = os.getenv('BOT_TOKEN', None)
if not TOKEN or not SERVER_IP:
    sys.exit('please set your BOT_TOKEN and SERVER_IP env variable')

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

def error_handler(update, context):
    """Log the error and send a telegram message to notify the developer."""
    # Log the error before we do anything else, so we can see it even if something breaks.
    logger.error(msg="Exception while handling an update:", exc_info=context.error)

    # traceback.format_exception returns the usual python message about an exception, but as a
    # list of strings rather than a single string, so we have to join them together.
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb = ''.join(tb_list)

    # Build the message with some markup and additional information about what happened.
    # You might need to add some logic to deal with messages longer than the 4096 character limit.
    message = (
        'An exception was raised while handling an update\n'
        '<pre>update = {}</pre>\n\n'
        '<pre>context.chat_data = {}</pre>\n\n'
        '<pre>context.user_data = {}</pre>\n\n'
        '<pre>{}</pre>'
    ).format(
        html.escape(json.dumps(update.to_dict(), indent=2, ensure_ascii=False)),
        html.escape(str(context.chat_data)),
        html.escape(str(context.user_data)),
        html.escape(tb)
    )
    # todo send error to me via telegram
    logger.error(msg="Detail error:", exc_info=message)

def start(update, context):
    update.message.reply_html(f'''Hi {update.effective_user.first_name}, any QR photos at hand?
file any issue or feedback? -> <a href="https://github.com/xuefeng-huang/qr_hero">something is not right</a>
/supportme if you find it useful and wanna treat me a coffee☕️''')

@run_async
def decode(update, context):
    if update.message.photo:
        id_img = update.message.photo[-1].file_id
    else:
        return

    bot = context.bot
    photo = bot.getFile(id_img)
    # generate tmp file name for each user
    tf = str(uuid.uuid4())
    photo.download(tf)

    # decode using opencv
    try:
        img = cv2.imread(tf)
        codes = pyzbar.decode(img)
        # logger.info(codes[0].data.decode('utf8'))
        for code in codes:
            update.message.reply_text(code.data.decode('utf8'))
    except Exception as e:
        update.message.reply_text("Oops, I can't see a QR code there, someone get my glasses?!")
        logger.error(msg="Exception while handling an update:", exc_info=str(e))

    os.remove(tf)

def text_handler(update, context):
    update.message.reply_text("I'll pretend I understand what you mean, but you know what, a picture is more than "
                                "thousand words 😎")

def supportme_handler(update, context):
    update.message.reply_html('''Thanks you, I know you enjoy coffee as well.
<a href="https://www.paypal.me/coffeeforxuefeng">here's paypalme link</a>''')

def main():
    updater = Updater(TOKEN, use_context=True, workers=4) # worker defaults to 4
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('supportme', supportme_handler))
    dp.add_handler(MessageHandler(Filters.photo, decode))
    dp.add_handler(MessageHandler(Filters.text & (~Filters.command), text_handler))
    dp.add_error_handler(error_handler)
    
    updater.start_webhook(listen='0.0.0.0',
                      port=PORT,
                      url_path=TOKEN,
                      key='private.key',
                      cert='cert.pem',
                      webhook_url=f'https://{SERVER_IP}:{PORT}/{TOKEN}')
    updater.idle()

if __name__ == '__main__':
    main()