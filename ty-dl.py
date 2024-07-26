import logging
import os
import zipfile
import yt_dlp
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import time

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot token from environment variable
TOKEN = "7449252023:AAGl88ZXaJD6Gu1M49zmnZNUvddsgIZZ0C0"
if not TOKEN:
    raise ValueError("No TELEGRAM_BOT_TOKEN found in environment variables")

bot_username = "ethioytdownloaderbot"

async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Send me a YouTube link or a list of links separated by spaces, and I will download the videos for you!')

def progress_hook(d, status_message, context):
    if d['status'] == 'downloading':
        total_bytes = d.get('total_bytes', 0)
        downloaded_bytes = d.get('downloaded_bytes', 0)
        percentage = (downloaded_bytes / total_bytes) * 100 if total_bytes > 0 else 0
        message = f"Downloading video... {percentage:.2f}%"
        context.bot.edit_message_text(chat_id=status_message.chat_id, message_id=status_message.message_id, text=message)

async def send_file(update, context, file_path, caption, retries=3):
    for attempt in range(retries):
        try:
            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=open(file_path, 'rb'),
                caption=caption,
                reply_to_message_id=update.message.message_id
            )
            os.remove(file_path)  # Delete the file after sending
            logger.info(f"Successfully sent and removed file: {file_path}")
            return
        except Exception as e:
            logger.error(f"Error sending file {file_path} on attempt {attempt + 1}: {e}")
            time.sleep(5)  # Wait before retrying
    await update.message.reply_text(f"Failed to send file {file_path} after {retries} attempts. Please try again later.")

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

def create_zip_archive(download_dir, archive_name='downloads.zip', max_size=10*1024*1024):
    zip_files = []
    current_zip = None
    current_size = 0
    part_num = 1

    for root, _, files in os.walk(download_dir):
        for file in files:
            file_path = os.path.join(root, file)
            file_size = os.path.getsize(file_path)

            if current_zip is None or current_size + file_size > max_size:
                if current_zip is not None:
                    current_zip.close()
                zip_name = f"{archive_name.split('.')[0]}_part{part_num}.zip"
                current_zip = zipfile.ZipFile(zip_name, 'w')
                zip_files.append(zip_name)
                current_size = 0
                part_num += 1

            current_zip.write(file_path, os.path.relpath(file_path, download_dir))
            current_size += file_size
            logger.info(f"Added {file_path} to archive {zip_name}")

    if current_zip is not None:
        current_zip.close()

    return zip_files

async def upload_remaining_files(update: Update, context: CallbackContext) -> None:
    download_dir = 'downloads'
    archive_name = 'downloads.zip'
    
    if os.path.exists(download_dir) and os.listdir(download_dir):
        zip_files = create_zip_archive(download_dir, archive_name)
        for zip_file in zip_files:
            try:
                await send_file(update, context, zip_file, "Here are your downloaded files in a zip archive.")
            except Exception as e:
                logger.error(f"Error sending archive {zip_file}: {e}")
                await update.message.reply_text(f"Failed to send archive {zip_file}. Please try again later.")
        
        # Clean up the downloads directory
        for file_name in os.listdir(download_dir):
            file_path = os.path.join(download_dir, file_name)
            if os.path.isfile(file_path):
                os.remove(file_path)
                logger.info(f"Deleted file {file_path}")
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
