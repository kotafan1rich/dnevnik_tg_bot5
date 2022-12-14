import sqlite3


class Database:
    def __init__(self, db_file):
        self.connection = sqlite3.connect(db_file)
        self.cursor = self.connection.cursor()

    def add_user(self, user_id):
        with self.connection:
            return self.cursor.execute("INSERT INTO `users` (`user_id`) VALUES (?)", (user_id,))

    def user_exists(self, user_id):
        with self.connection:
            result = self.cursor.execute("SELECT * FROM `users` WHERE `user_id` = ?", (user_id,)).fetchall()
            return bool(len(result))

    def set_login(self, user_id, login):
        with self.connection:
            return self.cursor.execute("UPDATE `users` SET `login` = ? WHERE `user_id` = ?", (login, user_id,))

    def set_password(self, user_id, password):
        with self.connection:
            return self.cursor.execute("UPDATE `users` SET `password` = ? WHERE `user_id` = ?", (password, user_id,))

    def get_login_and_password(self, user_id):
        with self.connection:
            result = self.cursor.execute("SELECT `login`, `password` FROM `users` WHERE `user_id` = ?", (user_id,)).fetchall()
            login = result[0][0]
            password = result[0][1]
            return [login, password]
