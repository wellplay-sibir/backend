import hashlib

from flask import Blueprint, jsonify, request
from psycopg2 import sql

from app.database import Database
from app.models import check_auth, authorize
from app.config import config

api_bp = Blueprint('api', __name__)


@api_bp.route('/documents', methods=['GET', "POST"])
def documets():
    user = check_auth(request.headers, __name__)
    if user != True:
        return user
    user = authorize.get(request.headers.get('UserToken'))
    try:
        database = Database(config)
    except TypeError:
        return jsonify({"message": "Нет подключения к БД"})
    
    result = {}

    if request.method == "GET":
        for row in database.select_data("SELECT id, title FROM document_type;"):
            result[row[0]] = row[1]
    elif request.method == "POST":
        json = request.get_json(silent=True)
        if not json:
            return jsonify({"message": "JSON не найден"}), 400 
        fields = [
            "hash",
            "document_type_id",
            "photo"
        ]
        for field in fields:
            if not json.get(field):
                return jsonify({"message": f"Поле {field} не найдено"}), 400

        hash_md5 = hashlib.md5()
        hash_md5.update(str(json.get("photo")).encode())

        if not hash_md5.hexdigest() == json.get("hash").lower():
            return jsonify({"message": f"hash не совпадает"}), 406
        
        query = "INSERT INTO {table}({fields}) VALUES ({values}, now())"

        values = {
            "table": sql.Identifier("public", "documents"),
            "fields": sql.SQL(",").join(sql.Identifier(i) for i in [
                "hash",
                "user_id",
                "document_type_id",
                "photo",
                "dt_upload"
            ]),
            "values": sql.SQL(",").join(sql.Literal(i) for i in [
                json.get("hash"),
                user.get_id(),
                json.get("document_type_id"),
                json.get("photo"),
            ])
        }

        result = database.insert_data(sql.SQL(query).format(**values))
        
    database.close()
    return jsonify(result)


@api_bp.route('/status_code', methods=['GET'])
def get_status_code(isCall = False):
    if not isCall:
        user = check_auth(request.headers, __name__)
        if user != True:
            return user
        user = authorize.get(request.headers.get('UserToken'))
    try:
        database = Database(config)
    except TypeError:
        return jsonify({"message": "Нет подключения к БД"})

    result = {}

    for row in database.select_data("SELECT id, title FROM status_code;"):
        result[row[0]] = row[1]
    
    database.close()
    return jsonify(result)