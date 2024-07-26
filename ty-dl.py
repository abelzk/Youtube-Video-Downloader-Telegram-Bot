import logging
import os
import yt_dlp
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Your bot token
TOKEN = "7449252023:AAGl88ZXaJD6Gu1M49zmnZNUvddsgIZZ0C0"
bot_username = "yt_musicdlbot"

async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Send me a YouTube link, and I will download the video for you!')

def progress_hook(d, status_message, context):
    if d['status'] == 'downloading':
        total_bytes = d.get('total_bytes', 0)
        downloaded_bytes = d.get('downloaded_bytes', 0)
        percentage = (downloaded_bytes / total_bytes) * 100 if total_bytes > 0 else 0
        message = f"Downloading video... {percentage:.2f}%"
        context.bot.edit_message_text(chat_id=status_message.chat_id, message_id=status_message.message_id, text=message)

async def download_youtube_video(update: Update, context: CallbackContext) -> None:
    url = update.message.text
    if "youtube.com" not in url and "youtu.be" not in url:
        await update.message.reply_text('Please send a valid YouTube link.')
        return
    status_message = await context.bot.send_message(chat_id=update.effective_chat.id, text="Processing your request...")

    try:
        ydl_opts = {
            'format': 'best[ext=mp4]',
            'progress_hooks': [lambda d: progress_hook(d, status_message, context)],
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'writethumbnail': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            video_file = ydl.prepare_filename(info_dict)
            thumbnail_file = f"{os.path.splitext(video_file)[0]}.jpg"

        title = info_dict.get('title', 'Unknown Title')
        uploader = info_dict.get('uploader', 'Unknown Uploader')
        description = info_dict.get('description', 'No Description')
        duration = info_dict.get('duration', 'Unknown Duration')
        view_count = info_dict.get('view_count', 'Unknown Views')
        like_count = info_dict.get('like_count', 'Unknown Likes')

        # Prepare a concise caption
        caption = f"Downloaded by @{bot_username}\nTitle: {title}\nUploader: {uploader}\nDuration: {duration}s\nViews: {view_count}\nLikes: {like_count}\nDescription: {description[:200]}..."  # Limit description length

        file_size = os.path.getsize(video_file)
        file_size_mb = file_size / (1024 * 1024)
        await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=status_message.message_id, text=f"Sending the video... (Size: {file_size_mb:.2f} MB)")

        # Send video
        with open(video_file, 'rb') as vf:
            if len(caption) > 1024:
                # Send the video in parts if the caption is too long
                for i in range(0, len(caption), 1024):
                    await context.bot.send_video(
                        chat_id=update.effective_chat.id,
                        video=vf,
                        caption=caption[i:i+1024],
                        reply_to_message_id=update.message.message_id
                    )
            else:
                await context.bot.send_video(
                    chat_id=update.effective_chat.id,
                    video=vf,
                    caption=caption,
                    reply_to_message_id=update.message.message_id
                )

        # Send thumbnail
        with open(thumbnail_file, 'rb') as tf:
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=tf,
                caption=f"Thumbnail for {title}"
            )

        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=status_message.message_id)
        os.remove(video_file)
        os.remove(thumbnail_file)

    except yt_dlp.utils.DownloadError as e:
        logger.error(f"DownloadError: {e}")
        await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=status_message.message_id, text='Failed to download the YouTube video. This might be due to restrictions on the video.')
    except Exception as e:
        logger.error(f"Error: {e}")
        await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=status_message.message_id, text='Failed to download the YouTube video. Please make sure the link is correct and try again.')

async def error_handler(update: Update, context: CallbackContext) -> None:
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    if update and update.message:
        await update.message.reply_text('An error occurred. Please try again later.')

def main() -> None:
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_youtube_video))
    application.add_error_handler(error_handler)
    application.run_polling()

if __name__ == '__main__':
    main()
