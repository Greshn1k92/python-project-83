import os

from dotenv import load_dotenv
from flask import (
    Flask, abort, flash, redirect, render_template, request, url_for
)

try:
    from .database import (
        add_check,
        add_url,
        get_all_urls,
        get_checks_by_url_id,
        get_url_by_id,
        get_url_by_name,
        init_db,
        validate_url,
    )
except ImportError:
    from database import (
        add_check,
        add_url,
        get_all_urls,
        get_checks_by_url_id,
        get_url_by_id,
        get_url_by_name,
        init_db,
        validate_url,
    )

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev")

# Инициализируем базу данных при запуске
# init_db()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/urls", methods=["GET", "POST"])
def urls():
    if request.method == "POST":
        url = request.form.get("url")

        # Валидация URL
        is_valid, error_message = validate_url(url)
        if not is_valid:
            flash(error_message, "error")
            return render_template("index.html", url=url), 422

        # Проверяем, существует ли URL уже в базе
        existing_url = get_url_by_name(url)
        if existing_url:
            flash("Страница уже существует", "info")
            return redirect(url_for("url_show", url_id=existing_url[0]))

        # Добавляем новый URL
        try:
            url_id = add_url(url)
            flash("Страница успешно добавлена", "success")
            return redirect(url_for("url_show", url_id=url_id))
        except Exception:
            flash("Произошла ошибка при добавлении URL", "error")
            return render_template("index.html", url=url), 422

    # GET запрос - показываем список всех URL
    urls_list = get_all_urls()
    return render_template("urls.html", urls=urls_list)


@app.route("/urls/<int:url_id>")
def url_show(url_id):
    url_data = get_url_by_id(url_id)
    if not url_data:
        abort(404)

    checks = get_checks_by_url_id(url_id)
    return render_template("url_show.html", url=url_data, checks=checks)


@app.route("/urls/<int:url_id>/checks", methods=["POST"])
def url_checks(url_id):
    url_data = get_url_by_id(url_id)
    if not url_data:
        abort(404)

    check_id = add_check(url_id)
    if check_id:
        flash("Страница успешно проверена", "success")
    else:
        flash("Произошла ошибка при проверке", "error")

    return redirect(url_for("url_show", url_id=url_id))


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
