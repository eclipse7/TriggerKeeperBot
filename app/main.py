import logging
from json import loads

from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ContentType

from config import API_TOKEN, ADMINS
from types_db import engine, local_triggers, MessageType


# Configure logging
logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
ENGINE = engine


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    """
    This handler will be called when client send `/start` command.
    """
    await message.answer("Hi! I'm TriggerKeeperBot!\nDeveloped by @ambient_luna\nFor more info, please see /help")


@dp.message_handler(commands=['help'])
async def send_welcome(message: types.Message):
    text = 'Cписок триггеров: /all_triggers\n'
    text += 'Добавить триггер: replay сообщения с текстом /add_trigger trigger_name\n'
    text += 'Удалить триггер: /del_trigger trigger_name\n'
    await message.answer(text)


@dp.message_handler(commands=['ping'])
async def ping(message: types.Message):
    await message.answer("pong, @{}".format(message.from_user.username))


@dp.message_handler(commands=['all_triggers'])
async def all_triggers(message: types.Message):
    chat_id = message.chat.id

    text = 'Cписок триггеров:\n'
    keys = ''
    async with ENGINE.acquire() as conn:
        async for row in conn.execute(local_triggers.
                                      select().
                                      where(local_triggers.c.chat_id == chat_id)):
            keys += str(row.trigger) + '\n'
    if keys:
        await message.answer(text + keys)
    else:
        await message.answer("No triggers")


@dp.message_handler(commands=['add_trigger'])
async def add_trigger(message: types.Message):
    chat_id = message.chat.id

    trigger_key = message.text.split(' ', 1)
    if len(trigger_key) == 2 and len(trigger_key[1]) > 0:
        trigger_key = trigger_key[1].strip()
    else:
        await message.answer('Ошибка, триггер не установлен.')
        return

    if trigger_key and message.reply_to_message:
        if message.reply_to_message.audio:
            trigger_msg = message.reply_to_message.audio.file_id
            message_type = MessageType.AUDIO.value
        elif message.reply_to_message.document:
            trigger_msg = message.reply_to_message.document.file_id
            message_type = MessageType.DOCUMENT.value
        elif message.reply_to_message.voice:
            trigger_msg = message.reply_to_message.voice.file_id
            message_type = MessageType.VOICE.value
        elif message.reply_to_message.sticker:
            trigger_msg = message.reply_to_message.sticker.file_id
            message_type = MessageType.STICKER.value
        elif message.reply_to_message.contact:
            trigger_msg = str(message.reply_to_message.contact)
            message_type = MessageType.CONTACT.value
        elif message.reply_to_message.video:
            trigger_msg = message.reply_to_message.video.file_id
            message_type = MessageType.VIDEO.value
        elif message.reply_to_message.video_note:
            trigger_msg = message.reply_to_message.video_note.file_id
            message_type = MessageType.VIDEO_NOTE.value
        elif message.reply_to_message.location:
            trigger_msg = str(message.reply_to_message.location)
            message_type = MessageType.LOCATION.value
        elif message.reply_to_message.photo:
            trigger_msg = message.reply_to_message.photo[-1].file_id
            message_type = MessageType.PHOTO.value
        else:
            trigger_msg = message.reply_to_message.text
            message_type = MessageType.TEXT.value

        async with ENGINE.acquire() as conn:
            res = await conn.execute(local_triggers.
                                     select().
                                     where(local_triggers.c.chat_id == chat_id).
                                     where(local_triggers.c.trigger == trigger_key))
            # print(row.id, row.chat_id, row.trigger, row.message, row.message_type)
            if res.rowcount == 0:
                await conn.execute(local_triggers.insert().values(chat_id=chat_id, trigger=trigger_key,
                                                                  message=trigger_msg, message_type=message_type))
                await message.answer('Триггер на фразу "{}" установлен.'.format(trigger_key))
            else:
                await message.answer('Триггер "{}" уже существует, выбери другой.'.format(trigger_key))
    else:
        await message.answer('Ошибка, триггер не установлен.')


@dp.message_handler(commands=['del_trigger'])
async def del_trigger(message: types.Message):
    chat_id = message.chat.id

    # auth
    username = message.from_user.username
    if username not in ADMINS:
        return

    trigger_key = message.text.split(' ', 1)
    if len(trigger_key) == 2 and len(trigger_key[1]) > 0:
        trigger_key = trigger_key[1].strip()
    else:
        return

    if trigger_key:
        async with ENGINE.acquire() as conn:
            res = await conn.execute(local_triggers.
                                     select().
                                     where(local_triggers.c.chat_id == chat_id).
                                     where(local_triggers.c.trigger == trigger_key))
            if res.rowcount > 0:
                await conn.execute(local_triggers.
                                   delete().
                                   where(local_triggers.c.chat_id == chat_id).
                                   where(local_triggers.c.trigger == trigger_key))
                await message.answer('Триггер на фразу "{}" удален.'.format(trigger_key))
            else:
                await message.answer('Ошибка, триггер на фразу "{}" не установлен.'.format(trigger_key))


# @dp.message_handler(content_types=ContentType.TEXT)
@dp.message_handler(content_types=ContentType.TEXT)
async def process_text(message: types.Message):
    chat_id = message.chat.id
    text = message.text

    s = text.lower().strip()
    if s == 'список триггеров':
        await all_triggers(message)
        return

    async with ENGINE.acquire() as conn:
        res = await conn.execute(local_triggers.
                                 select().
                                 where(local_triggers.c.chat_id == chat_id).
                                 where(local_triggers.c.trigger == text))
        res = await res.first()
        if res:
            msg = res.message
            message_type = res.message_type
            if message_type == MessageType.AUDIO.value:
                await message.answer_audio(msg)
            elif message_type == MessageType.DOCUMENT.value:
                await message.answer_document(msg)
            elif message_type == MessageType.VOICE.value:
                await message.answer_voice(msg)
            elif message_type == MessageType.STICKER.value:
                await message.answer_sticker(msg)
            elif message_type == MessageType.CONTACT.value:
                msg = msg.replace('\'', '"')
                contact = loads(msg)
                if 'phone_number' not in contact.keys():
                    contact['phone_number'] = None
                if 'first_name' not in contact.keys():
                    contact['first_name'] = None
                if 'last_name' not in contact.keys():
                    contact['last_name'] = None
                await message.answer_contact(contact['phone_number'], contact['first_name'], contact['last_name'])
            elif message_type == MessageType.VIDEO.value:
                await message.answer_video(msg)
            elif message_type == MessageType.VIDEO_NOTE.value:
                await message.answer_video_note(msg)
            elif message_type == MessageType.LOCATION.value:
                msg = msg.replace('\'', '"')
                location = loads(msg)
                await message.answer_location(location['latitude'], location['longitude'])
            elif message_type == MessageType.PHOTO.value:
                await message.answer_photo(msg)
            else:
                await message.answer(msg)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
