from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

main_kb_button = [
    [KeyboardButton(text='Пройти квиз')],
    [KeyboardButton(text='Изменить свое имя')]
]

main_kb = ReplyKeyboardMarkup(keyboard=main_kb_button, resize_keyboard=True)

########################################################################################################################

admin_main_kb_button = [
    [KeyboardButton(text='Пройти квиз')],
    [KeyboardButton(text='Изменить свое имя')],
    [KeyboardButton(text='Функции администратора')]
]

admin_main_kb = ReplyKeyboardMarkup(keyboard=admin_main_kb_button, resize_keyboard=True)

admin_func_kb_button = [
    [KeyboardButton(text='Добавить квиз'), KeyboardButton(text='Ссылки на квизы')],
    [KeyboardButton(text='Заблокировать игрока')],
    [KeyboardButton(text='Изменить чужое имя')],
]

admin_func_kb = ReplyKeyboardMarkup(keyboard=admin_func_kb_button, resize_keyboard=True)

superadmin_func_kb_button = [
    [KeyboardButton(text='Добавить квиз'), KeyboardButton(text='Ссылки на квизы')],
    [KeyboardButton(text='Заблокировать игрока')],
    [KeyboardButton(text='Изменить чужое имя')],
    [KeyboardButton(text='Назначить администратора')]
]

superadmin_func_kb = ReplyKeyboardMarkup(keyboard=superadmin_func_kb_button, resize_keyboard=True)


def generate_paginated_buttons(template_orders, page):
    items_per_page = 5
    start = page * items_per_page
    end = min(start + items_per_page, len(template_orders))
    total_pages = (len(template_orders) + items_per_page - 1) // items_per_page

    buttons = []
    for order in template_orders[start:end]:
        button = InlineKeyboardButton(text=order[1], callback_data=f"id_{order[0]}")
        buttons.append([button])

    navigation_buttons = []
    if page > 0:
        navigation_buttons.append(InlineKeyboardButton(text="⬅️ Previous", callback_data=f"page_{page - 1}"))
    if page < total_pages - 1:
        navigation_buttons.append(InlineKeyboardButton(text="Next ➡️", callback_data=f"page_{page + 1}"))

    if navigation_buttons:
        buttons.append(navigation_buttons)

    return InlineKeyboardMarkup(inline_keyboard=buttons)



def generate_verif_buttons():
    kb_button = [
        [InlineKeyboardButton(text='Подтвердить ✅', callback_data='yes')],
        [InlineKeyboardButton(text='Отмена ❌', callback_data='no')]
    ]
    kb = InlineKeyboardMarkup(inline_keyboard=kb_button)
    return kb


# def generate_answer_buttons(quiz_data):
#     if quiz_data:
#         for question, answers in quiz_data.items():
#             keyboard = [
#                 [InlineKeyboardButton(answer['answer_text'],
#                                       callback_data=f"{answer['answer_id']}:{'correct' if answer['is_correct'] else 'wrong'}")]
#                 for answer in answers
#             ]
#         reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
#         return reply_markup

def generate_quiz_buttons(quizzes):
    if quizzes:
        keyboard = []
        for quiz in quizzes:
            button_text = f"{quiz[1]} (Длительность: {quiz[2]} минут)"
            button = InlineKeyboardButton(text=button_text, callback_data=f"quiz_{quiz[0]}")
            keyboard.append([button])

        reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        return reply_markup



def generate_answer_buttons(answers):
    keyboard = [
        [InlineKeyboardButton(text=answer[1], callback_data=f"answer_{answer[0]}")]
        for answer in answers
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    return reply_markup