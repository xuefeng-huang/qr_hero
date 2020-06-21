from telegram.ext import Updater, Filters, MessageHandler, CommandHandler
from telegram.ext.dispatcher import run_async
import cv2
import os
import uuid
import logging
import traceback
import html
import sys

TOKEN = os.getenv('BOT_TOKEN', None)
if not TOKEN:
    sys.exit('please set your BOT_TOKEN env variable')

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
    update.message.reply_html(f'''Hi there, send me some QR code photos and I will tell you what they mean
file any issue or feedback? -> <a href="https://github.com/xuefeng-huang/qr_hero">something is not right</a>''')

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
        detector = cv2.QRCodeDetector()
        data, _, _ = detector.detectAndDecode(img)
        update.message.reply_text(data)
    except Exception as e:
        update.message.reply_text("Oops, I can't see a QR code there, someone get my glasses?!")
        logger.error(msg="Exception while handling an update:", exc_info=str(e))

    os.remove(tf)

def text_handler(update, context):
    update.message.reply_text("I'll pretend I understand what you mean, but you know what, a picture is more than "
                                "thousand words 😎")

def main():
    updater = Updater(TOKEN, use_context=True, workers=4) # worker defaults to 4
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(MessageHandler(Filters.photo, decode))
    dp.add_handler(MessageHandler(Filters.text & (~Filters.command), text_handler))
    dp.add_error_handler(error_handler)
    
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()