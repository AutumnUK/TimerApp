from flask              import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy   import SQLAlchemy
from werkzeug.security  import generate_password_hash, check_password_hash

app                                             = Flask(__name__)
app.secret_key                                  = 'doingurmom'
app.config['SQLALCHEMY_DATABASE_URI']           = 'sqlite:///timer.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']    = False
db                                              = SQLAlchemy(app)

class User(db.Model):
    id              = db.Column(db.Integer,     primary_key=True)
    username        = db.Column(db.String(80),  unique=True,        nullable=False)
    password        = db.Column(db.String(200), nullable=False)
    level           = db.Column(db.Integer,     nullable=False,     default=1)
    xp              = db.Column(db.Integer,     nullable=False,     default=0)
    xp_needed       = db.Column(db.Integer,     nullable=False,     default=10)
    free_hours      = db.Column(db.Integer,     nullable=False,     default=0)
    free_minutes    = db.Column(db.Integer,     nullable=False,     default=0)

class Activity(db.Model):
    id              = db.Column(db.Integer,     primary_key=True)
    name            = db.Column(db.String,      nullable=False)
    user_id         = db.Column(db.Integer,     db.ForeignKey('user.id'), nullable=False)
    total_seconds   = db.Column(db.Integer,     default=0)
    level           = db.Column(db.Integer,     default=0)
    xp              = db.Column(db.Integer,     default=0)
    xp_needed       = db.Column(db.Integer,     default=60)
    user            = db.relationship('User',   backref=db.backref('activities', lazy=True))

# TODO 
# REMOVE THIS -> CREATE SIGNUP PAGE
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='moon').first():
        user = User(username='moon', password=generate_password_hash('pass'))
        db.session.add(user)
        db.session.commit()

# Default page.
@app.route('/')
def home():
    return render_template('login.html')

# Login Process
@app.route('/login', methods=['POST'])
def login():
    username    = request.form['username']
    password    = request.form['password']
    user        = User.query.filter_by(username=username).first()

    if user and check_password_hash(user.password,password):
        session['user_id']  = user.id
        session['username'] = user.username
        return redirect(url_for('dashboard'))

    else:
        return render_template('login.html')

# Dashboard Loading
@app.route('/dashboard/')
def dashboard():
    user_id     = session.get('user_id')

    if 'user_id':
        user        = User.query.get(user_id)
        activities  = Activity.query.filter_by(user_id=user_id).all()
        if user:
            return render_template('dashboard.html', user=user, activities=activities)

    return render_template('login.html')

# Logout process, clears the session.
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# Popup for adding the activity
@app.route('/add_activity', methods=['POST'])
def add_activity():   
    name    = request.form.get('name')
    user_id = session['user_id']
    
    if name:
        new_activity = Activity(name=name, user_id=user_id)
        db.session.add(new_activity)
        db.session.commit()
        print(f'Activity "{name}" added!')
    else:
        flash("Activity name cannot be empty.")
    
    return redirect(url_for('dashboard'))

@app.route('/stop_tracking', methods=['POST'])
def stop_tracking():
    if 'user_id' not in session:
        return redirect(url_for('home'))

    activity_id = int(request.form['activity_id'])
    seconds     = int(request.form['tracked_seconds'])
    user        = User.query.get(session['user_id'])
    activity    = Activity.query.get(activity_id)

    # xp_earned   = seconds // 1  # 1 XP per 1 second, 600 for level up, grants 60s fun time
    # activity.xp += xp_earned

    # while user.xp >= user.level * 2 + 10:
    #     user.level += 1
    #     flash(f"Level up! You reached level {user.level}!")

    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/api/progress', methods=['POST'])
def api_progress():
    if 'user_id' not in session:
        return jsonify({'status': 'unauthorized'}), 401

    data = request.json
    activity_id = data.get('activity_id')
    seconds = data.get('seconds')

    if not activity_id or seconds is None:
        return jsonify({'status': 'error', 'message': 'Missing data'}), 400

    activity = Activity.query.get(activity_id)
    user = User.query.get(session['user_id'])

    activity.total_seconds += seconds

    # Progress both activity and user
    activity_xp, activity_leveled_up = handle_activity_progression(activity, seconds)

    db.session.commit()

    return jsonify({
        'status': 'success',
        'activity_level': activity.level,
        'activity_xp': activity.xp,
        'activity_leveled_up': activity_leveled_up,
        'user_level': user.level,
        'user_xp': user.xp,
        'xp_needed': xp_needed(user.level)
    })

def xp_needed(level):
    return 60  # or whatever formula you want

def handle_activity_progression(activity, seconds):
    # 1 XP for every 6 minutes (360 seconds)
    xp_earned = seconds
    activity.xp += xp_earned

    # Handle level-up
    leveled_up = False
    while activity.xp >= xp_needed(activity.level):
        activity.xp -= xp_needed(activity.level)
        activity.level += 1
        leveled_up = True

    if leveled_up:
        print(f"User leveled up! New level: {activity.level}")

    return xp_earned

if __name__ == '__main__':
    app.run(debug=True)
