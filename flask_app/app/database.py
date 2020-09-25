from time import time

import psycopg2
from psycopg2 import sql


class Database:
    conn = None

    def __init__(self, config):
        conn = self.connect(config)
        if conn:
            self.conn = conn
        else:
            print("Нет подключения к БД")
            raise TypeError

    def __init_cursor(func):
        def the_wrapper_around_the_original_function(self, *args, **kwargs):
            cursor = None
            try:
                cursor = self.conn.cursor()
            except AttributeError:
                return "Нет подключения к БД"

            try:
                return func(self, *args, **kwargs, cursor=cursor)
            except AttributeError:
                return "Нет подключения к БД"
            except Exception as e:
                bad_query = None
                if type(args[0]) == sql.Composed:
                    bad_query = args[0].as_string(self.conn)
                elif type(args[0]) == str:
                    bad_query = args[0]
                self.__write_logs(bad_query, cursor=cursor)

                return "Ошибка при обращении к БД"

        return the_wrapper_around_the_original_function

    def __write_logs(self, bad_query, cursor):
        query = "INSERT INTO {table}({fields}) VALUES({values});"
        values = {
            "table": sql.Identifier("logs_bad_query"),
            "fields": sql.Identifier("query"),
            "values": sql.Literal(bad_query)
        }
        cursor.execute(sql.SQL(query).format(**values))

    def connect(self, config):
        """Connect to database PostgreSQL"""
        try:
            conn = psycopg2.connect(
                dbname=str(config['POSTGRES']['POSTGRES_DATABASE_NAME']),
                user=str(config['POSTGRES']['POSTGRES_USERNAME']),
                password=str(config['POSTGRES']['POSTGRES_PASSWORD']),
                host=str(config['POSTGRES']['POSTGRES_HOST']),
                port=str(config['POSTGRES']['POSTGRES_PORT']))
            conn.autocommit = True
            return conn
        except psycopg2.OperationalError:
            return False

    def close(self):
        """Close connect with database"""
        if self.conn:
            self.conn.close()
        return True

    @__init_cursor
    def select_data(self, execute, cursor):
        # Если присылаемым значение было error, то вызывается исключение
        if execute == "error":
            raise AttributeError
        cursor.execute(execute)

        return cursor.fetchall()

    @__init_cursor
    def insert_data(self, execute, cursor, name_file=None):
        try:
            # Если присылаемым значение было error, то вызывается исключение
            if execute == "error":
                raise AttributeError

            cursor.execute(execute)
        except psycopg2.errors.UniqueViolation:
            if str(name_file).find('.') != -1:
                if name_file.split('.')[-1] == 'registration':
                    return "Пользователь с таким никнеймом уже существует"

        return True

    @__init_cursor
    def login(self, data, cursor):

        # Структура содержащая значения для отправки
        values_data = {
            "number_phone": sql.Literal(data["number_phone"])
        }
        # Структура содержащая поля для отправки
        columns = {
            "number_phone": sql.Identifier("number_phone")
        }

        # Формирование выражения для условия
        condition = []
        for key in data:
            condition.append(sql.SQL("=").join(
                val for val in [columns[key], values_data[key]]
            ))
        # Формирование структуры для подстановке к запросу
        values = {
            "field": sql.SQL(",").join(sql.Identifier(i) for i in ["id", "otp", "role", "status_active", "time_create_otp"]),
            "table": sql.Identifier("public", "users"),
            "condition": sql.SQL(" and ").join(cond for cond in condition)
        }

        query = "SELECT {field} FROM {table} WHERE {condition};"
        cursor.execute(sql.SQL(query).format(**values))
        psw = cursor.fetchone()
        return (psw if psw != None else False)
