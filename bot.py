import telebot
import sqlite3
import io


from telebot import types

bot = telebot.TeleBot('6772599133:AAE-HuGF4SpzlSzbWWygjjN7b8AzHb2d5VE')




# ID do usuario correto
correct_user_id = 24669

# Ciando teclado após o inicio
def create_start_keyboard():
    keyboard = types.ReplyKeyboardMarkup(row_width=2, one_time_keyboard=True, resize_keyboard=True)
    button_start_training = types.KeyboardButton('Começar o treino')
    button_view_progress = types.KeyboardButton('Ver o progresso dos treinos')
    keyboard.add(button_start_training, button_view_progress)
    return keyboard



def create_view_keyboard():
    keyboard = types.ReplyKeyboardMarkup(row_width=1, one_time_keyboard=True, resize_keyboard=True)
    button_choose_segunda = types.KeyboardButton('Segunda Feira')
    button_choose_terca = types.KeyboardButton('Terca Feira')
    button_choose_quarta = types.KeyboardButton('Quarta Feira')
    button_choose_quinta = types.KeyboardButton('Quinta Feira')
    button_choose_sexta = types.KeyboardButton('Sexta Feira')
    button_choose_sabado = types.KeyboardButton('Sabado')

    keyboard.add(button_choose_segunda, button_choose_terca, button_choose_quarta, button_choose_quinta, button_choose_sexta, button_choose_sabado)
    return keyboard

def choose_bodypart_keyboard():
    keyboard = types.ReplyKeyboardMarkup(row_width=1, one_time_keyboard=True, resize_keyboard=True)
    button_peito_tricep = types.KeyboardButton('Peito & Triceps')
    button_costas_biceps = types.KeyboardButton("Costas & Biceps")
    button_perna = types.KeyboardButton('Perna')

    keyboard.add(button_peito_tricep, button_costas_biceps, button_perna)
    return keyboard

# Verificação do ID do usuário no início
@bot.message_handler(commands=['start', 'hello'])
def start(message):

    bot.send_message(message.chat.id, 'Por favor, insira seu identificador de usuário:')
    bot.register_next_step_handler(message, verify_user_id)


def verify_user_id(message):
    try:
        user_id = int(message.text)

        if user_id != correct_user_id:
            bot.reply_to(message, 'Identificador de usuário incorreto. Você não tem permissão para usar este bot.')
            return

        bot.send_message(message.chat.id, 'Olá, eu sou um bot que vai te ajudar com seus treinos feito pelo Ivan!',
                         reply_markup=create_start_keyboard())
    except ValueError:
        bot.reply_to(message, 'Por favor, insira um identificador de usuário válido (número inteiro).')

# Após carregar "Começar o treino"
@bot.message_handler(func=lambda message: message.text == 'Começar o treino')
def start_training(message):
    bot.send_message(message.chat.id, 'Ótimo! Escolha o dia da semana para o treino:',
                     reply_markup=create_view_keyboard())

# Após carregar o dia da semana
@bot.message_handler(func=lambda message: message.text in ['Segunda Feira', 'Terca Feira', 'Quarta Feira', 'Quinta Feira', 'Sexta Feira', 'Sabado'])
def choose_bodypart_after_day(message):
    chosen_day = message.text
    bot.send_message(message.chat.id, f'Você escolheu o treino para {chosen_day}. Escolha a parte do corpo que deseja treinar:',
                     reply_markup=choose_bodypart_keyboard())

# Adicione um novo manipulador para a escolha da parte do corpo
@bot.message_handler(func=lambda message: message.text in ['Peito & Triceps', 'Costas & Biceps', 'Perna'])
def choose_bodypart(message):
    conn = sqlite3.connect('planosdetreinos.db')
    cur = conn.cursor()

    chosen_bodypart = message.text
    bot.send_message(message.chat.id, f'Você escolheu treinar {chosen_bodypart}. Aqui está o plano de treino:')

    # Determine the workout category based on the numeric input
    encontraroplano = {'Peito & Triceps': 'PeitoTricep', 'Costas & Biceps': 'CostasBiceps', 'Perna': 'Perna'} 
    workout_category = encontraroplano.get(chosen_bodypart)

    # Fetch the workout list for the specific category
    cur.execute(f"SELECT nome, sets, repeticoes, imagem_url FROM {workout_category}")
    workout_list = cur.fetchall()

    for exercise, sets, repeticoes, image_url in workout_list:
        workout_info = f'{exercise}: {sets} sets, {repeticoes} reps'
        image_path = f'./pics/{image_url}'  # Caminho relativo, ajuste conforme necessário

        # Crie um teclado inline com um botão que contém o nome do exercício como callback data
        keyboard = types.InlineKeyboardMarkup()
        button = types.InlineKeyboardButton(text='Apontar', callback_data=f'apontamento_{exercise}')
        keyboard.add(button)

        # Envie a foto, mensagem e teclado inline
        with open(image_path, 'rb') as image_file:
            image_buffer = io.BytesIO(image_file.read())
            bot.send_photo(message.chat.id, image_buffer, caption=workout_info, reply_markup=keyboard)

    cur.close()
    conn.close()


@bot.callback_query_handler(func=lambda call: call.data.startswith('apontamento_'))
def prompt_for_details(call):
    exercise_name = call.data[len('apontamento_'):]
    
    # Cria um teclado inline para inserir o peso e o número de sets
    keyboard = types.InlineKeyboardMarkup()
    button = types.InlineKeyboardButton(text='Registrar Apontamento', callback_data=f'registrar_{exercise_name}')
    keyboard.add(button)

    # Envia a mensagem com o novo teclado inline
    bot.send_message(call.message.chat.id, 'Toque no botão "Registrar Apontamento" para inserir o peso e as séries.', reply_markup=keyboard)

    # Responde ao callback query para fechar o aviso de processamento
    bot.answer_callback_query(callback_query_id=call.id)

# Adiciona um manipulador de callback para processar o clique no botão "Registrar Apontamento"
@bot.callback_query_handler(func=lambda call: call.data.startswith('registrar_'))
def log_exercise_prompt(call):
    # Extrai as informações de callback data
    _, exercise_name = call.data.split('_')
    
    # Cria um teclado inline para inserir o peso e o número de sets
    keyboard = types.InlineKeyboardMarkup()
    button = types.InlineKeyboardButton(text='Cancelar', callback_data=f'cancelar_{exercise_name}')
    keyboard.add(button)

    # Envia a mensagem com o novo teclado inline
    bot.send_message(call.message.chat.id, 'Por favor, insira o peso e o número de sets separados por espaço (exemplo: "70 3").', reply_markup=keyboard)

    # Responde ao callback query para fechar o aviso de processamento
    bot.answer_callback_query(callback_query_id=call.id)

# Adiciona um manipulador de mensagem para processar o peso e o número de sets inseridos pelo usuário
@bot.message_handler(func=lambda message: message.text.startswith('Cancelar'))
def cancel_log_exercise(message):
    bot.send_message(message.chat.id, 'Apontamento cancelado.')

# Adiciona um manipulador de mensagem para processar o peso e o número de sets inseridos pelo usuário
@bot.message_handler(func=lambda message: message.text.startswith('Cancelar'))
def cancel_log_exercise(message):
    bot.send_message(message.chat.id, 'Apontamento cancelado.')

# Adiciona um manipulador de mensagem para processar o peso e o número de sets inseridos pelo usuário
@bot.message_handler(func=lambda message: message.text.startswith('/apontamento_'))
def log_exercise(message):
    # Extrai as informações inseridas pelo usuário
    _, exercise_name, data = message.text.split('_')
    weight, sets = map(int, data.split())

    # Aqui você pode inserir essas informações em uma tabela específica no SQLite3
    # Certifique-se de adaptar isso conforme necessário para a sua estrutura de banco de dados
    conn = sqlite3.connect('log_exercicios.db')
    cur = conn.cursor()
    
    # Exemplo de inserção em uma tabela de log
    cur.execute("INSERT INTO log_exercicios (nome_exercicio, peso, sets) VALUES (?, ?, ?)", (exercise_name, weight, sets))
    conn.commit()
    
    cur.close()
    conn.close()

    # Responde ao usuário
    bot.send_message(message.chat.id, f'Você registrou {weight} kg para {sets} sets em {exercise_name}.')

 
bot.polling(none_stop=True)
