from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext
import requests
from datetime import datetime
from deep_translator import GoogleTranslator
import os

# Dicionário para armazenar as preferências de idioma dos usuários
user_language_preferences = {}

LANGUAGE_TO_MARKET = {
    'pt': 'pt-BR',
    'en': 'en-US',
    'es': 'es-ES'
}

# Função para obter a imagem APOD da NASA para uma data específica
def get_apod(date=None):
    # Insira sua chave de API da NASA aqui
    api_key = os.environ['NASA_KEY']
    url = f'https://api.nasa.gov/planetary/apod?api_key={api_key}'
    if date:
        url += f'&date={date}'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        return None

# Função para enviar a imagem APOD da NASA para o usuário
def send_apod(update: Update, context: CallbackContext, date=None):
    chat_id = update.effective_chat.id
    user_language = user_language_preferences.get(chat_id, 'en')
    apod_data = get_apod(date)
    if apod_data:
        image_url = apod_data['url']
        title = apod_data['title']
        explanation = apod_data['explanation']
        date = apod_data['date']
        if user_language != 'en':
            title = GoogleTranslator(source='auto', target=user_language, ).translate(title)
            explanation = GoogleTranslator(source='auto', target=user_language, ).translate(explanation)
            date_text = ('Data')
            credits_text = ('Créditos')
        else:
            date_text = 'Date'
            credits_text = 'Copyright'
        caption = f'{title}'
        context.bot.send_photo(chat_id=chat_id, photo=image_url, caption=caption)
        text = f'{explanation}\n\n{date_text}: {date}\n{credits_text}: NASA'
        for i in range(0, len(text), 4000):
            context.bot.send_message(chat_id=chat_id, text=text[i:i+4000])
    else:
        context.bot.send_message(chat_id=chat_id, text='Desculpe, não consegui encontrar a imagem APOD da NASA para a data solicitada.')

# Função de retorno de chamada para lidar com o comando /space
def space_callback(update: Update, context: CallbackContext):
    date = None
    args = context.args
    if args:
        arg = args[0].lower()
        if arg == 'today' or arg == 'hoje':
            date = datetime.now().strftime('%Y-%m-%d')
        else:
            try:
                datetime.strptime(arg, '%d-%m-%Y')
                date = '-'.join(arg.split('-')[::-1])
            except ValueError:
                pass
    send_apod(update, context, date)

# Função de retorno de chamada para lidar com consultas de retorno de chamada de botões inline
def button_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    chat_id = query.message.chat_id
    data = query.data
    if data in ['en', 'es', 'pt']:
        user_language_preferences[chat_id] = data
        context.bot.answer_callback_query(callback_query_id=query.id, text=f'Idioma alterado para {data}')
    else:
        context.bot.answer_callback_query(callback_query_id=query.id)

# Função de retorno de chamada para lidar com o comando /start
def start_callback(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    message_text = "Por favor, escolha seu idioma preferido abaixo:"
    keyboard = [
        [InlineKeyboardButton("Inglês 🇬🇧", callback_data='en')],
        [InlineKeyboardButton("Espanhol 🇪🇸", callback_data='es')],
        [InlineKeyboardButton("Português 🇧🇷", callback_data='pt')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(chat_id=chat_id, text=message_text, reply_markup=reply_markup)

def button_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    chat_id = query.message.chat_id
    data = query.data
    if data in ['en', 'es', 'pt']:
        user_language_preferences[chat_id] = data
        context.bot.answer_callback_query(callback_query_id=query.id, text=f'Idioma alterado para {data}')
        if data == 'en':
            welcome_text = "Hello! I am Helias, a bot that can send you amazing space images provided by NASA. You can use the '/space' command to get the NASA APOD (Astronomy Picture of the Day) image. You can also use the '/space dd-mm-yyyy' command to get the NASA APOD image for a specific date. If you want to receive an astronomical news article, just use the /news command."
        elif data == 'es':
            welcome_text = "¡Hola! Soy Helias, un bot que puede enviarte imágenes increíbles del espacio proporcionadas por la NASA. Puedes usar el comando '/space' para obtener la imagen APOD (Astronomy Picture of the Day) de la NASA. También puedes usar el comando '/space dd-mm-yyyy' para obtener la imagen APOD de la NASA para una fecha específica. Si quieres recibir una noticia astronómica, solo usa el comando /news."
        else:
            welcome_text = "Olá! Eu sou a Helias, um bot que pode enviar-lhe imagens incríveis do espaço fornecidas pela NASA. Você pode usar o comando '/space' para obter a imagem APOD (Astronomy Picture of the Day) da NASA. Você também pode usar o comando '/space dd-mm-yyyy' para obter a imagem APOD da NASA para uma data específica. Caso queira receber uma notícia astronômica, basta utilizar o comando /news."
        context.bot.send_message(chat_id=chat_id, text=welcome_text)
    else:
        context.bot.answer_callback_query(callback_query_id=query.id)


#Busca as noticias para a galera
def news_callback(update: Update, context: CallbackContext) -> None:
    # Obtém o código de mercado correspondente ao idioma escolhido pelo usuário
    user_id = update.message.from_user.id
    language = user_language_preferences.get(user_id, 'en')
    market = LANGUAGE_TO_MARKET.get(language, 'en-US')

    # Faz uma requisição à API do Bing News Search para obter notícias relacionadas à astronomia
    headers = {'Ocp-Apim-Subscription-Key': os.environ['BING_KEY']}
    params = {'q': 'astronomy, astronomía, astronomia', 'count': 1, 'mkt': market}
    response = requests.get('https://api.bing.microsoft.com/v7.0/news/search', headers=headers, params=params)
    data = response.json()

    # Verifica se há resultados disponíveis
    if 'value' in data and len(data['value']) > 0:
        # Obtém o primeiro resultado da pesquisa
        result = data['value'][0]

        # Extrai informações como o título da notícia, o URL e o snippet
        title = result['name']
        url = result['url']
        snippet = result['description']

        # Cria uma mensagem formatada para o usuário
        message = f'🔭 *{title}*\n{snippet}'

        # Adiciona um botão para ler a notícia na íntegra
        keyboard = [[InlineKeyboardButton('Leia na íntegra', url=url)]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Envia a mensagem para o usuário
        update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        # Caso não haja resultados disponíveis, envia uma mensagem informando ao usuário
        update.message.reply_text('Desculpe, não encontrei nenhuma notícia relacionada à astronomia no momento.')
#main
def main():
    updater = Updater(os.environ['BOT_TOKEN'])
    dp = updater.dispatcher
    dp.add_handler(CommandHandler('start', start_callback))
    dp.add_handler(CommandHandler('space', space_callback))
    dp.add_handler(CommandHandler('news', news_callback))
    dp.add_handler(CallbackQueryHandler(button_callback))
    updater.start_polling()
    updater.idle()
if __name__ == '__main__':
    main()
	
