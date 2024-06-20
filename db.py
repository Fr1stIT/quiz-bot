import psycopg2
import logging
from psycopg2 import Error

class Database:
    def __init__(self, db_params: dict = None):
        if db_params is None:
            db_params = {
                "host": "localhost",
                "database": "Employe",
                "user": "postgres",
                "password": "7292",
                "port": "5432"
            }

        try:
            self.connection = psycopg2.connect(**db_params)
            self.cursor = self.connection.cursor()
            self.create_tables()
        except Error as e:
            logging.error(f"Error while connecting to PostgreSQL: {e}")

    def create_tables(self):
        try:
            create_users_table_query = """CREATE TABLE IF NOT EXISTS users (
                                               user_id BIGINT PRIMARY KEY,
                                               user_name TEXT,
                                               is_admin BOOLEAN,
                                               quantity_of_kahoots INT
                                           )"""
            create_blacklist_table_query = """CREATE TABLE IF NOT EXISTS black_list (
                                                   user_id BIGINT PRIMARY KEY
                                               )"""

            create_quizzes_table_query = """CREATE TABLE IF NOT EXISTS quizzes (
                                                           quiz_id SERIAL PRIMARY KEY,
                                                           quiz_name VARCHAR(255) NOT NULL,
                                                           created_by INTEGER REFERENCES users(user_id),
                                                           duration INT NOT NULL
                                                       )"""
            create_questions_table_query = """CREATE TABLE IF NOT EXISTS questions (
                                                question_id SERIAL PRIMARY KEY,
                                                quiz_id INTEGER REFERENCES quizzes(quiz_id),
                                                question_text TEXT NOT NULL
                                            )"""
            create_answers_table_query = """CREATE TABLE IF NOT EXISTS answers (
                                                answer_id SERIAL PRIMARY KEY,
                                                question_id INTEGER REFERENCES questions(question_id),
                                                answer_text TEXT NOT NULL,
                                                is_correct BOOLEAN NOT NULL
                                            )"""

            self.cursor.execute(create_users_table_query)
            self.cursor.execute(create_blacklist_table_query)
            self.cursor.execute(create_quizzes_table_query)
            self.cursor.execute(create_questions_table_query)
            self.cursor.execute(create_answers_table_query)
            self.connection.commit()
            logging.info("Tables created successfully.")
        except Error as e:
            logging.error(f"Error while creating tables: {e}")

    def add_user(self, user_id, user_name, is_admin, quantity_of_kahoots):
        try:
            query = """INSERT INTO users (user_id, user_name, is_admin, quantity_of_kahoots)
                       VALUES (%s, %s, %s, %s)"""
            self.cursor.execute(query, (user_id, user_name, is_admin, quantity_of_kahoots))
            self.connection.commit()
            logging.info(f"User {user_name} added successfully.")
        except Error as e:
            logging.error(f"Error while adding user: {e}")
            self.connection.rollback()

    def is_admin(self, user_id):
        try:
            query = "SELECT is_admin FROM users WHERE user_id = %s"
            self.cursor.execute(query, (user_id,))
            result = self.cursor.fetchone()
            if result:
                return result[0]
            else:
                logging.error(f"User with ID {user_id} not found.")
                return False
        except Error as e:
            logging.error(f"Error while checking admin status: {e}")
            return None

    def get_username(self, user_id):
        try:
            query = "SELECT user_name FROM users WHERE user_id = %s"
            self.cursor.execute(query, (user_id,))
            result = self.cursor.fetchone()
            if result:
                return result[0]
            else:
                logging.error(f"User with ID {user_id} not found.")
                return None
        except Error as e:
            logging.error(f"Error while retrieving username: {e}")
            return None

    def close(self):
        if self.connection:
            self.cursor.close()
            self.connection.close()
            logging.info("PostgreSQL connection is closed.")

    def get_non_admin_users(self):
        try:
            query = "SELECT * FROM users WHERE is_admin = FALSE"
            self.cursor.execute(query)
            users = self.cursor.fetchall()
            return users
        except Error as e:
            logging.error(f"Error while fetching non-admin users: {e}")
            return None

    def make_admin(self, user_id):
        try:
            query = "UPDATE users SET is_admin = TRUE WHERE user_id = %s"
            self.cursor.execute(query, (user_id,))
            self.connection.commit()
            if self.cursor.rowcount > 0:
                logging.info(f"User with ID {user_id} has been made an admin.")
            else:
                logging.error(f"No user found with ID {user_id}.")
        except Error as e:
            logging.error(f"Error while making user an admin: {e}")
            self.connection.rollback()

    def is_user_in_blacklist(self, user_id):
        try:
            query = "SELECT 1 FROM black_list WHERE user_id = %s"
            self.cursor.execute(query, (user_id,))
            return self.cursor.fetchone() is not None
        except Error as e:
            logging.error(f"Error while checking blacklist status: {e}")
            return False

    def add_user_to_blacklist(self, user_id):
        try:
            query = "INSERT INTO black_list (user_id) VALUES (%s)"
            self.cursor.execute(query, (user_id,))
            self.connection.commit()
            logging.info(f"User with ID {user_id} has been added to the blacklist.")
            return True
        except Error as e:
            logging.error(f"Error while adding user to blacklist: {e}")
            self.connection.rollback()
            return False

    def delete_user(self, user_id):
        try:
            query = "DELETE FROM users WHERE user_id = %s"
            self.cursor.execute(query, (user_id,))
            self.connection.commit()
            if self.cursor.rowcount > 0:
                logging.info(f"User with ID {user_id} has been deleted.")
                return True
            else:
                logging.error(f"No user found with ID {user_id}.")
                return False
        except Error as e:
            logging.error(f"Error while deleting user: {e}")
            self.connection.rollback()
            return False

    def update_username(self, user_id, new_username):
        try:
            query = "UPDATE users SET user_name = %s WHERE user_id = %s"
            self.cursor.execute(query, (new_username, user_id))
            self.connection.commit()
            if self.cursor.rowcount > 0:
                logging.info(f"User with ID {user_id} has been updated with new username {new_username}.")
                return True
            else:
                logging.error(f"No user found with ID {user_id}.")
                return False
        except Error as e:
            logging.error(f"Error while updating username: {e}")
            self.connection.rollback()
            return False

    def get_quiz(self, quiz_id):
        try:
            query = """
                SELECT q.question_text, a.answer_id, a.answer_text, a.is_correct 
                FROM questions q 
                JOIN answers a ON q.question_id = a.question_id 
                WHERE q.quiz_id = %s
            """
            self.cursor.execute(query, (quiz_id,))
            quiz_data = {}
            for row in self.cursor.fetchall():
                question_text = row[0]
                if question_text not in quiz_data:
                    quiz_data[question_text] = []
                quiz_data[question_text].append({
                    'answer_id': row[1],
                    'answer_text': row[2],
                    'is_correct': row[3]
                })
            return quiz_data
        except Error as e:
            logging.error(f"Error while retrieving quiz: {e}")
            return None



    def add_quiz(self, quiz_name, admin_id, duration):
        try:
            query = "INSERT INTO quizzes (quiz_name, created_by, duration) VALUES (%s, %s, %s) RETURNING quiz_id"
            self.cursor.execute(query, (quiz_name, admin_id, duration))
            quiz_id = self.cursor.fetchone()[0]
            self.connection.commit()
            return quiz_id
        except Error as e:
            logging.error(f"Error while adding quiz: {e}")
            self.connection.rollback()
            return None

    def add_question(self, quiz_id, question_text):
        try:
            query = "INSERT INTO questions (quiz_id, question_text) VALUES (%s, %s) RETURNING question_id"
            self.cursor.execute(query, (quiz_id, question_text))
            question_id = self.cursor.fetchone()[0]
            self.connection.commit()
            return question_id
        except Error as e:
            logging.error(f"Error while adding question: {e}")
            self.connection.rollback()
            return None

    def add_answer(self, question_id, answer_text, is_correct):
        try:
            query = "INSERT INTO answers (question_id, answer_text, is_correct) VALUES (%s, %s, %s)"
            self.cursor.execute(query, (question_id, answer_text, is_correct))
            self.connection.commit()
        except Error as e:
            logging.error(f"Error while adding answer: {e}")
            self.connection.rollback()

    def get_all_quizzes(self):
        try:
            query = "SELECT quiz_id, quiz_name, duration FROM quizzes"
            self.cursor.execute(query)
            quizzes = self.cursor.fetchall()
            return quizzes
        except Error as e:
            logging.error(f"Error while retrieving quizzes: {e}")
            return None

    def get_quiz_duration(self, quiz_id):
        try:
            query = "SELECT duration FROM quizzes WHERE quiz_id = %s"
            self.cursor.execute(query, (quiz_id,))
            duration = self.cursor.fetchone()[0]
            return duration
        except Error as e:
            logging.error(f"Error while retrieving quiz duration: {e}")
            return None

    def get_quiz_questions(self, quiz_id):
        try:
            query = "SELECT question_id, question_text FROM questions WHERE quiz_id = %s"
            self.cursor.execute(query, (quiz_id,))
            questions = self.cursor.fetchall()
            return questions
        except Error as e:
            logging.error(f"Error while retrieving quiz questions: {e}")
            return None

    def get_question_answers(self, question_id):
        try:
            query = "SELECT answer_id, answer_text, is_correct FROM answers WHERE question_id = %s"
            self.cursor.execute(query, (question_id,))
            answers = self.cursor.fetchall()
            return answers
        except Error as e:
            logging.error(f"Error while retrieving question answers: {e}")
            return None

    def get_quiz_name(self, quiz_id):
        try:
            query = "SELECT quiz_name FROM quizzes WHERE quiz_id = %s"
            self.cursor.execute(query, (quiz_id,))
            result = self.cursor.fetchone()
            if result:
                return result[0]
            else:
                logging.error(f"Quiz with ID {quiz_id} not found.")
                return None
        except Error as e:
            logging.error(f"Error while retrieving quiz name: {e}")
            return None