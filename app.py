from flask import Flask, render_template, request, session, redirect, url_for
from flask_mysqldb import MySQL
from datetime import datetime
from flask_session import Session

sess = Session()

app = Flask(__name__)
app.debug = True
app.secret_key = 'pretestmitramas_df%&'
app.config['SESSION_TYPE'] = 'filesystem'
sess.init_app(app)

app.config['MYSQL_HOST'] = 'remotemysql.com'
app.config['MYSQL_USER'] = 'TL2O72Uy3k'
app.config['MYSQL_PASSWORD'] = 'fB3oxE4BPc'
app.config['MYSQL_DB'] = 'TL2O72Uy3k'
mysql = MySQL(app)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    elif request.method == 'POST':
        session['username'] = username = request.form['username']
        password = request.form['password']
        conn = mysql.connection.cursor()
        try:
            conn.execute("""INSERT INTO users(username, password) VALUES(%s,%s)""", [username, password])
            mysql.connection.commit()
            conn.close()
            session['registeruniqueerror'] = False
            return redirect(url_for('index'))
        except Exception as e:
            session['registeruniqueerror'] = True
            return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':       
        conn = mysql.connection.cursor()
        conn.execute("""SELECT password FROM users WHERE username=%s""", [request.form['username']])
        result = conn.fetchall()
        conn.close()
        if result:
            session['wrong'] = False
            if result[0][0] == request.form['password']:
                session['islogin'] = True
                session['username'] = request.form['username']
                return redirect(url_for('index'))
            else:
                session['wrong'] = True
                return render_template('login.html')
        else:
            session['wrong'] = True
            return render_template('login.html')
    elif request.method == 'GET':
        return render_template('login.html')

@app.route('/logout', methods=['GET'])
def logout():
    session.pop('username', None)
    session['islogin'] = False
    session.pop('check', None)
    return redirect(url_for('index'))

@app.route('/index', methods=['GET', 'POST'])
def index():
    issearchdate = False
    if session['islogin']:
        conn = mysql.connection.cursor()
            
        if request.method == 'GET':
            if 'username' not in session:
                session['username'] = ''
            if 'check' not in session:
                session['check'] = dict()
            if 'bool' not in session['check']:
                session['check']['bool'] = False
            
            
                conn.execute("""SELECT checkin, checkout FROM checks WHERE username=%s and checkout=%s""", [session['username'], 'null'])
                result = conn.fetchall()
                if len(result) == 1:
                    session['check']['intime'] = result[0][0]
                    session['check']['bool'] = True

        elif request.method == 'POST':
            
            if request.form['option'] == 'checkin' and not session['check']['bool']:
                session['check']['intime'] = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")).strip()
                session['check']['bool'] = True

                conn.execute("""INSERT INTO checks(username, checkin, checkout) VALUES (%s, %s, %s)""", [session['username'], session['check']['intime'], 'null'])
                mysql.connection.commit()

                session['check']['outtime'] = None

            if request.form['option'] == 'checkout' and session['check']['bool']:
                session['check']['outtime'] = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")).strip()
                session['check']['bool'] = False

                conn.execute("""UPDATE checks SET checkout=%s WHERE username=%s and checkin=%s""", [session['check']['outtime'], session['username'], session['check']['intime']])
                mysql.connection.commit()

                session['check']['intime'] = None

            if request.form['option'] == 'add':
                conn.execute("""INSERT INTO activities(username, date, activity) VALUES(%s, %s, %s)""", [session['username'], str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")).strip(), str(request.form['task'])])
                mysql.connection.commit()

            if request.form['option'] == 'delete':
                conn.execute("""DELETE FROM activities WHERE username=%s and date=%s and activity=%s""", [session['username'], str(request.form['activitytime']), str(request.form['activityname'])])
                mysql.connection.commit()
            
            if request.form['option'] == 'edit':
                conn.execute("""UPDATE activities SET activity=%s WHERE username=%s and date=%s and activity=%s""", [str(request.form['activitynewname']), session['username'], str(request.form['activitytime']), str(request.form['activityname'])])
                mysql.connection.commit()
            
            if request.form['option'] == 'searchtask':
                conn.execute("""SELECT date, activity FROM activities WHERE username=%s and date like %s""", [session['username'], str(request.form['activitydate']) + '%'])
                history_activities = conn.fetchall()
                issearchdate = True

        conn.execute("""SELECT checkin, checkout FROM checks WHERE username=%s""", [session['username']])
        history_checks = conn.fetchall()
        
        if not issearchdate:
            conn.execute("""SELECT date, activity FROM activities WHERE username=%s""", [session['username']])
            history_activities = conn.fetchall()

        conn.close()
        return render_template('index.html', history_checks=history_checks, history_activities=history_activities)
    
    else:
        return render_template('index.html')

@app.route('/', methods=['GET'])
def hello():
    return index()