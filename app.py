from flask              import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy   import SQLAlchemy
from werkzeug.security  import generate_password_hash, check_password_hash


activity_xp_needed = 3600

app                                             = Flask(__name__)
app.secret_key                                  = 'doingurmom'
app.config['SQLALCHEMY_DATABASE_URI']           = 'sqlite:///timer.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']    = False
db                                              = SQLAlchemy(app)

class User(db.Model):
    id              = db.Column(db.Integer,     primary_key = True              )
    username        = db.Column(db.String(80),  nullable    = False, unique=True)
    password        = db.Column(db.String(200), nullable    = False             )
    level           = db.Column(db.Integer,     nullable    = False, default =1 )
    xp              = db.Column(db.Integer,     nullable    = False, default =0 )
    xp_needed       = db.Column(db.Integer,     nullable    = False, default =5 )
    free_hours      = db.Column(db.Integer,     nullable    = False, default =0 )
    free_minutes    = db.Column(db.Integer,     nullable    = False, default =0 )
    gil             = db.Column(db.Integer,     nullable    = False, default =0 )

class Activity(db.Model):
    id              = db.Column(db.Integer,     primary_key = True                                  )
    name            = db.Column(db.String,      nullable    = False                                 )
    user_id         = db.Column(db.Integer,     db.ForeignKey('user.id'), nullable=False            )
    total_seconds   = db.Column(db.Integer,     default     = 0                                     )
    level           = db.Column(db.Integer,     default     = 0                                     )
    xp              = db.Column(db.Integer,     default     = 0                                     )
    xp_needed       = db.Column(db.Integer,     default     = activity_xp_needed                    )
    user            = db.relationship('User',   backref     = db.backref('activities', lazy = True) )

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
    xp_earned = seconds
    activity.xp += xp_earned

    # Handle level-up
    activity_leveled_up = False
    while activity.xp >= activity_xp_needed:
        activity.xp -= activity_xp_needed
        activity.level += 1
        user.xp += 1
        while user.xp >= user.xp_needed:
            user.xp -= user.xp_needed
            user.level += 1
            user.xp_needed += 5
            
        activity_leveled_up = True
        

    

    db.session.commit()
    return redirect(url_for('dashboard'))



if __name__ == '__main__':
    app.run(debug=True)
