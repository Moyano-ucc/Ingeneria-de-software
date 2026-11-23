from views.responses import error_page


def register_error_handlers(app):
    @app.errorhandler(413)
    def request_too_large(_error):
        return error_page("La solicitud es demasiado grande", 413)

    @app.errorhandler(400)
    def bad_request(error):
        return error_page(error.description, 400)

    @app.errorhandler(404)
    def not_found(_error):
        return error_page("La página no existe", 404)

    @app.errorhandler(500)
    def internal_error(_error):
        return error_page("Ocurrió un error interno", 500)
