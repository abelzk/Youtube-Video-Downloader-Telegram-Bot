import logging
import os
import yt_dlp
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import time
import zipfile
import math

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

#TOKEN = "7449252023:AAGl88ZXaJD6Gu1M49zmnZNUvddsgIZZ0C0"
TOKEN = "7322646122:AAFsMtnbFX2eSPfLtTTwIl2314biPQkTrKw"
if not TOKEN:
    raise ValueError("No TELEGRAM_BOT_TOKEN found in environment variables")

bot_username = "ethioytdownloaderbot"

MAX_CHUNK_SIZE = 49 * 1024 * 1024  # Slightly less than 50MB to avoid boundary issues

async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Send me a YouTube link or a list of links separated by spaces, and I will download the videos for you!')

def progress_hook(d, status_message, context):
    if d['status'] == 'downloading':
        total_bytes = d.get('total_bytes', 0)
        downloaded_bytes = d.get('downloaded_bytes', 0)
        percentage = (downloaded_bytes / total_bytes) * 100 if total_bytes > 0 else 0
        message = f"Downloading video... {percentage:.2f}%"
        context.bot.edit_message_text(chat_id=status_message.chat_id, message_id=status_message.message_id, text=message)

async def send_file(update, context, file_path, caption):
    file_size = os.path.getsize(file_path)
    if file_size > MAX_CHUNK_SIZE:
        await send_large_file(update, context, file_path, caption)
    else:
        await context.bot.send_document(
            chat_id=update.effective_chat.id,
            document=open(file_path, 'rb'),
            caption=caption,
            reply_to_message_id=update.message.message_id
        )
        os.remove(file_path)  # Delete the file after sending
        logger.info(f"Successfully sent and removed file: {file_path}")

async def send_large_file(update, context, file_path, caption):
    file_size = os.path.getsize(file_path)
    num_chunks = math.ceil(file_size / MAX_CHUNK_SIZE)

    with open(file_path, 'rb') as f:
        for i in range(num_chunks):
            chunk_data = f.read(MAX_CHUNK_SIZE)
            chunk_path = f"{file_path}.part{i+1}"
            with open(chunk_path, 'wb') as chunk_file:
                chunk_file.write(chunk_data)
            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=open(chunk_path, 'rb'),
                caption=f"{caption} (part {i+1}/{num_chunks})",
                reply_to_message_id=update.message.message_id
            )
            os.remove(chunk_path)  # Delete the chunk after sending

    os.remove(file_path)  # Delete the original file after sending

async def download_youtube_video(update: Update, context: CallbackContext) -> None:
    urls = update.message.text.split()
    valid_urls = [url for url in urls if "youtube.com" in url or "youtu.be" in url]

    if not valid_urls:
        await update.message.reply_text('Please send valid YouTube links.')
        return

    status_message = await context.bot.send_message(chat_id=update.effective_chat.id, text="Processing your request...")

    for url in valid_urls:
        try:
            ydl_opts = {
                'format': 'best',
                'progress_hooks': [lambda d: progress_hook(d, status_message, context)],
                'outtmpl': 'downloads/%(title)s.%(ext)s',
            }

            os.makedirs('downloads', exist_ok=True)

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=True)
                file_path = ydl.prepare_filename(info_dict)
                thumbnail_url = info_dict.get('thumbnail', '')
                description = info_dict.get('description', 'No description available')
                title = info_dict.get('title', 'Unknown Title')
                artist = info_dict.get('uploader', 'Unknown Artist')

            caption = f"Downloaded by @{bot_username}\nTitle: {title}\nArtist: {artist}\n\nDescription: {description}"
            if len(caption) > 1024:
                caption = caption[:1020] + "..."

            await send_file(update, context, file_path, caption)

            if thumbnail_url:
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=thumbnail_url,
                    caption=f"Thumbnail for {title}"
                )

        except Exception as e:
            logger.error(f"Error: {e}")
            await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=status_message.message_id, text=f'Failed to download the YouTube video: {url}. Please make sure the link is correct.')

    await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=status_message.message_id)

async def upload_remaining_files(update: Update, context: CallbackContext) -> None:
    download_dir = 'downloads'
    if os.path.exists(download_dir) and os.listdir(download_dir):
        for root, _, files in os.walk(download_dir):
            for file in files:
                file_path = os.path.join(root, file)
                await send_file(update, context, file_path, "Here is your downloaded file.")
    else:
        await update.message.reply_text('No files found in the downloads directory.')

async def error_handler(update: Update, context: CallbackContext) -> None:
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    if update and update.message:
        await update.message.reply_text('An error occurred. Please try again later.')

def main() -> None:
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_youtube_video))
    application.add_handler(CommandHandler("upload", upload_remaining_files))
    application.add_error_handler(error_handler)

    application.run_polling()

if __name__ == '__main__':
    main()
