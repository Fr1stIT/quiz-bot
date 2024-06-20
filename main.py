import asyncio
import datetime

from aiogram import Bot, Dispatcher, F, types
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from conf import BOT_API, db_params
from aiogram.filters.command import Command
from db import Database
from states import *
from aiogram.filters import CommandStart, CommandObject
import kb

bot = Bot(token=BOT_API)
dp = Dispatcher()

db = Database(db_params)

superadmin = 1061467560

async def main():
    await dp.start_polling(bot)

@dp.message(CommandStart(deep_link=True))
async def handler(message: Message, command: CommandObject, state: FSMContext):
    quiz_id = command.args
    print(f'Переход по ссылке с аргументом: {quiz_id}')
    duration = db.get_quiz_duration(quiz_id)
    await message.answer(f'Вы запустили квиз <b>{db.get_quiz_name(quiz_id)}</b>', parse_mode='html')
    await state.update_data(quiz_id=quiz_id, question_index=0, start_time=datetime.datetime.now(), correct_answers=0,
                            duration=duration, questions=db.get_quiz_questions(quiz_id))
    await send_next_question(message, state)


@dp.message(F.text == 'Ссылки на квизы')
async def generate_quiz_links(message: types.Message):
    user_id = message.from_user.id
    if not db.is_admin(user_id):
        await message.reply("Вы не имеете прав для выполнения этой команды.")
        return

    quizzes = db.get_all_quizzes()

    if quizzes:
        response = "🔖 Доступные квизы:\n"
        for quiz in quizzes:
            quiz_id = quiz[0]
            quiz_name = quiz[1]
            link = f"https://t.me/frist_kahoot_bot?start={quiz_id}"
            response += f"📃 {quiz_name}: \n🔗 {link}\n"
        await message.reply(response)
    else:
        await message.reply("No quizzes found or an error occurred.")


@dp.message(Command('start'))
async def strt_command(message: Message):
    if message.from_user.id == superadmin:
        await message.answer( ' 🦸 Вы супер администратор!', reply_markup=kb.admin_main_kb)
    else:
        if db.is_admin(user_id=message.from_user.id):
            await message.answer('✅ Вы вошли как администратор!', reply_markup=kb.admin_main_kb)
        else:
            username = db.get_username(message.from_user.id)
            if username:
                await message.answer(f'✅ Вы вошли в систему под аккаунтом <b>{username}</b>', reply_markup=kb.main_kb, parse_mode='html')
            else:
                if not db.is_user_in_blacklist(message.from_user.id):
                    if db.add_user(user_id=message.from_user.id, user_name=message.from_user.username, is_admin=False, quantity_of_kahoots=0):
                        await message.answer(f'✅ Вы были успешно добавлены в систему с ником <b>{message.from_user.username}</b>', parse_mode='html')
                else:
                    await message.answer('❌ Вы заблокированы и не можете войти в систему.')
########################################################################################################################
@dp.message(F.text == 'Изменить свое имя')
async def admin_func_com(message: Message, state: FSMContext):
    user_id = message.from_user.id
    await state.update_data(user_id=user_id)
    await message.answer(f'🛠 Укажите новое имя пользователя')
    await state.set_state(Change_Username.wait_for_username)

@dp.message(F.text == 'Функции администратора')
async def admin_func_com(message: Message):
    if message.from_user.id == superadmin:
        await message.answer('🛠 Вы открыли функции супер администратора!', reply_markup=kb.superadmin_func_kb)
    elif db.is_admin(message.from_user.id):
        await message.answer('🛠 Вы открыли функции администратора!', reply_markup=kb.admin_func_kb)


@dp.message(F.text == 'Назначить администратора')
async def admin_set(message: Message, state: FSMContext):
    await message.answer('Выберите игрока', reply_markup=kb.generate_paginated_buttons(db.get_non_admin_users(), 0))
    await state.set_state(AddAdmin.wait_for_user_id)

@dp.callback_query(AddAdmin.wait_for_user_id, lambda c: c.data and c.data.startswith('page_'))
async def process_callback_page(callback_query: types.CallbackQuery, state: FSMContext):
    page = int(callback_query.data.split('_')[1])
    template_orders = db.get_non_admin_users()

    keyboard = kb.generate_paginated_buttons(template_orders, page)

    await bot.edit_message_reply_markup(callback_query.message.chat.id,
                                        callback_query.message.message_id,
                                        reply_markup=keyboard)

@dp.callback_query(AddAdmin.wait_for_user_id, lambda c: not c.data.startswith('page_'))
async def process_callback_select(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = int(callback_query.data.split('_')[1])
    await state.update_data(user_id = user_id)
    username = db.get_username(user_id)
    await callback_query.message.answer(f'⚠ Вы собираетесь назначить администратором пользователя <b>{username}</b>', parse_mode='html', reply_markup=kb.generate_verif_buttons())
    await callback_query.answer('')
    await state.set_state(AddAdmin.confirm)


@dp.callback_query(AddAdmin.confirm)
async def confirm_add_admin(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.data == 'yes':
        data = await state.get_data()
        db.make_admin(data['user_id'])
        await callback_query.message.answer('✅ Пользователь был успешно назначен администратором!')
        await callback_query.answer('')
        await state.clear()
    else:
        await callback_query.message.answer('❌ Отменено')
        await callback_query.answer('')
        await state.clear()


@dp.message(F.text == 'Заблокировать игрока')
async def admin_func_com(message: Message, state: FSMContext):
    await message.answer('💁 Выберите игрока', reply_markup=kb.generate_paginated_buttons(db.get_non_admin_users(), 0))
    await state.set_state(AddToBlackList.wait_for_user_id)


@dp.callback_query(AddToBlackList.wait_for_user_id, lambda c: c.data and c.data.startswith('page_'))
async def process_callback_page(callback_query: types.CallbackQuery, state: FSMContext):
    page = int(callback_query.data.split('_')[1])
    template_orders = db.get_non_admin_users()

    keyboard = kb.generate_paginated_buttons(template_orders, page)

    await bot.edit_message_reply_markup(callback_query.message.chat.id,
                                        callback_query.message.message_id,
                                        reply_markup=keyboard)


@dp.callback_query(AddToBlackList.wait_for_user_id, lambda c: not c.data.startswith('page_'))
async def process_callback_select(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = int(callback_query.data.split('_')[1])
    await state.update_data(user_id=user_id)
    username = db.get_username(user_id)
    await callback_query.message.answer(f'⚠ Вы собираетесь заблокировать пользователя <b>{username}</b>',
                                        parse_mode='html', reply_markup=kb.generate_verif_buttons())
    await callback_query.answer('')
    await state.set_state(AddToBlackList.confirm)



@dp.callback_query(AddToBlackList.confirm)
async def confirm_add_admin(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.data == 'yes':
        data = await state.get_data()
        db.add_user_to_blacklist(data['user_id'])
        db.delete_user(data['user_id'])
        await callback_query.message.answer('✅ Пользователь был успешно заблокирован!')
        await callback_query.answer('')
        await state.clear()
    else:
        await callback_query.message.answer('❌ Отменено')
        await callback_query.answer('')
        await state.clear()


@dp.message(F.text == 'Изменить чужое имя')
async def admin_func_com(message: Message, state: FSMContext):
    await message.answer('💁 Выберите игрока', reply_markup=kb.generate_paginated_buttons(db.get_non_admin_users(), 0))
    await state.set_state(Change_Username.wait_for_user_id)


@dp.callback_query(Change_Username.wait_for_user_id, lambda c: c.data and c.data.startswith('page_'))
async def process_callback_page(callback_query: types.CallbackQuery, state: FSMContext):
    page = int(callback_query.data.split('_')[1])
    template_orders = db.get_non_admin_users()

    keyboard = kb.generate_paginated_buttons(template_orders, page)

    await bot.edit_message_reply_markup(callback_query.message.chat.id,
                                        callback_query.message.message_id,
                                        reply_markup=keyboard)


@dp.callback_query(Change_Username.wait_for_user_id, lambda c: not c.data.startswith('page_'))
async def process_callback_select(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = int(callback_query.data.split('_')[1])
    await state.update_data(user_id=user_id)
    await callback_query.message.answer(f'🛠 Укажите новое имя пользователя')
    await callback_query.answer('')
    await state.set_state(Change_Username.wait_for_username)

@dp.message(Change_Username.wait_for_username)
async def admin_func_com(message: Message, state: FSMContext):
    await state.update_data(username=message.text)
    data = await state.get_data()
    username = db.get_username(data['user_id'])
    await message.answer(f'⚠ Вы собираетесь сменить имя пользователя у <b>{username}</b> на <b>{message.text}</b>',
                                        parse_mode='html', reply_markup=kb.generate_verif_buttons())
    await state.set_state(Change_Username.confirm)




@dp.callback_query(Change_Username.confirm)
async def confirm_add_admin(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.data == 'yes':
        data = await state.get_data()
        db.update_username(data['user_id'], data['username'])
        await callback_query.message.answer('✅ Пользователь был изменен!')
        await callback_query.answer('')
        await state.clear()
    else:
        await callback_query.message.answer('❌ Отменено')
        await callback_query.answer('')
        await state.clear()
########################################################################################################################
@dp.message(F.text == 'Добавить квиз')
async def admin_func_com(message: Message, state: FSMContext):
    if message.from_user.id == superadmin or db.is_admin(message.from_user.id):
        await message.reply("🛠 Введите имя квиза:")
        await state.set_state(AddQuizForm.quiz_name)


@dp.message(AddQuizForm.quiz_name)
async def admin_func_com(message: Message, state: FSMContext):
    if message.from_user.id == superadmin or db.is_admin(message.from_user.id):
        await state.update_data(quiz_name=message.text)
        await message.reply('🛠 Введите длительность прохождения квиза:  ')
        await state.set_state(AddQuizForm.quiz_duration)


@dp.message(AddQuizForm.quiz_duration)
async def admin_func_com(message: Message, state: FSMContext):
    if message.from_user.id == superadmin or db.is_admin(message.from_user.id):
        await state.update_data(quiz_duration=int(message.text))
        await message.reply('🛠 Введите количество вопросов в квизе:  ')
        await state.set_state(AddQuizForm.num_questions)

@dp.message(AddQuizForm.num_questions)
async def admin_func_com(message: Message, state: FSMContext):
    if message.from_user.id == superadmin or db.is_admin(message.from_user.id):
        num_questions = int(message.text)
        await state.update_data(num_questions=num_questions, question_index=1)
        data = await state.get_data()
        quiz_id = db.add_quiz(data['quiz_name'], message.from_user.id, data['quiz_duration'])
        await state.update_data(current_quiz_id=quiz_id)
        await message.answer('🛠 Введите текст вопроса: ')
        await state.set_state(AddQuizForm.question_text)


@dp.message(AddQuizForm.question_text)
async def admin_func_com(message: Message, state: FSMContext):
    if message.from_user.id == superadmin or db.is_admin(message.from_user.id):
        data = await state.get_data()
        question_id = db.add_question(data['current_quiz_id'], message.text)
        await state.update_data(question_text=message.text, current_question_id=question_id, answer_index=0)
        await message.reply('🛠 Введите текст ответа: ')
        await state.set_state(AddQuizForm.answer_text)


@dp.message(AddQuizForm.answer_text)
async def admin_func_com(message: Message, state: FSMContext):
    if message.from_user.id == superadmin or db.is_admin(message.from_user.id):
        await state.update_data(answer_text=message.text)
        await message.answer('🛠 Этот ответ верный? (да/нет)')
        await state.set_state(AddQuizForm.is_correct)

@dp.message(AddQuizForm.is_correct)
async def admin_func_com(message: Message, state: FSMContext):
    if message.from_user.id == superadmin or db.is_admin(message.from_user.id):
        is_correct = message.text.lower() in ['верно', 'да', 'д']
        data = await state.get_data()
        db.add_answer(data['current_question_id'], data['answer_text'], is_correct)
        await state.update_data(answer_index=data['answer_index']+1)
        data = await state.get_data()
        if data['answer_index'] < 4:
            await message.reply(f"🛠 Введите текст {data['answer_index'] + 1}-го варианта ответа:")
            await state.set_state(AddQuizForm.answer_text)
        else:

            if data['question_index'] < data['num_questions']:
                await state.update_data(question_index=data['question_index'] + 1)
                await message.reply(f"🛠 Введите текст {data['question_index'] + 1}-го вопроса:")
                await state.set_state(AddQuizForm.question_text)
            else:
                await state.clear()
                await message.reply("✅ Квиз успешно добавлен.")
########################################################################################################################
@dp.message(F.text == 'Пройти квиз')
async def list_quizzes(message: types.Message):
    quizzes = db.get_all_quizzes()
    await message.reply("💠 Доступные квизы:", reply_markup=kb.generate_quiz_buttons(quizzes))


@dp.callback_query(lambda c: c.data and c.data.startswith('quiz_'))
async def start_quiz(callback_query: types.CallbackQuery, state: FSMContext):
    quiz_id = int(callback_query.data.split('_')[1])
    duration = db.get_quiz_duration(quiz_id)
    await state.update_data(quiz_id=quiz_id, question_index=0, start_time=datetime.datetime.now(), correct_answers=0, duration=duration, questions=db.get_quiz_questions(quiz_id))
    await send_next_question(callback_query.message, state)



@dp.callback_query(lambda c: c.data and c.data.startswith('answer_'))
async def process_answer(callback_query: types.CallbackQuery, state: FSMContext):
    answer_id = int(callback_query.data.split('_')[1])
    data = await state.get_data()
    answers = db.get_question_answers(data['question_id'])
    correct_answer = next(answer for answer in answers if answer[2])

    if correct_answer[0] == answer_id:
        await state.update_data(correct_answers=data['correct_answers']+1)

    await state.update_data(question_index=data['question_index']+1)

    current_time = datetime.datetime.now()
    elapsed_time = (current_time - data['start_time']).seconds

    if elapsed_time > data['duration'] * 60:
        await end_quiz(callback_query.message, state)
    else:
        await send_next_question(callback_query.message, state)


########################################################################################################################

async def end_quiz(message: types.Message, state: FSMContext):
    data = await state.get_data()
    total_questions = len(data['questions'])
    correct_answers = data['correct_answers']

    await message.answer(

        f"🎉 Квиз завершен! Ваш результат: {correct_answers}/{total_questions} правильных ответов."
    )
    await state.clear()


async def send_next_question(message: types.Message, state: FSMContext):
    data = await state.get_data()
    if data['question_index'] < len(data['questions']):
        question = data['questions'][data['question_index']]
        await state.update_data(question_id=question[0])
        answers = db.get_question_answers(question[0])

        await message.edit_text(question[1], reply_markup=kb.generate_answer_buttons(answers))

    else:
        await end_quiz(message, state)

if __name__ == '__main__':
    asyncio.run(main())