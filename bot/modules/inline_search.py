from pyrogram import Client
from bot import Config, LOGGER
from bot.helpers.translations import lang
from pyrogram.errors import QueryIdInvalid
from bot.helpers.utils.media_search import search_media_audio
from bot.helpers.utils.tidal_api import search_track, search_album
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InlineQuery, InlineQueryResultArticle, \
    InputTextMessageContent

"""
-a for album search
-s for track search
-d for file search in the channel
"""


@Client.on_inline_query()
async def inline_search_tidal(_, event: InlineQuery):
    answers = list()
    msg = None
    links = None
    if event.query == "" or not event.query.startswith(("-a", "-s", "-d")):
        answers.append(
            InlineQueryResultArticle(
                title=lang.INLINE_PLACEHOLDER,
                input_message_content=InputTextMessageContent(
                    message_text=lang.INLINE_SEARCH_HELP
                ),
                thumb_url=Config.INLINE_THUMB,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="Search",
                                switch_inline_query_current_chat=""
                            )
                        ]
                    ]
                )
            )
        )
    else:
        query = event.query
        if query.startswith("-s "):
            query = query[3:]
            msg, title, artist, url, thumb = await search_track(query)
        elif query.startswith("-a "):
            query = query[3:]
            msg, title, artist, url, thumb = await search_album(query)
        elif query.startswith("-d ") and Config.SEARCH_CHANNEL:
            query = query[3:]
            title, artist, links = await search_media_audio(query)
        else:
            msg = None

        if msg:
            for name in title:
                if thumb is None:
                    thumb = Config.INLINE_THUMB
                answers.append(
                    InlineQueryResultArticle(
                        title=name,
                        description=artist[title.index(name)],
                        input_message_content=InputTextMessageContent(
                            message_text=msg[title.index(name)],
                            disable_web_page_preview=True,
                        ),
                        thumb_url=thumb[title.index(name)],
                        reply_markup=InlineKeyboardMarkup(
                            [
                                [
                                    InlineKeyboardButton(
                                        text="Link",
                                        url=url[title.index(name)]
                                    )
                                ],
                                [
                                    InlineKeyboardButton(
                                        text="Search Again",
                                        switch_inline_query_current_chat=""
                                    )
                                ]
                            ]
                        )
                    )
                )
        elif links:
            for name in title:
                answers.append(
                    InlineQueryResultArticle(
                        title=name,
                        description=artist[title.index(name)],
                        input_message_content=InputTextMessageContent(
                            message_text=lang.INLINE_MEDIA_SEARCH.format(
                                name,
                                artist[title.index(name)]
                            ),
                            disable_web_page_preview=True,
                        ),
                        thumb_url=Config.INLINE_THUMB,
                        reply_markup=InlineKeyboardMarkup(
                            [
                                [
                                    InlineKeyboardButton(
                                        text="Search Again",
                                        switch_inline_query_current_chat=""
                                    )
                                ],
                                [
                                    InlineKeyboardButton(
                                        text="File Here",
                                        url=links[title.index(name)]
                                    )
                                ]
                            ]
                        )
                    )
                )
        else:
            answers.append(
                InlineQueryResultArticle(
                    title=lang.INLINE_NO_RESULT,
                    input_message_content=InputTextMessageContent(
                        message_text=lang.INLINE_NO_RESULT
                    ),
                    thumb_url=Config.INLINE_THUMB,
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    text="Search Again",
                                    switch_inline_query_current_chat=""
                                )
                            ]
                        ]
                    )
                )
            )

    try:
        await event.answer(
            results=answers,
            cache_time=0
        )
    except QueryIdInvalid:
        LOGGER.info(f"QueryIdInvalid: {event.query}")