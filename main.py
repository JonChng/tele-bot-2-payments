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
        text="Welcome to the payment splitting bot. We hope to be able to help you to split your bills easily amongst you and your friends. \n\n"
             "Please run <b><i>/split</i></b> to begin! \n\n"
             "Alternatively, if you have the final bill (inclusive/exclusive of GST and service charge, run \n\n"
             "<i><b>/instasplit {final price} {number of people to pay}</b></i>\n\n"
             "to split the bill immediately.",
        parse_mode = constants.ParseMode.HTML)


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Testing."
    )

#IMMEDIATE SPLIT
async def instasplit(update: Update, context:ContextTypes.DEFAULT_TYPE):
    #FOR THE IMMEDIATE SPLITTING OF THE BILL
    try:
        price = float(context.args[0])

    except ValueError:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Invalid price. Please enter a number."
        )

    else:
        price = float(context.args[0])

    try:
        price = float(context.args[1])

    except ValueError:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Invalid number of people. Please enter a number."
        )

    else:
        people = float(context.args[1])

    per_pax = round(price / people, 2)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Each person is to pay <b>${per_pax:,.2f}</b>. \n\n\n"
             f"Thank you for using our bot. We hope that it has been helpful.",
        parse_mode=constants.ParseMode.HTML
    )


#SPLIT FUNCTION

async def split(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text = "How much was the bill in $?",
        reply_markup=ForceReply()
    )

    return TAX

async def tax(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global price
    chat_id = update.message.chat_id

    try:
        value = float(update.message.text)

    except ValueError:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Please enter a number.",
            reply_markup=ForceReply()
        )

    else:
        base_value = update.message.text
        price = float(base_value)

    options = [
        [
            InlineKeyboardButton("Yes", callback_data=1),
            InlineKeyboardButton("No", callback_data=0)
        ]
    ]
    await update.message.reply_text(
        text = f"The bill was <b>${price:,.2f}</b>. Is service charge included in the price?",
        reply_markup = InlineKeyboardMarkup(options),
        parse_mode = constants.ParseMode.HTML
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

    await query.edit_message_text(text = f"The bill after service charge is <b>${price:,.2f}</b>.",
                                  parse_mode = constants.ParseMode.HTML)


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

    await query.edit_message_text(f"The final bill after service charge and GST is: <b>${price:,.2f}</b>.",
                                  parse_mode=constants.ParseMode.HTML)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text = "How many people do you want to split amongst?",
        reply_markup= ForceReply()
    )

    return PEOPLE

async def people(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global price

    chat_id = update.message.chat_id

    try:
        people = int(update.message.text)

    except ValueError:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Please enter a integer.",
            reply_markup=ForceReply()
        )

    else:
        people = int(update.message.text)

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

    #HELP HANDLER
    help_handler = CommandHandler("help", help)
    app.add_handler(help_handler)

    #INSTA HANDLER
    insta_handler = CommandHandler("instasplit", instasplit)
    app.add_handler(insta_handler)

    app.run_polling()

if __name__ == "__main__":
    main()

