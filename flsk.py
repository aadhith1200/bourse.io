from flask import Flask
from flask import flash, redirect, render_template, request, session, abort, url_for
import os
import exchange_test

app = Flask(__name__)
name="aadhith"

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


@app.route('/market', methods=['GET','POST'])

def market():

    l=exchange_test.market()
    ticker=l[0]
    ltp=l[1]
    change=l[2]
    changep=l[3]
    timestmp=l[4]

    return render_template('market.html',ln = len(ticker), ticker=ticker,ltp=ltp, change=change, changep=changep, timestmp=timestmp)

@app.route('/portfolio', methods=['GET','POST'])
def portfolio():


    global name
    nm=name
    l=exchange_test.portfolio(nm)
    ticker=l[0]
    qty=l[1]
    timestmp=l[2]

    return render_template('portfolio.html',nm=nm,ln = len(ticker), ticker=ticker,qty=qty, timestmp=timestmp)

@app.route('/orderbook', methods=['GET','POST'])
def orderbook():

    global name
    nm=name
    l=exchange_test.orderbook(nm)
    order=l[0]
    ord_type=l[1]
    ticker=l[2]
    price=l[3]
    status_qty=l[4]
    timestamp=l[5]

    return render_template('orderbook.html',nm=nm,ln = len(ticker),order=order,ord_type=ord_type, ticker=ticker,price=price,status_qty=status_qty,timestamp=timestamp)

if __name__ == "__main__":
    app.secret_key = os.urandom(12)
    app.run(debug=True,use_reloader=False,port=5000)
