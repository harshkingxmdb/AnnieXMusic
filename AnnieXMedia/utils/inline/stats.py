# Authored By Certified Coders © 2025

from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup


class StatsCallbacks:
    SHOW_OVERVIEW = "stats:overview"
    SHOW_BOT_STATS = "stats:bot"
    BACK = "stats:back"
    CLOSE = "stats:close"


def build_stats_keyboard(_, is_sudo: bool) -> InlineKeyboardMarkup:
    non_sudo_row = [
        InlineKeyboardButton(
            text=_["SA_B_1"],
            callback_data=StatsCallbacks.SHOW_OVERVIEW,
            style=ButtonStyle.PRIMARY,
        )
    ]

    sudo_row = [
        InlineKeyboardButton(
            text=_["SA_B_2"],
            callback_data=StatsCallbacks.SHOW_BOT_STATS,
            style=ButtonStyle.SUCCESS,
        ),
        InlineKeyboardButton(
            text=_["SA_B_3"],
            callback_data=StatsCallbacks.SHOW_OVERVIEW,
            style=ButtonStyle.PRIMARY,
        ),
    ]

    rows = [
        sudo_row if is_sudo else non_sudo_row,
        [
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"],
                callback_data=StatsCallbacks.CLOSE,
                style=ButtonStyle.DANGER,
            )
        ],
    ]

    return InlineKeyboardMarkup(rows)


def build_back_keyboard(_) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=_["BACK_BUTTON"],
                callback_data=StatsCallbacks.BACK,
                style=ButtonStyle.SECONDARY,
            ),
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"],
                callback_data=StatsCallbacks.CLOSE,
                style=ButtonStyle.DANGER,
            ),
        ]
    ]

    return InlineKeyboardMarkup(rows)
