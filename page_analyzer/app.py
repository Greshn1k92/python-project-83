import os
from flask import Flask, render_template, request, flash, redirect, url_for
from dotenv import load_dotenv

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
        if not url:
            flash('URL обязателен', 'error')
            return redirect(url_for('index'))
        
        # Здесь будет логика обработки URL
        flash('Страница успешно проверена', 'success')
        return redirect(url_for('urls'))
    
    return render_template('urls.html')


if __name__ == '__main__':
    app.run(debug=True) 