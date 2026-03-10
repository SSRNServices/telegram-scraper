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

# =============================
# CONFIG (USE ENV VARIABLES)
# =============================

api_id = int(os.getenv("TG_API_ID"))
api_hash = os.getenv("TG_API_HASH")

target_channel = "@LootDeals193"

webhook_url = "https://n8n.ssrn.online/webhook-test/faf98eb2-4660-43b3-ba4e-2173921dab8a"

session_name = "deal_listener"


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

processed_messages = deque(maxlen=5000)


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

        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:

            for attempt in range(retries):

                try:

                    async with session.post(webhook_url, json=payload) as response:

                        if response.status == 200:

                            logging.info("Sent to n8n successfully")
                            return True

                        else:

                            logging.warning(f"Webhook returned status {response.status}")

                except Exception as e:

                    logging.error(f"Webhook error: {e}")

                await asyncio.sleep(delay)

            logging.error("Failed sending webhook after retries")

    return False


# =============================
# PROCESS TELEGRAM MESSAGE
# =============================

async def process_message(event):

    message = event.message
    message_id = message.id
    text = message.text or ""

    if not text:
        return

    if message_id in processed_messages:
        return

    processed_messages.append(message_id)

    urls = URL_REGEX.findall(text)

    if not urls:
        return

    # Detect image
    image_url = None

    if message.photo:
        image_url = f"https://t.me/{target_channel.replace('@','')}/{message_id}"

    payload = {
        "message_id": message_id,
        "channel": target_channel,
        "text": text,
        "urls": urls,
        "image": image_url,
        "date": str(message.date)
    }

    await send_to_webhook(payload)


# =============================
# NEW MESSAGE LISTENER
# =============================

@client.on(events.NewMessage(chats=target_channel))
async def new_message_handler(event):

    logging.info("New message received")

    await process_message(event)


# =============================
# EDITED MESSAGE LISTENER
# =============================

@client.on(events.MessageEdited(chats=target_channel))
async def edited_message_handler(event):

    logging.info("Message edited")

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