import os
import subprocess
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

BOT_TOKEN = os.environ.get("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 M3U8 Downloader Bot වෙත සාදරයෙන් පිළිගනිමු! Link එක එවන්න.")

async def handle_m3u8(update: Update, context: ContextTypes.DEFAULT_TYPE):
    m3u8_url = update.message.text.strip()
    status_msg = await update.message.reply_text("⏳ Video එක Download වෙමින් පවතී...")
    output_filename = f"video_{update.message.message_id}.mp4"
    
    ffmpeg_cmd = ["ffmpeg", "-y", "-i", m3u8_url, "-c", "copy", "-bsf:a", "aac_adtstoasc", output_filename]

    try:
        process = subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if process.returncode != 0:
            await status_msg.edit_text("❌ Download කිරීම අසාර්ථක විය.")
            if os.path.exists(output_filename): os.remove(output_filename)
            return

        await status_msg.edit_text("📤 Upload වෙමින් පවතී...")
        with open(output_filename, 'rb') as video_file:
            await update.message.reply_video(video=video_file, caption="✅ Download සාර්ථකයි!")
        await status_msg.delete()

    except Exception as e:
        await status_msg.edit_text(f"❌ Error එකක් ආවා: `{str(e)}`")
    finally:
        if os.path.exists(output_filename): os.remove(output_filename)

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_m3u8))
    print("Bot is running...")
    app.run_polling()
