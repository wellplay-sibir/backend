from app.errorhandler import error_bp

from api.api import api_bp
from api.manage_documents import manage_document_bp

from personal_area.authorization import auth_bp
from personal_area.logout import logout_bp


def route(app):
    app.register_blueprint(api_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(logout_bp)
    app.register_blueprint(error_bp)
    app.register_blueprint(manage_document_bp)

    return True


def csrf_exempt(csrf):
    csrf.exempt(api_bp)
    csrf.exempt(auth_bp)
    csrf.exempt(logout_bp)
    csrf.exempt(manage_document_bp)

    return True
