import asyncio
import re
import logging
import os
from collections import deque
from dotenv import load_dotenv

from telethon import TelegramClient, events
import aiohttp

# =============================
# LOAD ENV VARIABLES
# =============================

load_dotenv()

api_id = int(os.getenv("TG_API_ID"))
api_hash = os.getenv("TG_API_HASH")

# =============================
# CONFIG
# =============================

target_channels = [
    "@LootDeals193",
    "@Premium_HubO",
    "@GiantMod",
]

webhook_url = "https://n8n.ssrn.online/webhook-test/telegram-auto-publish"

session_name = "deal_listener"

media_folder = "downloaded_media"
os.makedirs(media_folder, exist_ok=True)

# =============================
# LOGGING
# =============================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

# =============================
# TELEGRAM CLIENT
# =============================

client = TelegramClient(session_name, api_id, api_hash)

# =============================
# DUPLICATE PROTECTION
# =============================

processed_messages = deque(maxlen=10000)

# =============================
# URL REGEX
# =============================

URL_REGEX = re.compile(r'https?://[^\s\)\]]+')

# =============================
# RATE LIMIT PROTECTION
# =============================

semaphore = asyncio.Semaphore(5)

# =============================
# WEBHOOK SENDER
# =============================

async def send_to_webhook(payload):

    retries = 3
    delay = 2

    async with semaphore:

        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=20)
        ) as session:

            for attempt in range(retries):

                try:

                    async with session.post(webhook_url, json=payload) as response:

                        if response.status == 200:
                            logging.info("Webhook success")
                            return True

                        logging.warning(f"Webhook status {response.status}")

                except Exception as e:
                    logging.error(f"Webhook error: {e}")

                await asyncio.sleep(delay)

            logging.error("Webhook failed after retries")

    return False


# =============================
# DOWNLOAD MEDIA
# =============================

async def download_media(message):

    if not message.media:
        return None

    try:

        file_path = await message.download_media(file=media_folder)

        return file_path

    except Exception as e:

        logging.error(f"Media download failed: {e}")
        return None


# =============================
# PROCESS TELEGRAM MESSAGE
# =============================

async def process_message(event):

    message = event.message
    message_id = message.id

    unique_id = f"{event.chat_id}-{message_id}"

    if unique_id in processed_messages:
        return

    processed_messages.append(unique_id)

    text = message.raw_text or ""

    urls = URL_REGEX.findall(text)

    # channel info
    channel = await event.get_chat()

    channel_username = getattr(channel, "username", None)
    channel_title = channel.title

    # =============================
    # MEDIA DETECTION
    # =============================

    media_type = None

    if message.photo:
        media_type = "photo"

    elif message.video:
        media_type = "video"

    elif message.gif:
        media_type = "gif"

    elif message.sticker:
        media_type = "sticker"

    elif message.document:
        media_type = "document"

    # =============================
    # DOWNLOAD MEDIA
    # =============================

    media_file = await download_media(message)

    # =============================
    # TELEGRAM MESSAGE LINK
    # =============================

    message_link = None

    if channel_username:
        message_link = f"https://t.me/{channel_username}/{message_id}"

    # =============================
    # RAW TELEGRAM MESSAGE
    # =============================

    raw_message = message.to_dict()

    payload = {

        "message_id": message_id,

        "channel_id": event.chat_id,

        "channel_name": channel_title,

        "channel_username": channel_username,

        "message_link": message_link,

        "date": str(message.date),

        "text": text,

        "urls": urls,

        "media_type": media_type,

        "media_file": media_file,

        "raw_message": raw_message
    }

    await send_to_webhook(payload)


# =============================
# NEW MESSAGE LISTENER
# =============================

@client.on(events.NewMessage(chats=target_channels))
async def new_message_handler(event):

    logging.info(f"New message from {event.chat_id}")

    await process_message(event)


# =============================
# EDITED MESSAGE LISTENER
# =============================

@client.on(events.MessageEdited(chats=target_channels))
async def edited_message_handler(event):

    logging.info(f"Edited message in {event.chat_id}")

    await process_message(event)


# =============================
# MAIN LOOP
# =============================

async def main():

    await client.start()

    logging.info("Telegram scraper started")

    await client.run_until_disconnected()


# =============================
# START SCRIPT
# =============================

if __name__ == "__main__":

    asyncio.run(main())