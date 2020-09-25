import re
import os
import configparser

from flask import Blueprint, request, make_response, jsonify
from werkzeug.security import check_password_hash
from psycopg2 import sql

from app.models import User, authorize
from app.config import config
from app.database import Database

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/auth', methods=['POST'])
def auth_api():
    try:
        database = Database(config)
    except TypeError:
        return jsonify({"message": "Нет подключения к БД"})
    username = request.get_json(silent=True).get("username")
    password = request.get_json(silent=True).get("password")
    user_data = database.login({"username": username})
    if user_data:
        if check_password_hash(user_data[1], password):
            if user_data[3] == True:
                user = User(
                    id=user_data[0],
                    username=username,
                    role=user_data[2]
                )
                authorize[user.get_token()] = user

                database.insert_data("UPDATE users SET last_login=now() \
                                    WHERE username='{username}'".format(
                    username=user.get_username()
                ))
                return jsonify({"UserToken": user.get_token(), "role": user.get_role()})
            return jsonify({'message': 'Пользователь заблокирован'}), 401, {'ContentType': 'application/json'}
    return jsonify({'message': 'Неправильный логин или пароль'}), 401, {'ContentType': 'application/json'}
