import os
import sys
import asyncio
import aiohttp
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait, Timeout

# Configuration (Use environment variables in production)
API_ID = 22696222
API_HASH = "1b4cdb255f37262200981dbbf87a1fa0"
BOT_TOKEN = "7897731857:AAG6GtiqGXlxn3NPVwlSJL713wlTFSnIwW8"
MAX_FILE_SIZE = 2000 * 1024 * 1024  # 2GB (Telegram's max file size)

bot = Client(
    "bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

async def run_command(command):
    """Execute shell commands asynchronously"""
    process = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    return stdout.decode(), stderr.decode(), process.returncode

async def download_hls(url: str, output_name: str, chat_id: int):
    """Download HLS stream with proper headers and parameters"""
    cmd = [
        'yt-dlp',
        '-o', f'"{output_name}"',
        '--hls-use-mpegts',
        '--no-check-certificate',
        '--referer', 'https://vz-b84dcfa8-0db.b-cdn.net/',
        '--add-header', 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        '--concurrent-fragments', '4',
        '--buffer-size', '16K',
        f'"{url}"'
    ]
    return await run_command(' '.join(cmd))

async def safe_delete(file_path: str):
    """Safely delete files with error handling"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        print(f"Error deleting file {file_path}: {e}")

@bot.on_message(filters.command(["start"]))
async def start(bot: Client, m: Message):
    await m.reply_text(
        f"<b>Hello {m.from_user.mention} 👋\n\n"
        "I can download videos (including HLS streams) and PDFs from URLs!\n\n"
        "Use /upload to begin\n"
        "Max file size: 2GB</b>"
    )

@bot.on_message(filters.command("stop"))
async def stop_handler(_, m: Message):
    await m.reply_text("🚦 Operation Stopped")
    os.execl(sys.executable, sys.executable, *sys.argv)

@bot.on_message(filters.command(["upload"]))
async def upload_handler(bot: Client, m: Message):
    try:
        # Get video URL
        video_msg = await bot.ask(
            chat_id=m.chat.id,
            text="📥 Send video URL (HLS/M3U8 supported) or /skip",
            timeout=300
        )
        video_url = None if video_msg.text.lower() == "/skip" else video_msg.text
        await video_msg.delete()

        # Get PDF URL
        pdf_msg = await bot.ask(
            chat_id=m.chat.id,
            text="📄 Send PDF URL or /skip",
            timeout=300
        )
        pdf_url = None if pdf_msg.text.lower() == "/skip" else pdf_msg.text
        await pdf_msg.delete()

        # Get batch name
        batch_msg = await bot.ask(
            chat_id=m.chat.id,
            text="🏷️ Send batch name (e.g., Batch-1)",
            timeout=300
        )
        batch_name = batch_msg.text.strip().replace(" ", "_")
        await batch_msg.delete()

        # Validate input
        if not (video_url or pdf_url):
            await m.reply_text("❌ Please provide at least one URL!")
            return

        # Process Video
        if video_url:
            video_name = f"{batch_name}_video.mp4"
            msg = await m.reply_text(f"⏬ Downloading video...\nURL: {video_url[:50]}...")

            # Download using yt-dlp with HLS support
            stdout, stderr, returncode = await download_hls(video_url, video_name, m.chat.id)
            
            if returncode != 0 or not os.path.exists(video_name):
                await msg.edit_text(f"❌ Video download failed!\nError: {stderr[:300]}")
                await safe_delete(video_name)
                return

            file_size = os.path.getsize(video_name)
            if file_size > MAX_FILE_SIZE:
                await msg.edit_text(f"❌ File too large ({file_size//1024//1024}MB > 2000MB)")
                await safe_delete(video_name)
                return

            await msg.edit_text("📤 Uploading video...")
            await bot.send_video(
                chat_id=m.chat.id,
                video=video_name,
                caption=f"🎥 {batch_name}",
                supports_streaming=True,
                progress=lambda c, t: asyncio.create_task(
                    msg.edit_text(f"📤 Uploading video... {c*100/t:.1f}%")
                )
            )
            await safe_delete(video_name)

        # Process PDF
        if pdf_url:
            pdf_name = f"{batch_name}.pdf"
            msg = await m.reply_text(f"⏬ Downloading PDF...\nURL: {pdf_url[:50]}...")
            
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(pdf_url) as response:
                        if response.status == 200:
                            with open(pdf_name, "wb") as f:
                                async for chunk in response.content.iter_chunked(1024*1024):
                                    f.write(chunk)
                        else:
                            raise Exception(f"HTTP Error {response.status}")
            except Exception as e:
                await msg.edit_text(f"❌ PDF download failed!\nError: {str(e)}")
                await safe_delete(pdf_name)
                return

            await msg.edit_text("📤 Uploading PDF...")
            await bot.send_document(
                chat_id=m.chat.id,
                document=pdf_name,
                caption=f"📄 {batch_name}",
                progress=lambda c, t: asyncio.create_task(
                    msg.edit_text(f"📤 Uploading PDF... {c*100/t:.1f}%")
                )
            )
            await safe_delete(pdf_name)

        await m.reply_text("✅ All files processed successfully! 🚀")

    except Timeout:
        await m.reply_text("⌛ Operation timed out after 5 minutes")
    except Exception as e:
        await m.reply_text(f"❌ Critical error: {str(e)}")
    finally:
        await safe_delete(video_name)
        await safe_delete(pdf_name)

if __name__ == "__main__":
    print("⚡ Bot Started!")
    bot.run()
