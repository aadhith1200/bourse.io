from flask import Flask
from flask import flash, redirect, render_template, request, session, abort
import os
import exchange_test

app = Flask(__name__)
name=""

@app.route('/',methods=['GET', 'POST'])
def home():
    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        return render_template('stock.html')
    
@app.route('/stock')
def stock():
    return render_template('stock.html',user=name)

@app.route('/login', methods=['GET','POST'])
def login():

    pwd = request.form['pwd'];
    user = request.form['user'];
    global name
    name=user
    if exchange_test.login(user,pwd):
        session['logged_in'] = True
        return redirect(url_for('stock'))
    else:
        flash('wrong password!')
        return home()
    
    
@app.route("/signup",methods=['GET', 'POST'])

def signup():

    if request.method == 'POST':
        if exchange_test.register(request.form['user'],request.form['pwd'],request.form['name'],request.form['funds']):
            flash('Account created successfully !')
            return home()

        else:
            flash('Username Already Exists!')
            return render_template('signup.html')

    else:
        return render_template('signup.html')


@app.route("/logout")

def logout():

    session['logged_in'] = False
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.secret_key = os.urandom(12)
    app.run(debug=True,use_reloader=False)
