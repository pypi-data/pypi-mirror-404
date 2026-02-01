#  Pyrogram - Telegram MTProto API Client Library for Python
#  Copyright (C) 2017-present Dan <https://github.com/delivrance>
#
#  This file is part of Pyrogram.
#
#  Pyrogram is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Lesser General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Pyrogram is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with Pyrogram.  If not, see <http://www.gnu.org/licenses/>.

from typing import Optional

import pyrogram
from pyrogram import raw, types, utils, enums
from .inline_query_result import InlineQueryResult


class InlineQueryResultCachedMpeg4Animation(InlineQueryResult):
    """Represents a link to a cached MPEG4 animation (H.264/MPEG-4 AVC video without sound).

    By default, this MPEG4 animation will be sent by the user with optional caption.
    Alternatively, you can use *input_message_content* to send a message with the specified content instead of the
    animation.

    Parameters:
        mpeg4_animation_file_id (``str``):
            A valid file identifier for the MPEG4 animation.

        id (``str``, *optional*):
            Unique identifier for this result, 1-64 bytes.
            Defaults to a randomly generated UUID4.

        title (``str``, *optional*):
            Title for the result.

        caption (``str``, *optional*):
            Caption of the MPEG-4 animation to be sent, 0-1024 characters after entities parsing.

        parse_mode (:obj:`~pyrogram.enums.ParseMode`, *optional*):
            By default, texts are parsed using both Markdown and HTML styles.
            You can combine both syntaxes together.

        caption_entities (List of :obj:`~pyrogram.types.MessageEntity`):
            List of special entities that appear in the caption, which can be specified instead of *parse_mode*.

        show_caption_above_media (``bool``, *optional*):
            Pass True, if the caption must be shown above the message media.

        reply_markup (:obj:`~pyrogram.types.InlineKeyboardMarkup`, *optional*):
            Inline keyboard attached to the message.

        input_message_content (:obj:`~pyrogram.types.InputMessageContent`):
            Content of the message to be sent instead of the MPEG4 animation.
    """

    def __init__(
        self,
        mpeg4_animation_file_id: str,
        id: str = None,
        title: str = None,
        caption: str = "",
        parse_mode: Optional["enums.ParseMode"] = None,
        caption_entities: list["types.MessageEntity"] = None,
        show_caption_above_media: bool = None,
        reply_markup: "types.InlineKeyboardMarkup" = None,
        input_message_content: "types.InputMessageContent" = None,
    ):
        super().__init__("mpeg4_gif", id, input_message_content, reply_markup)

        self.mpeg4_animation_file_id = mpeg4_animation_file_id
        self.title = title
        self.caption = caption
        self.parse_mode = parse_mode
        self.caption_entities = caption_entities
        self.show_caption_above_media = show_caption_above_media
        self.reply_markup = reply_markup
        self.input_message_content = input_message_content

    async def write(self, client: "pyrogram.Client"):
        message, entities = (await utils.parse_text_entities(
            client, self.caption, self.parse_mode, self.caption_entities
        )).values()

        return raw.types.InputBotInlineResultCached(
            id=self.id,
            type=self.type,
            title=self.title,
            file_id=await client.storage.file_id(self.mpeg4_animation_file_id),
            send_message=(
                await self.input_message_content.write(client, self.reply_markup)
                if self.input_message_content
                else raw.types.InputBotInlineMessageMediaAuto(
                    reply_markup=await self.reply_markup.write(client) if self.reply_markup else None,
                    message=message,
                    entities=entities,
                    invert_media=self.show_caption_above_media
                )
            )
        )
