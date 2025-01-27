# Don't Remove Credit Tg - @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/@Tech_VJ
# Ask Doubt on telegram @KingVJ01

import os
import re
import sys
import json
import time
import asyncio
import requests
import subprocess

import core as helper
from utils import progress_bar
from vars import API_ID, API_HASH, BOT_TOKEN
from aiohttp import ClientSession
from pyromod import listen
from subprocess import getstatusoutput

from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait
from pyrogram.errors.exceptions.bad_request_400 import StickerEmojiInvalid
from pyrogram.types.messages_and_media import message
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup


bot = Client(
    "bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN)


@bot.on_message(filters.command(["start"]))
async def start(bot: Client, m: Message):
    await m.reply_text(f"<b>Hello {m.from_user.mention} 👋\n\n I Am A Bot For Download Links From Your **.TXT** File And Then Upload That File On Telegram So Basically If You Want To Use Me First Send Me /upload Command And Then Follow Few Steps..\n\nUse /stop to stop any ongoing task.</b>")


@bot.on_message(filters.command("stop"))
async def restart_handler(_, m):
    await m.reply_text("**Stopped**🚦", True)
    os.execl(sys.executable, sys.executable, *sys.argv)



@bot.on_message(filters.command(["upload"]))
async def upload(bot: Client, m: Message):
    editable = await m.reply_text("Send the JSON file ⚡️")
    input: Message = await bot.listen(editable.chat.id)
    file_path = await input.download()
    await input.delete(True)

    try:
        # Load JSON data
        with open(file_path, 'r') as file:
            data = json.load(file)

        # Extract videos and PDFs
        video_items = data.get('data', [])[0].get('videos', [])
        if not video_items:
            await m.reply_text("No videos or PDFs found in the file.")
            return

        links = [{"video": item.get("videoUrl"), "pdf": item.get("pdfUrl")} for item in video_items]

        await editable.edit(f"Found {len(links)} items. Please send your batch name.")
        batch_msg: Message = await bot.listen(editable.chat.id)
        batch_name = batch_msg.text
        await batch_msg.delete()

        for idx, item in enumerate(links, start=1):
            video_url = item.get("video")
            pdf_url = item.get("pdf")
            name = f"Item-{idx}"

            try:
                # Process video
                if video_url:
                    await m.reply_text(f"Processing Video {idx}: {video_url}")
                    cmd = f'yt-dlp -o "{name}.mp4" "{video_url}"'
                    os.system(cmd)  # Replace with actual video downloading logic
                    await bot.send_video(chat_id=m.chat.id, video=f"{name}.mp4", caption=f"Batch: {batch_name}")

                # Process PDF
                if pdf_url:
                    await m.reply_text(f"Processing PDF {idx}: {pdf_url}")
                    await bot.send_document(chat_id=m.chat.id, document=pdf_url, caption=f"Batch: {batch_name}")

            except Exception as e:
                await m.reply_text(f"Error processing {name}: {str(e)}")
                continue

        await editable.edit("**Done processing all items. 🚀**")

    except Exception as e:
        await m.reply_text(f"Error: {str(e)}")
    finally:
        os.remove(file_path)


   

bot.run()
