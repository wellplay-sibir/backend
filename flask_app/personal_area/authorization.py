from time import time
import configparser
import datetime
import random
import string
import ftplib
import os

from flask import Blueprint, request, make_response, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from psycopg2 import sql

from app.models import User, authorize
from app.config import config
from app.database import Database

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/password', methods=['POST'])
def get_password():
    try:
        database = Database(config)
    except TypeError:
        return jsonify({"message": "Нет подключения к БД"})
    
    result = {}

    number_phone = request.get_json(silent=True).get("number_phone")
    if not number_phone:
        return jsonify({"error": "Телефон не найден"}), 404

    isFind = database.select_data(sql.SQL("SELECT id FROM users WHERE number_phone={number_phone}").format(number_phone=sql.Literal(number_phone)))

    if not isFind:
        isFind = create_user(database, number_phone)
    
    if isFind:
        password = generate_password()
        update_password(database, isFind[0], generate_password_hash(password, method='sha256'))
        send_password(password, number_phone)
        update_connection_log(database, isFind[0], request.remote_addr)

    database.close()
    return "Ok"


@auth_bp.route('/auth', methods=['POST'])
def auth_api():
    try:
        database = Database(config)
    except TypeError:
        return jsonify({"message": "Нет подключения к БД"})
    number_phone = request.get_json(silent=True).get("number_phone")
    password = request.get_json(silent=True).get("password")
    user_data = database.login({"number_phone": number_phone})
    if user_data:
        if time() - user_data[4].timestamp() >= 300:
            update_password(database, user_data[0], "")
            return jsonify({'message': 'Время пароля истекло'}), 401, {'ContentType': 'application/json'}

        if check_password_hash(user_data[1], password):
            if user_data[3] == True:
                user = User(
                    id=user_data[0],
                    number_phone=number_phone,
                    role=user_data[2]
                )

                authorize[user.get_token()] = user
                update_password(database, user_data[0], "")

                return jsonify({"UserToken": user.get_token(), "role": user.get_role()})
            return jsonify({'message': 'Пользователь заблокирован'}), 401, {'ContentType': 'application/json'}

    return jsonify({'message': 'Неправильный логин или пароль'}), 401, {'ContentType': 'application/json'}


def create_user(database, number_phone):
    query = "INSERT INTO {table}({fields}) VALUES ({values})"

    values = {
        "table": sql.Identifier("public", "users"),
        "fields": sql.SQL(",").join(sql.Identifier(i) for i in ["number_phone", "role"]),
        "values": sql.SQL(",").join(sql.Literal(i) for i in [number_phone, "2"])
    }

    database.insert_data(sql.SQL(query).format(**values))

    return database.select_data(sql.SQL("SELECT id FROM users WHERE number_phone={number_phone}").format(number_phone=sql.Literal(number_phone)))


def generate_password():
    length = 6
    letters_and_digits = string.ascii_letters + string.digits
    return ''.join((random.choice(letters_and_digits) for i in range(length)))


def update_password(database, user_id, password):
    query = "UPDATE {table} SET ({fields})=({values}) WHERE id={user_id}"

    values = {
        "table": sql.Identifier("public", "users"),
        "fields": sql.SQL(",").join(sql.Identifier(i) for i in ["otp", "time_create_otp"]),
        "values": sql.SQL("{}, now()").format(sql.Literal(password)),
        "user_id": sql.Literal(user_id)
    }
    
    return database.insert_data(sql.SQL(query).format(**values))


def send_password(password, number_phone):
    with open(f'./sms/{number_phone}', 'w', encoding='utf-8') as f:
        f.write(create_text(password, number_phone))

    path = f'{os.path.abspath(os.getcwd())}/sms'
    ftp = init_ftp(path)

    f = open(f'{path}/{number_phone}', 'rb')
    ftp.storlines(f'STOR {number_phone}', f)
    
    f.close()
    ftp.quit()
    os.remove(f"{path}/{number_phone}")

    return True


def init_ftp(path):
    FTP_TIMEOUT = 10 # seconds

    ftp = ftplib.FTP()

    ftp.connect(host=config['FTP']['FTP_HOST'], timeout=FTP_TIMEOUT)
    ftp.login()

    return ftp


def create_text(password, number_phone):
    return """To: +7{number_phone}
Alphabet: UTF-8
UDH: false

Одноразовый пароль для доступа: {password}. Не сообщайте его никому""".format(
            number_phone=number_phone,
            password=password
        )


def update_connection_log(database, user_id, ip_address):
    query = "INSERT INTO {table} ({fields}) VALUES({values})"

    values = {
        "table": sql.Identifier("public", "login_logs"),
        "fields": sql.SQL(",").join(sql.Identifier(i) for i in ["time_login", "ip_address", "user_id"]),
        "values": sql.SQL("now(), {ip_address}, {user_id}").format(
            ip_address=sql.Literal(ip_address),
            user_id=sql.Literal(user_id)),
        "user_id": sql.Literal(user_id)
    }
    print(sql.SQL(query).format(**values).as_string(database.conn))
    return database.insert_data(sql.SQL(query).format(**values))
