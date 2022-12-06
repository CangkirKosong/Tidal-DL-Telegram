import asyncio
from bot import CMD
from config import Config
from pyrogram import Client, filters
from bot.helpers.translations import lang
from bot.helpers.buttons.help_buttons import *
from bot.helpers.utils.auth_check import get_chats
from bot.helpers.utils.auth_check import check_id, get_chats
from bot.helpers.utils.media_search import index_audio_files
from bot.helpers.utils.media_search import check_file_exist_db
from bot.helpers.database.postgres_impl import users_db, admins_db, chats_db, music_db

@Client.on_message(filters.command(CMD.START))
async def start(bot, update):
    msg = await bot.send_message(
        chat_id=update.chat.id,
        text=lang.INIT_MSG.format(
            update.from_user.first_name
        ),
        reply_to_message_id=update.id
    )
    await asyncio.sleep(1)
    await bot.edit_message_text(
        chat_id=update.chat.id,
        message_id=msg.id,
        text=lang.START_TEXT.format(
            update.from_user.first_name
        )
    )

@Client.on_message(filters.command(CMD.HELP))
async def help_msg(bot, update):
    await bot.send_message(
        chat_id=update.chat.id,
        text=lang.HELP_MSG.format(
            update.from_user.first_name,
            CMD.CMD_LIST[0]
        ),
        reply_to_message_id=update.id,
        disable_web_page_preview=True,
        reply_markup=cmds_button()
    )

@Client.on_callback_query(filters.regex(pattern=r"^cmdscb"))
async def cmd_list(bot, update):
    await bot.edit_message_text(
        chat_id=update.message.chat.id,
        message_id=update.message.id,
        text=lang.CMD_LIST.format(
            update.from_user.first_name,
            CMD.HELP[0],
            CMD.CMD_LIST[0],
            CMD.DOWNLOAD[0],
            CMD.AUTH[0],
            CMD.SHELL[0],
            CMD.SETTINGS[0]
        ),
        disable_web_page_preview=True
    )

@Client.on_message(filters.command(CMD.AUTH))
async def auth_chat(bot, update):
    if check_id(update.from_user.id, restricted=True):
        if update.reply_to_message:
            chat_id = update.reply_to_message.from_user.id
        else:
            try:
                chat_id = int(update.text.split()[1])
            except:
                chat_id = update.chat.id
        
        if str(chat_id).startswith("-100"):
            chats_db.set_chats(int(chat_id))
        else:
            users_db.set_users(int(chat_id))
        # For refreshing the global auth list
        await get_chats()

        await bot.send_message(
            chat_id=update.chat.id,
            text=lang.CHAT_AUTH.format(
                chat_id
            ),
            reply_to_message_id=update.id
        )

@Client.on_message(filters.command(CMD.ADD_ADMIN))
async def add_admin(bot, update):
    if check_id(update.from_user.id, restricted=True):
        if update.reply_to_message:
            admin_id = update.reply_to_message.from_user.id
        else:
            try:
                admin_id = update.text.split()[1]
                if admin_id.isnumeric():
                    pass
                else:
                    admin_id = None
            except:
                admin_id = None
        if admin_id:
            admins_db.set_admins(int(admin_id))
        else:
            await bot.send_message(
                chat_id=update.chat.id,
                text=lang.NO_ID_PROVIDED,
                reply_to_message_id=update.id
            )
            return
        # For refreshing the global admin list
        await get_chats()

        await bot.send_message(
            chat_id=update.chat.id,
            text=lang.ADD_ADMIN.format(
                admin_id
            ),
            reply_to_message_id=update.id
        )

@Client.on_message(filters.command(CMD.INDEX))
async def index_files(bot, update):
    if check_id(update.from_user.id, restricted=True):
        if Config.SEARCH_CHANNEL:
            init = await bot.send_message(
                chat_id=update.chat.id,
                text=lang.INIT_INDEX,
                reply_to_message_id=update.id
            )
            await index_audio_files(Config.SEARCH_CHANNEL)
            await asyncio.sleep(1)
            await bot.edit_message_text(
                chat_id=update.chat.id,
                message_id=init.id,
                text=lang.INDEX_DONE
            )
        else:
            await bot.send_message(
                chat_id=update.chat.id,
                text=lang.ERR_NO_CHANNEL,
                reply_to_message_id=update.id
            )

@Client.on_message(filters.media)
async def add_audio_to_db(bot, update):
    if update.audio:
        if update.chat.id == Config.SEARCH_CHANNEL:
            if not await check_file_exist_db(update.audio.title):
                music_db.set_music(update.id, update.audio.title)


