import logging
import dotenv
import os
from telegram import Update, InlineQueryResultArticle, InputTextMessageContent, ForceReply,  InlineKeyboardButton, InlineKeyboardMarkup, constants
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, filters, MessageHandler, InlineQueryHandler, ConversationHandler, CallbackQueryHandler

END = ConversationHandler.END
TAX, TAX_BUTTON, GST, PEOPLE = range(4)



dotenv.load_dotenv()
token = os.environ['TOKEN']

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

price = 0

#START FUNCTION

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Payment testing bot! Please run /split to split your bill.")

#SPLIT FUNCTION

async def split(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text = "How much was the bill in $?",
        reply_markup=ForceReply()
    )

    return TAX

async def tax(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    base_value = update.message.text

    global price

    price = base_value


    options = [
        [
            InlineKeyboardButton("Yes", callback_data=1),
            InlineKeyboardButton("No", callback_data=0)
        ]
    ]
    await update.message.reply_text(
        text = f"The base bill was ${base_value:,.2f}. Is service charge included in the price?",
        reply_markup = InlineKeyboardMarkup(options)
    )

    return TAX_BUTTON


async def tax_button(update:Update, context: ContextTypes.DEFAULT_TYPE):

    global price

    print(price)

    added = False
    query = update.callback_query

    await query.answer()

    ans = query.data

    if query.data == "1":
        added = True
        print(price)


    elif query.data == "0":
        price = float(price)
        price = round(price * 1.1, 2)
        print(price)

    await query.edit_message_text(text = f"The bill after service charge is ${price:,.2f}.")


    options = [
        [
            InlineKeyboardButton("Yes", callback_data=1),
            InlineKeyboardButton("No", callback_data=0)
        ]
    ]
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Is GST included in the price?",
        reply_markup=InlineKeyboardMarkup(options)
    )

    return GST

async def gst(update:Update, context: ContextTypes.DEFAULT_TYPE):

    global price

    query = update.callback_query

    await query.answer()

    ans = query.data

    if ans == "0":
        price = round(float(price) * 1.08, 2)

    await query.edit_message_text(f"The final bill is: ${price:,.2f}")

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text = "How many people do you want to split amongst?",
        reply_markup= ForceReply()
    )

    return PEOPLE

async def people(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    people = int(update.message.text)

    global price

    per_pax = round(price/people, 2)

    await context.bot.send_message(
        chat_id = update.effective_chat.id,
        text = f"Each person is to pay <b>${per_pax:,.2f}</b>. \n\n\n"
               f"Thank you for using our bot. We hope that it has been helpful.",
        parse_mode = constants.ParseMode.HTML
    )

    return END



async def done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Fail"
    )

#INITIALIZING THE APP

def main():
    app = ApplicationBuilder().token(os.environ['TOKEN']).build()

    #START HANDLER
    start_handler = CommandHandler('start', start)
    app.add_handler(start_handler)

    #SPLIT HANDLER
    split_handler = ConversationHandler(
        entry_points= [CommandHandler('split', split)],
        states = {
            TAX: [MessageHandler(filters.TEXT & ~filters.COMMAND, tax)],
            TAX_BUTTON: [CallbackQueryHandler(tax_button)],
            GST: [CallbackQueryHandler(gst)],
            PEOPLE:[MessageHandler(filters.TEXT & ~filters.COMMAND, people)]
        },
        fallbacks=[MessageHandler(filters.Regex("^Done$"), done)],
    )
    app.add_handler(split_handler)

    app.run_polling()

if __name__ == "__main__":
    main()

