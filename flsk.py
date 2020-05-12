from flask import Flask
from flask import flash, redirect, render_template, request, session, abort, url_for
import os
import exchange_test

app = Flask(__name__)
@app.route('/',methods=['GET', 'POST'])
def home():
    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        return render_template('stock.html')

@app.route('/stock')
def stock():

    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        return render_template('stock.html',user=session.get('user_name'))

@app.route('/login', methods=['GET','POST'])
def login():

    pwd = request.form['pwd'];
    user = request.form['user'];
    session['user_name']=user
    if exchange_test.login(user,pwd):
        session['logged_in'] = True
        return redirect(url_for('stock'))
    else:
        flash('Wrong username or password!')
        return home()


@app.route("/signup",methods=['GET', 'POST'])

def signup():

    if request.method == 'POST':
        if exchange_test.register(request.form['user'],request.form['pwd'],request.form['name'],request.form['fund'],request.form['email']):
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
    session['user_name'] = ""
    return redirect(url_for('home'))


@app.route('/market', methods=['GET','POST'])

def market():

    if not session.get('logged_in'):
        return render_template('login.html')

    else:
        l=exchange_test.market()
        ticker=l[0]
        ltp=l[1]
        change=l[2]
        changep=l[3]
        timestmp=l[4]

        return render_template('market.html',ln = len(ticker), ticker=ticker,ltp=ltp, change=change, changep=changep, timestmp=timestmp)

@app.route('/portfolio', methods=['GET','POST'])
def portfolio():

    if not session.get('logged_in'):
        return render_template('login.html')

    else:
        nm=session.get('user_name')
        l=exchange_test.portfolio(nm)
        ticker=l[0]
        qty=l[1]
        timestmp=l[2]

        return render_template('portfolio.html',nm=nm,ln = len(ticker), ticker=ticker,qty=qty, timestmp=timestmp)

@app.route('/orderbook', methods=['GET','POST'])
def orderbook():

    if not session.get('logged_in'):
        return render_template('login.html')

    else:
        nm=session.get('user_name')
        l=exchange_test.orderbook(nm)
        order=l[0]
        ord_type=l[1]
        ticker=l[2]
        price=l[3]
        status_qty=l[4]
        timestamp=l[5]

        return render_template('orderbook.html',nm=nm,ln = len(ticker),order=order,ord_type=ord_type, ticker=ticker,price=price,status_qty=status_qty,timestamp=timestamp)

@app.route('/order', methods=['GET','POST'])

def order():

    if not session.get('logged_in'):
        return render_template('login.html')

    else:
        if request.method == 'POST':

            order_type = str(request.form['order_type'])
            order = str(request.form['trade']).upper()
            ticker = str(request.form['ticker'])
            qty = int(request.form['qty'])
            if(order_type=='LMT'):
                price = int(request.form['price'])
            else:
                price = 'NULL'
            print(order_type,order,ticker,qty,price,name)
            out=exchange_test.order(order,order_type,price,ticker,qty,session.get('user_name'))
            if out['status'] == "placed":
                flash('Order placed successfully!, Check your orderbook!')
                return stock()
            elif out['status'] == "insufficient":
                flash('Insufficient Funds!')
                return render_template('order.html')
            else:
                flash('Incorrect Inputs!')
                return render_template('order.html')

        else:
            return render_template('order.html')


@app.route('/fund', methods=['GET','POST'])
def fund():

    if not session.get('logged_in'):
        return render_template('login.html')

    else:

        funds=exchange_test.funds_disp(session.get('user_name'))
        if request.method == 'POST':

            fnd = int(request.form['fund'])
            flag = request.form['flag']
            print(fnd,flag)
            if exchange_test.funds_update(session.get("user_name"),fnd,flag[0]) == "success":
                if(flag=="Add"):
                    flash("Funds added successfully")
                    return stock()
                elif(flag=="Withdraw"):
                    flash("Funds withdrawn successfully")
                    return stock()
            else:
                flash('Wrong Input!')
                return render_template('fund.html',funds=funds)

        else:
            return render_template('fund.html',funds=funds)

@app.route('/forgot-password', methods=['GET','POST'])
def forgot_password():
    if request.method == 'POST':
        status=exchange_test.forgot_password(request.form.get('email'))
        if status!="0" and status!="1":
            session['user_name']=status
            flash('The link to reset the password is sent to your mail!')
            return home()

        elif status=="0":
            flash('Email id not found!')
            return home()
        elif status=="1":
            flash('Oops! Error on our part,Try again later.')
            return home()

    else:
        return render_template('forgot_password.html')

@app.route('/reset-password', methods=['GET','POST'])
def reset_password():
    if request.method == 'POST':
        status = exchange_test.reset_password(request.form.get('pwd'),request.form.get('cnf_pwd'),session.get('user_name'))
        if status=="success":
            flash('Password Changed!')
            return home()

        elif status=="no_match":
            flask('Password does not match')
            return render_template('reset_password.html')

        else:
            flash('Oops! Something went wrong.')
            return home()

    else:
        return render_template('reset_password.html')




if __name__ == "__main__":
    app.secret_key = os.urandom(12)
    app.run(debug=True,use_reloader=False,port=5000)
