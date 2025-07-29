import os
from flask import Flask, render_template, request, flash, redirect, url_for, abort
from dotenv import load_dotenv
from .database import validate_url, add_url, get_url_by_id, get_all_urls, get_url_by_name

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/urls', methods=['GET', 'POST'])
def urls():
    if request.method == 'POST':
        url = request.form.get('url')
        
        # Валидация URL
        is_valid, error_message = validate_url(url)
        if not is_valid:
            flash(error_message, 'error')
            return render_template('index.html', url=url), 422
        
        # Проверяем, существует ли URL уже в базе
        existing_url = get_url_by_name(url)
        if existing_url:
            flash('Страница уже существует', 'info')
            return redirect(url_for('url_show', id=existing_url[0]))
        
        # Добавляем новый URL
        try:
            url_id = add_url(url)
            flash('Страница успешно добавлена', 'success')
            return redirect(url_for('url_show', id=url_id))
        except Exception as e:
            flash('Произошла ошибка при добавлении URL', 'error')
            return render_template('index.html', url=url), 422
    
    # GET запрос - показываем список всех URL
    urls_list = get_all_urls()
    return render_template('urls.html', urls=urls_list)


@app.route('/urls/<int:id>')
def url_show(id):
    url_data = get_url_by_id(id)
    if not url_data:
        abort(404)
    
    return render_template('url_show.html', url=url_data)


if __name__ == '__main__':
    app.run(debug=True) 