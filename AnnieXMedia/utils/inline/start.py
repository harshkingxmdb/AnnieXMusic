# Authored By Certified Coders © 2025

from pyrogram.types import InlineKeyboardButton

import config
from AnnieXMedia import app


def start_panel(_):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["S_B_1"],
                url=f"https://t.me/{app.username}?startgroup=true",
                style=ButtonStyle.PRIMARY,
            ),
            InlineKeyboardButton(
                text=_["S_B_2"],
                url=config.SUPPORT_CHANNEL,
                style=ButtonStyle.SUCCESS,
            ),
        ],
    ]

    return buttons


def private_panel(_):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["S_B_1"],
                url=f"https://t.me/{app.username}?startgroup=true",
                style=ButtonStyle.PRIMARY,
            )
        ],
        [
            InlineKeyboardButton(
                text=_["S_B_7"],
                user_id=config.OWNER_ID,
                style=ButtonStyle.SECONDARY,
            ),
            InlineKeyboardButton(
                text=_["S_B_4"],
                url=config.SUPPORT_CHAT,
                style=ButtonStyle.SUCCESS,
            ),
        ],
        [
            InlineKeyboardButton(
                text=_["S_B_3"],
                callback_data="open_help",
                style=ButtonStyle.DANGER,
            ),
        ],
    ]

    return buttons
