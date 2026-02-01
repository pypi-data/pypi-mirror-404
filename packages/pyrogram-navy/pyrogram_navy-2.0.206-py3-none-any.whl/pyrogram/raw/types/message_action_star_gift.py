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

from io import BytesIO

from pyrogram.raw.core.primitives import Int, Long, Int128, Int256, Bool, Bytes, String, Double, Vector
from pyrogram.raw.core import TLObject
from pyrogram import raw
from typing import List, Optional, Any

# # # # # # # # # # # # # # # # # # # # # # # #
#               !!! WARNING !!!               #
#          This is a generated file!          #
# All changes made in this file will be lost! #
# # # # # # # # # # # # # # # # # # # # # # # #


class MessageActionStarGift(TLObject):  # type: ignore
    """Telegram API type.

    Constructor of :obj:`~pyrogram.raw.base.MessageAction`.

    Details:
        - Layer: ``195``
        - ID: ``8557637``

    Parameters:
        gift (:obj:`StarGift <pyrogram.raw.base.StarGift>`):
            N/A

        name_hidden (``bool``, *optional*):
            N/A

        saved (``bool``, *optional*):
            N/A

        converted (``bool``, *optional*):
            N/A

        message (:obj:`TextWithEntities <pyrogram.raw.base.TextWithEntities>`, *optional*):
            N/A

        convert_stars (``int`` ``64-bit``, *optional*):
            N/A

    """

    __slots__: List[str] = ["gift", "name_hidden", "saved", "converted", "message", "convert_stars"]

    ID = 0x8557637
    QUALNAME = "types.MessageActionStarGift"

    def __init__(self, *, gift: "raw.base.StarGift", name_hidden: Optional[bool] = None, saved: Optional[bool] = None, converted: Optional[bool] = None, message: "raw.base.TextWithEntities" = None, convert_stars: Optional[int] = None) -> None:
        self.gift = gift  # StarGift
        self.name_hidden = name_hidden  # flags.0?true
        self.saved = saved  # flags.2?true
        self.converted = converted  # flags.3?true
        self.message = message  # flags.1?TextWithEntities
        self.convert_stars = convert_stars  # flags.4?long

    @staticmethod
    def read(b: BytesIO, *args: Any) -> "MessageActionStarGift":
        
        flags = Int.read(b)
        
        name_hidden = True if flags & (1 << 0) else False
        saved = True if flags & (1 << 2) else False
        converted = True if flags & (1 << 3) else False
        gift = TLObject.read(b)
        
        message = TLObject.read(b) if flags & (1 << 1) else None
        
        convert_stars = Long.read(b) if flags & (1 << 4) else None
        return MessageActionStarGift(gift=gift, name_hidden=name_hidden, saved=saved, converted=converted, message=message, convert_stars=convert_stars)

    def write(self, *args) -> bytes:
        b = BytesIO()
        b.write(Int(self.ID, False))

        flags = 0
        flags |= (1 << 0) if self.name_hidden else 0
        flags |= (1 << 2) if self.saved else 0
        flags |= (1 << 3) if self.converted else 0
        flags |= (1 << 1) if self.message is not None else 0
        flags |= (1 << 4) if self.convert_stars is not None else 0
        b.write(Int(flags))
        
        b.write(self.gift.write())
        
        if self.message is not None:
            b.write(self.message.write())
        
        if self.convert_stars is not None:
            b.write(Long(self.convert_stars))
        
        return b.getvalue()
