from aiogram.fsm.state import StatesGroup, State

class AddAdmin(StatesGroup):
    wait_for_user_id = State()
    confirm = State()

class AddToBlackList(StatesGroup):
    wait_for_user_id = State()
    confirm = State()

class Change_Username(StatesGroup):
    wait_for_user_id = State()
    wait_for_username = State()
    confirm = State()

class AddQuizForm(StatesGroup):
    quiz_name = State()
    quiz_duration = State()
    num_questions = State()
    question_text = State()
    answer_text = State()
    is_correct = State()
    question_index = State()
    answer_index = State()
    current_quiz_id = State()
    current_question_id = State()


class QuizForm(StatesGroup):
    quiz_id = State()
    question_index = State()
    start_time = State()
    correct_answers = State()
    question_id = State()
