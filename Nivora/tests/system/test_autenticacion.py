"""System tests of registration, initial level, login and logout through HTTP."""

from tests.helpers import test_client


def test_registration_checks_confirmation_and_password_strength_inline():
    client = test_client()
    client.get("/registro")
    with client.session_transaction() as session:
        csrf = session["csrf_token"]

    response = client.post(
        "/registro",
        data={
            "csrf_token": csrf,
            "nombre": "Ana",
            "email": "ana@example.com",
            "password": "solo-letras",
            "confirmacion": "solo-letras",
        },
    )

    assert response.status_code == 303
    form = client.get(response.headers["Location"])
    assert b"Usa al menos 8 caracteres, con letras y n" in form.content
    assert b"class=\"form-message\"" not in form.content
    assert b"value=\"solo-letras\"" not in form.content


def test_registration_confirmation_mismatch_is_shown_by_the_password_fields():
    client = test_client()
    client.get("/registro")
    with client.session_transaction() as session:
        csrf = session["csrf_token"]

    response = client.post(
        "/registro",
        data={
            "csrf_token": csrf,
            "nombre": "Ana",
            "email": "ana@example.com",
            "password": "clave1234",
            "confirmacion": "clave5678",
        },
    )
    form = client.get(response.headers["Location"])

    assert response.status_code == 303
    assert form.content.count(b"Las contrase") == 2
    assert b"clave1234" not in form.content
    assert b"clave5678" not in form.content


def test_registration_login_and_back_navigation_keep_user_in_the_flow():
    client = test_client()
    client.get("/registro")
    with client.session_transaction() as session:
        csrf = session["csrf_token"]

    registration = client.post(
        "/registro",
        data={
            "csrf_token": csrf,
            "nombre": "Ana",
            "email": "ana@example.com",
            "password": "clave1234",
            "confirmacion": "clave1234",
        },
    )
    assert registration.status_code == 303
    assert registration.headers["Location"].endswith("/nivel")
    assert client.get("/registro").headers["Location"].endswith("/nivel")

    client.get("/nivel")
    with client.session_transaction() as session:
        csrf = session["csrf_token"]
    client.post("/logout", data={"csrf_token": csrf})

    client.get("/login")
    with client.session_transaction() as session:
        csrf = session["csrf_token"]
    login = client.post(
        "/login",
        data={
            "csrf_token": csrf,
            "email": "ana@example.com",
            "password": "clave1234",
        },
    )

    assert login.status_code == 303
    assert login.headers["Location"].endswith("/aprender")
    assert client.get("/login").headers["Location"].endswith("/aprender")


def test_auth_forms_disable_caching_and_authenticated_user_does_not_return_to_signup():
    client = test_client()
    registration = client.get("/registro")

    assert registration.headers["Cache-Control"] == "no-store, max-age=0"
    with client.session_transaction() as session:
        session["usuario"] = {"nombre": "Ana", "recomendacion": {"codigo": "inicial"}}

    response = client.get("/registro")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/aprender")


def test_login_session_survives_next_request():
    client = test_client()
    client.get('/login')
    with client.session_transaction() as session:
        csrf = session['csrf_token']

    response = client.post(
        '/login',
        data={'csrf_token': csrf, 'email': 'missing@example.com', 'password': 'password-123'},
    )

    assert response.status_code == 303
    login_page = client.get(response.headers["Location"])
    assert b"Correo o contrase\xc3\xb1a incorrectos" in login_page.content
    assert b'value="password-123"' not in login_page.content
    assert b'id="email-error"' in login_page.content
    assert b'id="password-error"' in login_page.content
    assert b'class="form-message"' not in login_page.content


def test_level_page_requires_login():
    client = test_client()
    response = client.get("/nivel")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/registro")


def test_level_page_recommends_starting_from_zero():
    client = test_client()
    with client.session_transaction() as session:
        session["usuario"] = {"nombre": "Ana", "email": "ana@example.com"}

    response = client.post(
        "/nivel",
        data={"csrf_token": "invalid", "nivel_inicial": "no_se_nada"},
    )

    assert response.status_code == 400


def test_logout_clears_the_user_session():
    client = test_client()
    client.get("/login")
    with client.session_transaction() as session:
        session["usuario"] = {"nombre": "Ana"}
        csrf = session["csrf_token"]

    response = client.post("/logout", data={"csrf_token": csrf})

    assert response.status_code == 303
    assert response.headers["Location"].endswith("/")
    with client.session_transaction() as session:
        assert "usuario" not in session
