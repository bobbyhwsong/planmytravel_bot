import os
import logging
from utils import send_action, facts_to_str
from chat import MyTravelAgent
from dotenv import load_dotenv
from emoji import emojize
import argparse
from datetime import datetime as time


parser = argparse.ArgumentParser(description="Process some integers.")
parser.add_argument(
    "--MODEL", default="gpt-3.5-turbo", required=False, help="Specify the GPT version"
)
args = parser.parse_args()

# MODEL = args.MODEL
MODEL = "gpt-4-1106-preview"

TEMPLATE = "template_06"


from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)

from telegram.constants import ChatAction

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ConversationHandler,
    filters,
    MessageHandler,
    ContextTypes,
    CallbackQueryHandler,
)


load_dotenv(verbose=True)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


# Predefined emojis
bookmark = emojize(":bookmark:", use_aliases=True)
bell = emojize(":bell:", use_aliases=True)
lightning = emojize(":high_voltage:", use_aliases=True)
good = emojize(":smiling_face_with_sunglasses:", use_aliases=True)
siren = emojize(":police_car_light:", use_aliases=True)
plus = emojize(":plus:", use_aliases=True)
minus = emojize(":minus:", use_aliases=True)
party = emojize(":party_popper:", use_aliases=True)


send_typing_action = send_action(ChatAction.TYPING)

######################

START, CUSTOMIZE, EMOJI, POLITE, VERBOSE, WARM, DONE, PLAN = range(8)
# START, CUSTOMIZE, PLAN = range(3)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    logger.info("User %s started the conversation.", user.first_name)
    with open(f"chatlog/{update.effective_chat.id}.log", "a") as f:
        f.write(
            f"{time.now()} - {'system':<9}: ********** {user.first_name} 대화 시작 **********\n"
        )

    # Create an agent with a given template
    agent = MyTravelAgent(
        prompt_file=TEMPLATE, user=update.effective_chat.id, model=MODEL
    )
    logger.info(f"A new agent was created for {agent.user}")
    logger.info(f"A default chat style: {agent.style}")

    context.user_data["agent"] = agent
    context.user_data["style"] = {
        "emoji": True,
        "polite": True,
        "verbose": True,
        "warm": False,
    }

    options = [
        [
            InlineKeyboardButton(
                text=f"{good} 나만의 챗봇 만들기 {good}", callback_data="customize"
            )
        ],
        [
            InlineKeyboardButton(
                text=f"{siren} 여행계획 세우기 {siren}", callback_data="plan"
            ),
        ],
    ]
    markup = InlineKeyboardMarkup(options)

    await update.message.reply_text(
        text="안녕하세요, 당신의 여행을 도와주는 챗봇🤖입니다. 무엇을 할까요?", reply_markup=markup
    )

    return CUSTOMIZE


async def customize(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    user = update.effective_user
    await query.answer()

    if query.data == "customize":
        logger.info(f"callback_start: {query.data}")
        await query.edit_message_text(text=f"좋아요! 나만의 챗봇을 만들어볼까요?{good}")

        options = [InlineKeyboardButton(text=f"> 시작하기 <", callback_data="emoji")]

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"지금부터 {user.first_name}님이 선호하는 챗봇으로 만들어보세요!",
            reply_markup=InlineKeyboardMarkup([options]),
        )
        return EMOJI

    elif query.data == "plan":
        logger.info(query.data)
        await query.edit_message_text(text=f"응답이 반영되었습니다! 여행을 도와드릴게요{good}")

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"{user.first_name}님, 지금 어디신가요?",
        )
        # without customizing

        logger.info(f"without customized: {context.user_data}")

        return PLAN


async def emoji(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    logger.info(f"emoji_tf: {query.data}")

    options = [
        [
            InlineKeyboardButton(
                text=f"{good}이모티콘도 적절히 사용해주세요.{good}", callback_data="emoji_on"
            )
        ],
        [InlineKeyboardButton(text=f"텍스트로만 대답해주세요.", callback_data="emoji_off")],
    ]

    # Buttons' layout markup
    reply_markup = InlineKeyboardMarkup(options)

    # Message with the buttons
    await query.edit_message_text(
        # chat_id=update.effective_chat.id,
        text="이모티콘도 사용해볼까요?",
        reply_markup=reply_markup,
    )

    return VERBOSE


async def emoji_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    logger.info(f"emoji_callback: {query.data}")

    if query.data == "emoji_on":
        context.user_data["style"]["emoji"] = True
        await query.edit_message_text(text=f"좋아요! 이모티콘도 사용해볼게요{good}")
    elif query.data == "emoji_off":
        context.user_data["style"]["emoji"] = False
        await query.edit_message_text(text=f"네, 텍스트로만 대답할게요{siren}")

    logger.info(context.user_data)


async def verbose(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    await emoji_callback(update, context)
    logger.info(f"polite_tf: {query.data}")

    options = [
        [InlineKeyboardButton(text=f"최대한 자세하고 길게 대답해주세요", callback_data="verbose_on")],
        [InlineKeyboardButton(text=f"간결하고 짧게 대답해주세요", callback_data="verbose_off")],
    ]

    # Buttons' layout markup
    reply_markup = InlineKeyboardMarkup(options)

    # Message with the buttons
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="길고 상세한 답변을 원하시나요?",
        reply_markup=reply_markup,
    )

    return POLITE


async def verbose_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    logger.info(f"verbose_callback: {query.data}")

    if query.data == "verbose_on":
        context.user_data["style"]["verbose"] = True
        await query.edit_message_text(text=f"좋아요! 최대한 자세하게 대답할게요{good}")

    elif query.data == "verbose_off":
        context.user_data["style"]["verbose"] = False
        await query.edit_message_text(text=f"네, 간결하게 대답할게요{siren}")

    logger.info(context.user_data)


async def polite(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    await verbose_callback(update, context)

    logger.info(f"polite_tf: {query.data}")

    options = [
        [
            InlineKeyboardButton(
                text=f"{good} 존댓말로 공손하게 {good}", callback_data="polite_on"
            )
        ],
        [
            InlineKeyboardButton(
                text=f"{siren} 반말로 친근하게 {siren}", callback_data="polite_off"
            )
        ],
    ]

    # Buttons' layout markup
    reply_markup = InlineKeyboardMarkup(options)

    # Message with the buttons
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="친근하게 반말로? 아니면 공손하게 존댓말로?",
        reply_markup=reply_markup,
    )
    return WARM


async def polite_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    logger.info(f"polite_callback: {query.data}")

    if query.data == "polite_on":
        context.user_data["style"]["polite"] = True
        await query.edit_message_text(text=f"존댓말로 공손하게 대답해드릴게요{good}")

    elif query.data == "polite_off":
        context.user_data["style"]["polite"] = False
        await query.edit_message_text(text=f"반말로 친근하게 대답할게{good}")

    logger.info(context.user_data)


async def warm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    await polite_callback(update, context)

    logger.info(f"warm_tf: {query.data}")

    options = [
        [InlineKeyboardButton(text=f"따스하게", callback_data="warm_on")],
        [InlineKeyboardButton(text=f"차갑게", callback_data="warm_off")],
    ]

    # Buttons' layout markup
    reply_markup = InlineKeyboardMarkup(options)

    # Message with the buttons
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="대화의 온도는?",
        reply_markup=reply_markup,
    )
    return DONE


async def warm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    logger.info(f"warm_callback: {query.data}")

    if query.data == "warm_on":
        context.user_data["style"]["warm"] = True
        await query.edit_message_text(text=f"따뜻한 말투로 대답해 드릴게요{good}")

    elif query.data == "warm_off":
        context.user_data["style"]["warm"] = False
        await query.edit_message_text(text=f"차가운 말투로 대답해 드릴게요{good}")

    logger.info(context.user_data)


@send_typing_action
async def done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Display the gathered info and end the conversation."""

    query = update.callback_query
    await query.answer()

    await warm_callback(update, context)
    user = update.effective_user

    logger.info("User %s done the conversation.", user.first_name)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"{user.first_name}님만의 챗봇이 완성되었습니다!{good} 지금 어디신가요?{party}",
    )
    logger.info(context.user_data)

    return PLAN


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)

    await update.message.reply_text(f"{user.first_name}님의 대화를 종료합니다! 다음에 또 만나요!")

    with open(f"chatlog/{update.effective_chat.id}.log", "a") as f:
        f.write(
            f"{time.now()} - {'system':<9}: ********** {user.first_name} 대화 종료 **********\n\n\n"
        )

    agent = context.user_data["agent"]

    context.user_data.clear()

    agent.messages = []

    return ConversationHandler.END


@send_typing_action
async def response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    agent = context.user_data["agent"]
    agent.style = context.user_data["style"]
    agent.set_style()

    logger.info(agent.style)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=agent.response(update.message.text, last_n=10),
    )
    return PLAN


async def show_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display the gathered info."""
    await update.message.reply_text(f"수집된 정보: {facts_to_str(context.user_data)}")


def main() -> None:
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    # Create an agent with a given template: template_01

    conversation = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CUSTOMIZE: [CallbackQueryHandler(customize)],
            EMOJI: [CallbackQueryHandler(emoji)],
            POLITE: [CallbackQueryHandler(polite)],
            VERBOSE: [CallbackQueryHandler(verbose)],
            WARM: [CallbackQueryHandler(warm)],
            DONE: [CallbackQueryHandler(done)],
            PLAN: [MessageHandler(filters.TEXT & (~filters.COMMAND), response)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
        per_chat=True,
        per_user=True,
    )

    application.add_handler(conversation)

    show_data_handler = CommandHandler("show_data", show_data)
    application.add_handler(show_data_handler)

    application.run_polling()


if __name__ == "__main__":
    main()
