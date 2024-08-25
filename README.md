# YouTube Video Downloader Telegram Bot

This is a Telegram bot that allows users to download YouTube videos by simply sending the bot a link. The bot can handle multiple links, download the videos, and send them back to the user. It also manages large video files by splitting them into chunks before sending them.

## Features

- **Download YouTube Videos:** Send a YouTube link to the bot, and it will download the video for you.
- **Supports Multiple Links:** Send multiple YouTube links in a single message, and the bot will process each one.
- **Handles Large Files:** Automatically splits large video files into chunks to ensure they can be sent via Telegram.
- **Thumbnail Preview:** The bot sends a thumbnail of the downloaded video.
- **Error Handling:** Provides feedback in case of errors during the download process.

## Installation

1. **Clone the repository:**

    ```bash
    git clone https://github.com/abelzk/Youtube-Video-Downloader-Telegram-Bot.git
    cd youtube-video-downloader-telegram-bot
    ```

2. **Install the required dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

3. **Set up your Telegram bot token:**

    Replace `"YOUR API KEY"` in the code with your actual Telegram bot token.

4. **Run the bot:**

    ```bash
    python bot.py
    ```

## Usage

- **Start the bot:**
  - Use the `/start` command to begin interacting with the bot.
  
- **Download a video:**
  - Simply send a YouTube link or multiple links separated by spaces.
  
- **Upload any remaining files:**
  - Use the `/upload` command to upload any files that might still be in the `downloads` directory.

## Dependencies

- `python-telegram-bot`
- `yt-dlp`
- `moviepy`

Ensure you have these dependencies installed by using the `requirements.txt`.

## Contributing

Feel free to submit issues or pull requests if you find any bugs or have new features to propose.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
