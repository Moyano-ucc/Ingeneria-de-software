from flask import render_template


def error_page(message, status_code):
    return render_template("error.html", mensaje=message), status_code
