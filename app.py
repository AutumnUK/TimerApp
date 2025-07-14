from flask import Flask, render_template, request, redirect, url_for, session

from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = 'doingurmom'

# username password
USERNAME = 'user'
PASSWORD = 'pass'

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    if username == USERNAME and password == PASSWORD:
        session['user'] = username
        return redirect(url_for('dashboard'))
    else:
        return 'Invalid Login'


@app.route('/dashboard/')
def dashboard():
    if 'user' in session:
        return render_template('dashboard.html', user=session['user'])
    return redirect(url_for('home'))


@app.route('/logout')
def logout():
    session.pop('user',None)
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)


