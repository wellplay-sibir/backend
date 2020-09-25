from flask import Blueprint, jsonify, request
from psycopg2 import sql

from app.database import Database
from app.models import check_auth, authorize
from app.config import config

api_bp = Blueprint('api', __name__)


@api_bp.route('/api', methods=['GET'])
def api():
    user = check_auth(request.headers, __name__)
    if user != True:
        return user
    user = authorize.get(request.headers.get('UserToken'))
    try:
        database = Database(config)
    except TypeError:
        return jsonify({"message": "Нет подключения к БД"})

    result = {}
    

    database.close()
    return jsonify(result)