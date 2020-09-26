from flask import Blueprint, jsonify, request
from psycopg2 import sql

from app.database import Database
from app.models import check_auth, authorize
from app.config import config

from api.api import get_status_code

manage_document_bp = Blueprint('manage_document', __name__)


@manage_document_bp.route('/free_documents', methods=['GET'])
def free_document():
    user = check_auth(request.headers, __name__)
    if user != True:
        return user
    user = authorize.get(request.headers.get('UserToken'))
    try:
        database = Database(config)
    except TypeError:
        return jsonify({"message": "Нет подключения к БД"})
    
    result = []

    query = """
    SELECT 
        doc.id,
        u.lastname,
        u.firstname,
        u.patronymic,
        doc.dt_upload,
		dt.title
    FROM documents doc
    LEFT JOIN document_processing dp ON dp.document_id = doc.id
    LEFT JOIN users u ON u.id = doc.user_id
	LEFT JOIN document_type dt ON dt.id = doc.document_type_id
    WHERE dp.status_code_id is NULL;"""

    for row in database.select_data(query):
        result.append({
            "document_id": row[0],
            "lastname": row[1],
            "firstname": row[2],
            "patronymic": row[3],
            "dt_upload": row[4],
            "document_type": row[5]
        })
        
    database.close()
    return jsonify(result)

@manage_document_bp.route('/my_documents', methods=['GET'])
def my_documents():
    user = check_auth(request.headers, __name__)
    if user != True:
        return user
    user = authorize.get(request.headers.get('UserToken'))
    try:
        database = Database(config)
    except TypeError:
        return jsonify({"message": "Нет подключения к БД"})
    
    result = []

    query = """
    SELECT 
        doc.id,
        u.lastname,
        u.firstname,
        u.patronymic,
        doc.dt_upload,
		dt.title
    FROM documents doc
    LEFT JOIN document_processing dp ON dp.document_id = doc.id
    LEFT JOIN users u ON u.id = doc.user_id
	LEFT JOIN document_type dt ON dt.id = doc.document_type_id
    WHERE dp.manager_id={};""".format(user.get_id())

    for row in database.select_data(query):
        result.append({
            "document_id": row[0],
            "lastname": row[1],
            "firstname": row[2],
            "patronymic": row[3],
            "dt_upload": row[4],
            "document_type": row[5]
        })
        
    database.close()
    return jsonify(result)

@manage_document_bp.route('/change_status', methods=['GET', 'POST'])
def change_status():
    user = check_auth(request.headers, __name__)
    if user != True:
        return user
    user = authorize.get(request.headers.get('UserToken'))
    try:
        database = Database(config)
    except TypeError:
        return jsonify({"message": "Нет подключения к БД"})
    
    result = {}

    if request.method == 'GET':
        return get_status_code(True)
    elif request.method == 'POST':
        json = request.get_json(silent=True)
        if not json:
            return jsonify({"message": "JSON не найден"}), 400
        
        fields = [
            "document_id",
            "status_code_id"
        ]
        for field in fields:
            if not json.get(field):
                return jsonify({"message": f"Поле {field} не найдено"}), 400

        query = None
        values = None
        isManager = database.select_data(sql.SQL("SELECT manager_id FROM document_processing WHERE document_id={document_id}").format(
            document_id=sql.Literal(json.get("document_id")))
            )
        if isManager:
            isManager = isManager[0][0]

        if isManager == user.get_id() and isManager:
            query = "UPDATE {table} SET {fields}={values} WHERE document_id={document_id}"

            values = {
                "table": sql.Identifier("public", "document_processing"),
                "fields": sql.SQL(",").join(sql.Identifier(i) for i in [
                    "status_code_id"
                ]),
                "values": sql.SQL(",").join(sql.Literal(i) for i in [
                    json.get("status_code_id")
                ]),
                "document_id": sql.Literal(json.get("document_id"))
            }
        elif isManager != user.get_id() and isManager:
            return jsonify({"message": f"Документ не найден"})
        else:
            query = "INSERT INTO {table}({fields}) VALUES({values})"

            values = {
                "table": sql.Identifier("public", "document_processing"),
                "fields": sql.SQL(",").join(sql.Identifier(i) for i in [
                    "document_id",
                    "status_code_id",
                    "manager_id"
                ]),
                "values": sql.SQL(",").join(sql.Literal(i) for i in [
                    json.get("document_id"),
                    json.get("status_code_id"),
                    user.get_id()
                ])
            }

        result = database.insert_data(sql.SQL(query).format(**values))

        
    database.close()
    return jsonify(result)

