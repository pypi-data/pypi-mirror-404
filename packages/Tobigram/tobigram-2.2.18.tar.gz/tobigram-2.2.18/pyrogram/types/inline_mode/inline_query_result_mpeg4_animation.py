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

import logging
from typing import Optional

import pyrogram
from pyrogram import raw, types, utils, enums
from .inline_query_result import InlineQueryResult

log = logging.getLogger(__name__)


class InlineQueryResultMpeg4Animation(InlineQueryResult):
    """Represents a link to a video animation (H.264/MPEG-4 AVC video without sound).

    By default, this MPEG4 animation will be sent by the user with optional caption.
    Alternatively, you can use *input_message_content* to send a message with the specified content instead of the
    animation.

    Parameters:
        mpeg4_animation_url (``str``):
            A valid URL for the MPEG4 file.

        mpeg4_animation_width (``int``, *optional*):
            Width of the video.

        mpeg4_animation_height (``int``, *optional*):
            Height of the video.

        mpeg4_animation_duration (``int``, *optional*):
            Duration of the video in seconds.

        thumbnail_url (``str``, *optional*):
            URL of the static (JPEG or GIF) or animated (MPEG4) thumbnail for the result.

        thumbnail_mime_type (``str``, *optional*):
            MIME type of the thumbnail. Must be one of "image/jpeg", "image/gif", or "video/mp4".
            Defaults to "image/jpeg".

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
        mpeg4_animation_url: str,
        mpeg4_animation_width: int = 0,
        mpeg4_animation_height: int = 0,
        mpeg4_animation_duration: int = 0,
        thumbnail_url: str = None,
        thumbnail_mime_type: str = "image/jpeg",
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

        self.mpeg4_animation_url = mpeg4_animation_url
        self.mpeg4_animation_width = mpeg4_animation_width
        self.mpeg4_animation_height = mpeg4_animation_height
        self.mpeg4_animation_duration = mpeg4_animation_duration
        self.thumbnail_url = thumbnail_url
        self.thumbnail_mime_type = thumbnail_mime_type
        self.title = title
        self.caption = caption
        self.parse_mode = parse_mode
        self.caption_entities = caption_entities
        self.show_caption_above_media = show_caption_above_media
        self.reply_markup = reply_markup
        self.input_message_content = input_message_content

    async def write(self, client: "pyrogram.Client"):
        mpeg4_doc = raw.types.InputWebDocument(
            url=self.mpeg4_animation_url,
            size=0,
            mime_type="video/mp4",
            attributes=[
                raw.types.DocumentAttributeVideo(
                    w=self.mpeg4_animation_width,
                    h=self.mpeg4_animation_height,
                    duration=self.mpeg4_animation_duration
                )
            ]
        )

        thumb = (
            raw.types.InputWebDocument(
                url=self.thumbnail_url,
                size=0,
                mime_type=self.thumbnail_mime_type,
                attributes=[]
            )
            if self.thumbnail_url
            else None
        )

        message, entities = (await utils.parse_text_entities(
            client, self.caption, self.parse_mode, self.caption_entities
        )).values()

        return raw.types.InputBotInlineResult(
            id=self.id,
            type=self.type,
            title=self.title,
            thumb=thumb,
            content=mpeg4_doc,
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
