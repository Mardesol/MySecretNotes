import json, sqlite3, click, functools, os, hashlib,time, random, sys
from flask import Flask, current_app, g, session, redirect, render_template, url_for, request




### DATABASE FUNCTIONS ###

def connect_db():
    return sqlite3.connect(app.database)

def init_db():
    """Initializes the database with our great SQL schema"""
    conn = connect_db()
    db = conn.cursor()
    db.executescript("""

DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS friendlist;
DROP TABLE IF EXISTS notes;

CREATE TABLE notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    assocUser INTEGER NOT NULL,
    dateWritten DATETIME NOT NULL,
    note TEXT NOT NULL,
    publicID INTEGER NOT NULL
);

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT, 
    username TEXT NOT NULL,
    password TEXT NOT NULL
);

CREATE TABLE friendlist (
    assocUser INTEGER,
    friendId INTEGER NOT NULL,
    FOREIGN KEY (friendId)
        REFERENCES users (id),
    UNIQUE(assocUser, friendId)
);

INSERT INTO users VALUES(null,"admin", "lIgMaBaLlS");
INSERT INTO users VALUES(null,"bernardo", "omgMPC");
INSERT INTO users VALUES(null,"Alexander", "alexander123");
INSERT INTO users VALUES(null,"Dagrun", "dagrun123");
INSERT INTO users VALUES(null,"Frederik", "frederik123");
INSERT INTO users VALUES(null,"Joakim", "joakim123");
INSERT INTO users VALUES(null,"Markus", "markus123");
INSERT INTO users VALUES(null,"Steven", "steven123");
INSERT INTO users VALUES(null,"Test", "test123");
INSERT INTO notes VALUES(null,2,"1993-09-23 10:10:10","hello my friend",1234567890);
INSERT INTO notes VALUES(null,3,"1993-09-23 10:10:10","I love security",1111111110);
INSERT INTO notes VALUES(null,1,"1993-09-23 10:10:10","Admin rules",1111111111);
INSERT INTO notes VALUES(null,1,"1993-09-23 10:10:10","Good luck trying to get into this very secure system",1243433422);
INSERT INTO notes VALUES(null,1,"1993-09-23 10:10:10","The code is secu04",1243433242);
INSERT INTO notes VALUES(null,1,"1993-09-23 10:10:10","No, the code is adminRules",1243433452);
INSERT INTO notes VALUES(null,2,"1993-09-23 12:10:10","i want lunch pls",1234567891);
INSERT INTO friendlist VALUES(1, 2);

""")



### APPLICATION SETUP ###
app = Flask(__name__)
app.database = "db.sqlite3"
app.secret_key = os.urandom(32)

### ADMINISTRATOR'S PANEL ###
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return view(**kwargs)
    return wrapped_view

@app.route("/")
def index():
    if not session.get('logged_in'):
        return render_template('index.html')
    else:
        return redirect(url_for('notes'))


@app.route("/notes/", methods=('GET', 'POST'))
@login_required
def notes():
    importerror=""
    #Posting a new note:
    if request.method == 'POST':
        if request.form['submit_button'] == 'add note':
            note = request.form['noteinput']
            db = connect_db()
            c = db.cursor()
            statement = """INSERT INTO notes(id,assocUser,dateWritten,note,publicID) VALUES(null,?,?,?,?);"""
            print(statement, (session['userid'],time.strftime('%Y-%m-%d %H:%M:%S'),note,random.randrange(1000000000, 9999999999)))
            c.execute(statement, (session['userid'],time.strftime('%Y-%m-%d %H:%M:%S'),note,random.randrange(1000000000, 9999999999)))
            db.commit()
            db.close()
        elif request.form['submit_button'] == 'import note':
            noteid = request.form['noteid']
            db = connect_db()
            c = db.cursor()
            #Changed from string concatonation to question mark
            statement = """SELECT * from NOTES where publicID = ?"""
            #Noteid is added as an argument in execute
            c.execute(statement, (noteid,))
            result = c.fetchall()
            if(len(result)>0):
                row = result[0]
                statement = """INSERT INTO notes(id,assocUser,dateWritten,note,publicID) VALUES(null,%s,'%s','%s',%s);""" %(session['userid'],row[2],row[3],row[4])
                c.execute(statement)
            else:
                importerror="No such note with that ID!"
            db.commit()
            db.close()
        elif request.form['submit_button'] == 'Add friend':
            noteid = request.form['friendName']
            db = connect_db()
            c = db.cursor()
            statement = """SELECT * from USERS where username = ?"""
            c.execute(statement, (noteid,))
            result = c.fetchall()
            if(len(result)>0):
                row = result[0]
                # statement = """INSERT INTO notes(id,assocUser,dateWritten,note,publicID) VALUES(null,%s,'%s','%s',%s);""" %(session['userid'],row[2],row[3],row[4])
                statement = """INSERT INTO friendlist(assocUser,friendId) VALUES('%s','%s');""" %(session['userid'],row[0])
                c.execute(statement)
            else:
                importerror="No person with that username!"
            db.commit()
            db.close()
    
    # Get user specific information to be displayed
    db = connect_db()
    c = db.cursor()
    
    # Get notes
    statement = "SELECT * FROM notes WHERE assocUser = %s;" %session['userid']
    print(statement)
    c.execute(statement)
    notes = c.fetchall()
    print(notes)
    
    # Get ID of all friends
    statement = "SELECT * FROM friendlist WHERE assocUser = %s;" %session['userid']
    c.execute(statement)
    friends = c.fetchall()

    # Get information of friends
    friendsInfoList = []

    for row in friends:
        statement = "SELECT * FROM users WHERE id = %d;" % row[1]
        c.execute(statement)
        friendInfo = c.fetchall()
        friendsInfoList.append(friendInfo)

    return render_template('notes.html',notes=notes, friendsInfoList=friendsInfoList,importerror=importerror)

@app.route("/notes/delete/<publicID>", methods=('GET', 'POST'))
def delete(publicID):
        publicID = request.form['delete']
        db = connect_db()
        c = db.cursor()
        statement = """SELECT * from NOTES where publicID = ?"""
        c.execute(statement, (publicID,))
        result = c.fetchall()
        if(len(result)>0):
            row = result[0]
            statement = """DELETE from NOTES where publicID = ?"""
            c.execute(statement, (publicID,))
        else:
            importerror="Note not deleted!"
        db.commit()
        db.close()  

        db = connect_db()
        c = db.cursor()
        statement = "SELECT * FROM notes WHERE assocUser = %s;" %session['userid']
        print(statement)
        c.execute(statement)
        notes = c.fetchall()
        print(notes)
        return redirect(url_for('notes'))


@app.route("/login/", methods=('GET', 'POST'))
def login():
    error = ""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = connect_db()
        c = db.cursor()
        statement = "SELECT * FROM users WHERE username = ? AND password = ?;"
        c.execute(statement,(username, password))
        result = c.fetchall()

        if len(result) > 0:
            session.clear()
            session['logged_in'] = True
            session['userid'] = result[0][0]
            session['username']=result[0][1]
            return redirect(url_for('index'))
        else:
            error = "Wrong username or password!"
    return render_template('login.html',error=error)


@app.route("/register/", methods=('GET', 'POST'))
def register():
    errored = False
    usererror = ""
    passworderror = ""
    if request.method == 'POST':
        

        username = request.form['username']
        password = request.form['password']
        db = connect_db()
        c = db.cursor()
        pass_statement = """SELECT * FROM users WHERE password = '%s';""" %password
        user_statement = """SELECT * FROM users WHERE username = '%s';""" %username
        c.execute(pass_statement)
        if(len(c.fetchall())>0):
            errored = True
            passworderror = "That password is already in use by someone else!"

        c.execute(user_statement)
        if(len(c.fetchall())>0):
            errored = True
            usererror = "That username is already in use by someone else!"

        if(not errored):
            statement = """INSERT INTO users(id,username,password) VALUES(null,'%s','%s');""" %(username,password)
            print(statement)
            c.execute(statement)
            db.commit()
            db.close()
            return f"""<html>
                        <head>
                            <meta http-equiv="refresh" content="2;url=/" />
                        </head>
                        <body>
                            <h1>SUCCESS!!! Redirecting in 2 seconds...</h1>
                        </body>
                        </html>
                        """
        
        db.commit()
        db.close()
    return render_template('register.html',usererror=usererror,passworderror=passworderror)


@app.route("/logout/")
@login_required
def logout():
    """Logout: clears the session"""
    session.clear()
    return redirect(url_for('index'))

if __name__ == "__main__":
    #create database if it doesn't exist yet
    if not os.path.exists(app.database):
        init_db()
    runport = 5000
    if(len(sys.argv)==2):
        runport = sys.argv[1]
    try:
        app.run(host='0.0.0.0', port=runport) # runs on machine ip address to make it visible on netowrk
    except:
        print("Something went wrong. the usage of the server is either")
        print("'python3 app.py' (to start on port 5000)")
        print("or")
        print("'sudo python3 app.py 80' (to run on any other port)")