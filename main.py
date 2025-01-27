import os
import sys
import asyncio
import aiohttp
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait, Timeout

# API credentials (consider using environment variables in production)
API_ID = 22696222
API_HASH = "1b4cdb255f37262200981dbbf87a1fa0"
BOT_TOKEN = "7897731857:AAG6GtiqGXlxn3NPVwlSJL713wlTFSnIwW8"

bot = Client(
    "bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

async def run_command(command):
    process = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    return stdout.decode(), stderr.decode()

@bot.on_message(filters.command(["start"]))
async def start(bot: Client, m: Message):
    await m.reply_text(
        f"<b>Hello {m.from_user.mention} 👋\n\n"
        "I am a bot that can download videos and PDFs from URLs and upload them to Telegram.\n\n"
        "Use /upload to start the process\n"
        "Use /stop to cancel any ongoing task</b>"
    )

@bot.on_message(filters.command("stop"))
async def stop_handler(_, m: Message):
    await m.reply_text("**Operation Stopped** 🚦")
    os.execl(sys.executable, sys.executable, *sys.argv)

@bot.on_message(filters.command(["upload"]))
async def upload(bot: Client, m: Message):
    try:
        # Get video URL
        video_msg = await bot.ask(
            chat_id=m.chat.id,
            text="Please send the video URL 🎥 (or /skip to skip video)",
            timeout=300
        )
        if video_msg.text.lower() == "/skip":
            video_url = None
        else:
            video_url = video_msg.text
        await video_msg.delete()

        # Get PDF URL
        pdf_msg = await bot.ask(
            chat_id=m.chat.id,
            text="Please send the PDF URL 📄 (or /skip to skip PDF)",
            timeout=300
        )
        if pdf_msg.text.lower() == "/skip":
            pdf_url = None
        else:
            pdf_url = pdf_msg.text
        await pdf_msg.delete()

        # Get batch name
        batch_msg = await bot.ask(
            chat_id=m.chat.id,
            text="Please send a name for this batch (e.g., Batch-1)",
            timeout=300
        )
        batch_name = batch_msg.text
        await batch_msg.delete()

        # Process Video
        if video_url:
            msg = await m.reply_text(f"⏬ Downloading video from: {video_url}")
            video_name = f"{batch_name}_video.mp4"
            
            # Use yt-dlp with async subprocess
            cmd = f'yt-dlp -o "{video_name}" "{video_url}"'
            stdout, stderr = await run_command(cmd)
            
            if not os.path.exists(video_name):
                await msg.edit_text("❌ Video download failed!")
                return

            await msg.edit_text("📤 Uploading video to Telegram...")
            await bot.send_video(
                chat_id=m.chat.id,
                video=video_name,
                caption=f"🎥 {batch_name} Video",
                progress=lambda current, total: print(f"Uploaded {current * 100 / total:.1f}%")
            )
            os.remove(video_name)

        # Process PDF
        if pdf_url:
            msg = await m.reply_text(f"⏬ Downloading PDF from: {pdf_url}")
            pdf_name = f"{batch_name}_pdf.pdf"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(pdf_url) as response:
                    if response.status == 200:
                        with open(pdf_name, "wb") as f:
                            f.write(await response.read())
                    else:
                        await msg.edit_text("❌ PDF download failed!")
                        return

            await msg.edit_text("📤 Uploading PDF to Telegram...")
            await bot.send_document(
                chat_id=m.chat.id,
                document=pdf_name,
                caption=f"📄 {batch_name} PDF",
                progress=lambda current, total: print(f"Uploaded {current * 100 / total:.1f}%")
            )
            os.remove(pdf_name)

        await m.reply_text("✅ All files processed successfully! 🚀")

    except Timeout:
        await m.reply_text("⌛ Operation timed out. Please try again.")
    except Exception as e:
        await m.reply_text(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    print("Bot started...")
    bot.run()
