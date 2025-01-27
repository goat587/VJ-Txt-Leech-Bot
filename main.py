import os
import sys
import asyncio
import aiohttp
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait, Timeout

# Configuration - Replace with your actual credentials
API_ID = 22696222
API_HASH = "1b4cdb255f37262200981dbbf87a1fa0"
BOT_TOKEN = "7897731857:AAG6GtiqGXlxn3NPVwlSJL713wlTFSnIwW8"
MAX_FILE_SIZE = 2000 * 1024 * 1024  # 2GB

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

async def download_hls(url: str, output_name: str):
    """Download HLS stream with optimized parameters"""
    cmd = (
        f'yt-dlp -o "{output_name}" '
        f'--hls-use-mpegts --no-check-certificate '
        f'--referer "https://vz-b84dcfa8-0db.b-cdn.net/" '
        f'--add-header "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)" '
        f'--concurrent-fragments 4 --buffer-size 16K "{url}"'
    )
    return await run_command(cmd)

async def safe_delete(file_path: str):
    """Safely delete files with error handling"""
    try:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        print(f"Error deleting file: {e}")

@bot.on_message(filters.command(["start"]))
async def start_handler(client: Client, message: Message):
    await message.reply_text(
        f"<b>Hello {message.from_user.mention} 👋\n\n"
        "I can download videos (including HLS streams) and PDFs!\n\n"
        "Use /upload to begin\n"
        "Max file size: 2GB</b>"
    )

@bot.on_message(filters.command("stop"))
async def stop_handler(client: Client, message: Message):
    await message.reply_text("🚦 Operation Stopped")
    os.execl(sys.executable, sys.executable, *sys.argv)

@bot.on_message(filters.command(["upload"]))
async def upload_handler(client: Client, message: Message):
    video_name = None
    pdf_name = None
    try:
        # Step 1: Get video URL
        prompt = await message.reply_text("📥 Send video URL (HLS/M3U8 supported) or /skip")
        video_msg = await client.listen(chat_id=message.chat.id, filters=filters.text, timeout=300)
        video_url = None if video_msg.text.lower() == "/skip" else video_msg.text.strip()
        await prompt.delete()
        await video_msg.delete()

        # Step 2: Get PDF URL
        prompt = await message.reply_text("📄 Send PDF URL or /skip")
        pdf_msg = await client.listen(chat_id=message.chat.id, filters=filters.text, timeout=300)
        pdf_url = None if pdf_msg.text.lower() == "/skip" else pdf_msg.text.strip()
        await prompt.delete()
        await pdf_msg.delete()

        # Step 3: Get batch name
        prompt = await message.reply_text("🏷️ Send batch name (e.g., Batch-1)")
        batch_msg = await client.listen(chat_id=message.chat.id, filters=filters.text, timeout=300)
        batch_name = batch_msg.text.strip().replace(" ", "_")
        await prompt.delete()
        await batch_msg.delete()

        if not (video_url or pdf_url):
            await message.reply_text("❌ Please provide at least one URL!")
            return

        # Process Video
        if video_url:
            video_name = f"{batch_name}_video.mp4"
            msg = await message.reply_text(f"⏬ Downloading video...\nURL: {video_url[:50]}...")

            stdout, stderr, returncode = await download_hls(video_url, video_name)
            
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
            await client.send_video(
                chat_id=message.chat.id,
                video=video_name,
                caption=f"🎥 {batch_name}",
                supports_streaming=True,
                progress=lambda c, t: asyncio.create_task(
                    msg.edit_text(f"📤 Uploading video... {c*100/t:.1f}%")
                )
            )
            await safe_delete(video_name)
            video_name = None  # Mark as cleaned up

        # Process PDF
        if pdf_url:
            pdf_name = f"{batch_name}.pdf"
            msg = await message.reply_text(f"⏬ Downloading PDF...\nURL: {pdf_url[:50]}...")
            
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
            await client.send_document(
                chat_id=message.chat.id,
                document=pdf_name,
                caption=f"📄 {batch_name}",
                progress=lambda c, t: asyncio.create_task(
                    msg.edit_text(f"📤 Uploading PDF... {c*100/t:.1f}%")
                )
            )
            await safe_delete(pdf_name)
            pdf_name = None  # Mark as cleaned up

        await message.reply_text("✅ All files processed successfully! 🚀")

    except Timeout:
        await message.reply_text("⌛ Operation timed out after 5 minutes")
    except Exception as e:
        await message.reply_text(f"❌ Critical error: {str(e)}")
    finally:
        # Final cleanup with null checks
        await safe_delete(video_name)
        await safe_delete(pdf_name)

if __name__ == "__main__":
    print("⚡ Bot Started!")
    bot.run()
