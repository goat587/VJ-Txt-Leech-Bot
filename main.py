import os
import sys
import json
import asyncio
import requests
import subprocess

from aiohttp import ClientSession
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.errors import FloodWait
from pyrogram.errors.exceptions.bad_request_400 import StickerEmojiInvalid

# Replace these with your actual API credentials
API_ID = 22696222
API_HASH = "1b4cdb255f37262200981dbbf87a1fa0"
BOT_TOKEN = "7897731857:AAG6GtiqGXlxn3NPVwlSJL713wlTFSnIwW8"

bot = Client(
    "bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

@bot.on_message(filters.command(["start"]))
async def start(bot: Client, m: Message):
    await m.reply_text(
        f"<b>Hello {m.from_user.mention} 👋\n\n"
        "I am a bot that can download videos and PDFs from the URLs you provide and upload them to Telegram.\n\n"
        "To use me, send the /upload command and follow the instructions.\n\n"
        "Use /stop to stop any ongoing task.</b>"
    )

@bot.on_message(filters.command("stop"))
async def stop_handler(_, m: Message):
    await m.reply_text("**Stopped**🚦", True)
    os.execl(sys.executable, sys.executable, *sys.argv)

@bot.on_message(filters.command(["upload"]))
async def upload(bot: Client, m: Message):
    editable = await m.reply_text("Please send the video URL 🎥")
    video_msg: Message = await bot.listen(m.chat.id)
    video_url = video_msg.text
    await video_msg.delete()

    editable = await m.reply_text("Please send the PDF URL 📄")
    pdf_msg: Message = await bot.listen(m.chat.id)
    pdf_url = pdf_msg.text
    await pdf_msg.delete()

    editable = await m.reply_text("Please send a name for this batch (e.g., Batch-1)")
    batch_msg: Message = await bot.listen(m.chat.id)
    batch_name = batch_msg.text
    await batch_msg.delete()

    try:
        # Process Video
        if video_url:
            await m.reply_text(f"Downloading video from: {video_url}")
            video_name = f"{batch_name}_video.mp4"
            cmd = f'yt-dlp -o "{video_name}" "{video_url}"'
            os.system(cmd)  # Download the video using yt-dlp
            await m.reply_text("Video downloaded. Uploading to Telegram...")
            await bot.send_video(chat_id=m.chat.id, video=video_name, caption=f"Batch: {batch_name}")
            os.remove(video_name)  # Clean up the downloaded file

        # Process PDF
        if pdf_url:
            await m.reply_text(f"Downloading PDF from: {pdf_url}")
            pdf_name = f"{batch_name}_pdf.pdf"
            response = requests.get(pdf_url)
            with open(pdf_name, "wb") as pdf_file:
                pdf_file.write(response.content)
            await m.reply_text("PDF downloaded. Uploading to Telegram...")
            await bot.send_document(chat_id=m.chat.id, document=pdf_name, caption=f"Batch: {batch_name}")
            os.remove(pdf_name)  # Clean up the downloaded file

        await m.reply_text("**All files processed successfully! 🚀**")

    except Exception as e:
        await m.reply_text(f"Error: {str(e)}")

bot.run()
