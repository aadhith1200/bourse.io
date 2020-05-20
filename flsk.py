from flask import Flask
from flask import flash, redirect, render_template, request, session, abort, url_for, jsonify, make_response
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
import os
import exchange_test
import json
from datetime import datetime
from flask_cors import CORS
from time import time

app = Flask(__name__)
CORS(app)
s = URLSafeTimedSerializer('Thisisasecret!')
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
            flash('Username or Email id Already Exists!')
            return render_template('signup.html')

    else:
        return render_template('signup.html')


@app.route("/logout")

def logout():

    session['logged_in'] = False
    session['user_name'] = ""
    return redirect(url_for('home'))


@app.route('/portfolio', methods=['GET','POST'])
def portfolio():

    if not session.get('logged_in'):
        return render_template('login.html')
    
    return render_template('portfolio.html')

@app.route('/orderbook', methods=['GET','POST'])
def orderbook():

    if not session.get('logged_in'):
        return render_template('login.html')

    else:
        return render_template('orderbook.html')
    
@app.route('/order', methods=['GET','POST'])

def order():

    if not session.get('logged_in'):
        return render_template('login.html')

    else:
        if request.method == 'POST':
            if (request.form['order_type']!="MRKT" and request.form['order_type']!="LMT") or request.form['qty']=='' or request.form['price']=='':
                flash("Invalid inputs")
                return redirect(f"/stockpage?ticker={request.args['sname']} ({request.args['ticker']})")
            order_type = str(request.form['order_type'])
            order = request.args['ord'].upper()
            ticker = request.args['ticker'].upper()
            qty = int(request.form['qty'])
            if(order_type=='LMT'):
                price = int(request.form['price'])
            else:
                price = 'NULL'
            print(order,order_type,price,ticker,qty,session.get('user_name'))
            out=exchange_test.order(order,order_type,price,ticker,qty,session.get('user_name'))
            if out['status'] == "PLACED":
                flash('Order placed successfully!, Check your orderbook!')
                print('Order placed successfully!, Check your orderbook!')
                return stock()
            elif out['status'] == "insufficient":
                flash('Insufficient Funds!')
                return redirect(f"/stockpage?ticker={request.args['sname']} ({request.args['ticker']})")
            else:
                flash('Incorrect Inputs!')
                return redirect(f"/stockpage?ticker={request.args['sname']} ({request.args['ticker']})")

@app.route('/fund', methods=['GET','POST'])
def fund():

    if not session.get('logged_in'):
        return render_template('login.html')

    else:

        funds=exchange_test.funds_disp(session.get('user_name'))
        if request.method == 'POST':
            if(request.form['fund']==''):
                flash("Invalid input!")
                return redirect(url_for("fund"))
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
        email = request.form['email']
        token = s.dumps(email, salt='email-confirm')
        link = url_for('reset_password', token=token, _external=True)
        status=exchange_test.forgot_password(email,link)
        if status!="0" and status!="1":
            session['user_name']=status
            flash('The link to reset the password is sent to your mail!')
            session['mode']='forgot_password'
            return home()

        elif status=="0":
            flash('Email id not found!')
            return home()

        elif status=="1":
            flash('Oops! Error on our part,Try again later.')
            return home()

    else:
        return render_template('forgot_password.html')

@app.route('/reset-password/<token>', methods=['GET','POST'])
def reset_password(token):
    if(session['logged_in']):
        if request.method == 'POST':
            status = exchange_test.reset_password(request.form.get('pwd'),request.form.get('cnf_pwd'),session.get('user_name'))
            if status=="success":
                flash('Password Changed!')
                session['mode']=""
                return redirect(url_for("home"))
    
            elif status=="no_match":
                flash('Password does not match')
                return render_template('reset_password.html')

            else:
                flash('Oops! Something went wrong.')
                return home()

        else:
            return render_template('reset_password.html',token="/reset-password/loggedin=true")
        
        
    try:
        email = s.loads(token, salt='email-confirm', max_age=3600)
    except:
        flash("Session Timed Out or Wrong URL!")
        return home()

    if request.method == 'POST':
        status = exchange_test.reset_password(request.form.get('pwd'),request.form.get('cnf_pwd'),session.get('user_name'))
        if status=="success":
            flash('Password Changed!')
            session['mode']=""
            return home()

        elif status=="no_match":
            flash('Password does not match')
            return render_template('reset_password.html')

        else:
            flash('Oops! Something went wrong.')
            return home()

    else:
        return render_template('reset_password.html',token=token)


@app.route('/orderbookdata',methods=['GET','POST'])
def orderbookdata():
    if not session.get('logged_in'):
        return render_template('login.html')
    reqtype=request.args['req']
    if(reqtype=="open"):
        d=exchange_test.orderbook("open",session['user_name'])
        return(json.dumps(d))
    elif(reqtype=="exec"):
        d=exchange_test.orderbook("exec",session['user_name'])
        return(json.dumps(d))
    else:
        return "error"
    
@app.route('/watchlist',methods=['GET','POST'])
def watchlist():
    userid=session['user_name']
    if request.method=="POST":
        sname=request.url.split("=")[1]
        d=exchange_test.watchlist(userid,sname,"add")
        if(d=="already exist"):
            flash("Already in Watchlist!")
            return redirect(url_for('home'))
        if(d=="success"):
            flash("Added to Watchlist!")
            return redirect(url_for('home'))
    
    else:
        url=request.url.split("=")
        if(url[1]=="asc"):    
            d=exchange_test.watchlist(userid,"0","0")
            return json.dumps(d)
        else:
            sname=url[1]
            d=exchange_test.watchlist(userid,sname,"remove")
            if(d=="success"):
                flash("Removed from Watchlist")
                return redirect(url_for('home'))
    
    
@app.route('/dashboard_right',methods=['GET','POST'])
def dashboard_right():
    userid=session['user_name']
    if(request.url.split("=")[1]=='total'):
        data=exchange_test.pandl(userid,'total')
        if(data=="portfolio empty"):
            total=[0,0,datetime.now().strftime("%d %B %Y %I:%M:%S %p")]
            response = make_response(json.dumps(total))
            response.content_type = 'application/json'
            return response
        else:
            total=[data[0],data[1],datetime.now().strftime("%d %B %Y %I:%M:%S %p")]
            response = make_response(json.dumps(total))
            response.content_type = 'application/json'
            return response
    
    if(request.url.split('=')[1]=='table&order'):
        data=exchange_test.pandl(userid,'table')
        if(data=="portfolio empty"):
            return data
        else:
            return json.dumps(data)
        
    
@app.route('/stockpage')
def stockpage():
    if not session.get('logged_in'):
        return render_template('login.html')
    ticker= request.args['ticker']
    ticker=ticker.split("(")
    if(len(ticker)!=2):
        flash("Invalid Stock")
        return redirect(url_for('home'))
    sname=ticker[0][:-1]
    tickername=ticker[1][:-1]
    out=exchange_test.checkticker(tickername)
    if(out==True):
        return render_template("stockpage.html",ticker=tickername,sname=sname)
    else:
        flash("Invalid Stock")
        return redirect(url_for('home'))

@app.route('/stockdata')
def stockdata():
    if not session.get('logged_in'):
        return render_template('login.html')
    ticker=request.args['stock']
    data=exchange_test.stockdata(ticker)
    response = make_response(json.dumps(data))
    response.content_type = 'application/json'
    return response
@app.route('/portfoliodata')
def portfoliodata():
    if not session.get('logged_in'):
        return render_template('login.html')
    d=exchange_test.portfolio(session['user_name'])
    return json.dumps(d)

@app.route('/cancelorder')
def cancelorder():
    timestmp=str(request.args['cancel'])
    op=exchange_test.cancelorder(timestmp,session['user_name'])
    if(op=="success"):
        flash("Order Cancelled")
        print(op)
        return orderbook()
    else:
        flash("Oops! Something went wrong.")
    
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == "__main__":
    app.secret_key = os.urandom(12)
    app.run(debug=True,use_reloader=False,port=5000)
