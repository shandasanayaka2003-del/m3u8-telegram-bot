import os
import subprocess
import math
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

BOT_TOKEN = os.environ.get("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 M3U8 Downloader Bot! Link එක එවන්න. (Video එක 360p වලට Compress කර කැබලි ලෙස එවනු ලැබේ)")

async def handle_m3u8(update: Update, context: ContextTypes.DEFAULT_TYPE):
    m3u8_url = update.message.text.strip()
    status_msg = await update.message.reply_text("⏳ 360p වලට Compress කරමින් Download වේ... (විනාඩි කිහිපයක් යනු ඇත)")
    
    msg_id = update.message.message_id
    raw_output = f"compressed_{msg_id}.mp4"

    # FFmpeg හරහා Video එක 360p (Resolution 640x360) වලට Compress කිරීම
    ffmpeg_cmd = [
        "ffmpeg", "-y", "-i", m3u8_url,
        "-vf", "scale=-2:360",
        "-c:v", "libx264", "-crf", "28", "-preset", "veryfast",
        "-c:a", "aac", "-b:a", "64k",
        raw_output
    ]

    try:
        process = subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        if process.returncode != 0 or not os.path.exists(raw_output):
            await status_msg.edit_text("❌ Download/Compression අසාර්ථක විය.")
            return

        total_size_mb = os.path.getsize(raw_output) / (1024 * 1024)
        await status_msg.edit_text(f"📦 Compress වී අවසන්! Size: {total_size_mb:.1f} MB.\nTelegram එකට කොටස් ලෙස Upload වේ...")

        # 45MB Parts වලට Split කිරීම (Telegram Limit එක 50MB නිසා)
        part_size_mb = 45
        part_size_bytes = part_size_mb * 1024 * 1024
        total_parts = math.ceil(total_size_mb / part_size_mb)

        with open(raw_output, 'rb') as f:
            for i in range(total_parts):
                part_filename = f"part_{i+1}_of_{total_parts}_{msg_id}.mp4"
                chunk = f.read(part_size_bytes)
                
                with open(part_filename, 'wb') as chunk_file:
                    chunk_file.write(chunk)

                # Part එක Telegram එකට Upload කිරීම
                with open(part_filename, 'rb') as pf:
                    await update.message.reply_document(
                        document=pf,
                        filename=f"Part_{i+1}_of_{total_parts}.mp4",
                        caption=f"🎬 Part {i+1} / {total_parts} ({os.path.getsize(part_filename)/(1024*1024):.1f} MB)"
                    )
                
                if os.path.exists(part_filename):
                    os.remove(part_filename)

        await status_msg.edit_text("✅ සියලුම කොටස් Upload කර අවසන්!")

    except Exception as e:
        await status_msg.edit_text(f"❌ Error එකක් ආවා: `{str(e)}`")
    finally:
        if os.path.exists(raw_output):
            os.remove(raw_output)

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_m3u8))
    print("Bot is running...")
    app.run_polling()
