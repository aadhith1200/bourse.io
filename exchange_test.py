import flask,json,psycopg2,sqlite3
from mailer import Mailer
from mailer import Message
from pathlib import Path
app=flask.Flask(__name__)

url=str(Path(__file__).parent.absolute())+"\\"
market_db={'SBI':17,'HDFC':25}
def order(order,order_type,price,ticker,qty,name):
    data={'ord':order,'order_type':order_type,'price':price,'ticker':ticker,'qty':qty,'id':name}
    qty_init=data['qty']
    if(data['order_type']=="MRKT"):
        conn=sqlite3.connect(url+"orders.db")
        cur=conn.cursor()
        if(data['ord']=="BUY"):
            query="select * from orders where ticker='"+str(data['ticker'])+"' and ord='SELL' order by timestamp;"
            op=cur.execute(query)
            if(op):
                f=1
                orders=op.fetchall()
                quant=data['qty']
                for i in range(len(orders)):
                    op=orders[i]
                    d_id=op[0]
                    d_p=op[5]
                    d_userid=op[1]
                    d_qty=op[8]
                    if (d_qty==0):
                        continue
                    if(int(d_qty)<int(data['qty'])):
                        data['qty']=d_qty
                    conn2=sqlite3.connect(url+"users.db")
                    cur2=conn2.cursor()
                    funds=cur2.execute("select funds from users where userid=?",(data['id'],))
                    funds=funds.fetchone()[0]
                    if(d_p*data['qty']>funds):
                        d={"status":"insufficient"}
                        return d
                    else:
                        conn=sqlite3.connect(url+"orders.db")
                        cur=conn.cursor()
                        cur2.execute("update users set funds=funds-? where userid=?",(d_p*data['qty'],data['id']))
                        conn2.commit()
                        conn2.close()
                        if(data['qty']==d_qty):
                            cur.execute("update orders set status_qty=status_qty-?, status='BOOKED',timestamp=datetime(CURRENT_TIMESTAMP, 'localtime')  where ord_id=?",(data['qty'],d_id))
                            conn.commit()
                        else:
                            cur.execute("update orders set status_qty=status_qty-?, status='PARTIAL',timestamp=datetime(CURRENT_TIMESTAMP, 'localtime') where ord_id=?",(data['qty'],d_id))
                            conn.commit()
                        conn.close()
                        conn2=sqlite3.connect(url+"portfolio.db")
                        cur2=conn2.cursor()
                        check=cur2.execute(f"select * from {data['id']} where ticker='{data['ticker']}'")
                        if(len(check.fetchall())==0):
                            cur2.execute(f"insert into {data['id']}(ticker,qty) values('{data['ticker']}',{data['qty']})")
                            conn2.commit()
                        else:
                            cur2.execute(f"update {data['id']} set qty=qty+{data['qty']}, timestamp=datetime(CURRENT_TIMESTAMP, 'localtime') where ticker='{data['ticker']}'")
                            conn2.commit()

                        cur3=conn2.cursor()
                        cur3.execute(f"update {d_userid} set qty=qty-{data['qty']}, timestamp=datetime(CURRENT_TIMESTAMP, 'localtime') where ticker='{data['ticker']}'")
                        conn2.commit()
                        conn2.close()
                        conn4=sqlite3.connect(url+"users.db")
                        cur4=conn4.cursor()
                        cur4.execute("update users set funds=funds+? where userid=?",(d_p*data['qty'],d_userid))
                        conn4.commit()
                        conn4.close()
                        conn5=sqlite3.connect(url+"market.db")
                        cur5=conn5.cursor()
                        cur5.execute("update market set price=?, timestamp=datetime(CURRENT_TIMESTAMP, 'localtime') where ticker=?",(d_p,data['ticker']))
                        conn5.commit()
                        conn5.close()
                        if(data['qty']<d_qty):
                            f=0
                            break
                        data['qty']=quant-d_qty
                        quant=quant-d_qty
                        if(quant==0):
                            f=0
                            break

                if(f!=0):
                    conn=sqlite3.connect(url+"orders.db")
                    cur=conn.cursor()
                    d_id=cur.execute("select ord_id from orders order by ord_id DESC LIMIT 1")
                    conn2=sqlite3.connect(url+"market.db")
                    cur2=conn2.cursor()
                    d_p=cur2.execute("select price from market where ticker=?",(data['ticker'],))
                    d_p=d_p.fetchall()[0][0]
                    d_id=d_id.fetchall()[0][0]
                    conn2.close()
                    cur.execute("insert into orders(ord_id, userid, ord, order_type, qty, price,ticker,status,status_qty) values(?, ?, ?, ?, ?, ?, ?, ?, ?)",(d_id+1,data['id'],'BUY','MRKT',qty_init,d_p,data['ticker'],'PLACED',data['qty']))
                    conn.commit()
                    conn.close()


        elif(data['ord']=="SELL"):
                query="select * from orders where ticker='"+str(data['ticker'])+"' and ord='BUY' order by timestamp;"
                op=cur.execute(query)
                if(op):
                    f=1
                    orders=op.fetchall()
                    quant=data['qty']
                    con=sqlite3.connect(url+"portfolio_"+data['id']+".db")
                    c=con.cursor()
                    qty_check=c.execute("select qty from portfolio where ticker=?",(data['ticker'],))
                    qt=qty_check.fetchone()
                    if(qt[0]<data['qty']):
                        d={"status":"insufficient"}
                        return(d)
                    con.close()
                    for i in range(len(orders)):
                        op=orders[i]
                        d_id=op[0]
                        d_p=op[5]
                        d_userid=op[1]
                        d_qty=op[8]
                        if (d_qty==0):
                            continue
                        if(int(d_qty)<int(data['qty'])):
                            data['qty']=d_qty
                        conn2=sqlite3.connect(url+"users.db")
                        cur2=conn2.cursor()
                        funds=cur2.execute("select funds from users where userid=?",(d_userid,))
                        funds=funds.fetchone()[0]
                        if(d_p*data['qty']>funds):
                            continue
                        else:
                            conn=sqlite3.connect(url+"orders.db")
                            cur=conn.cursor()
                            cur2.execute("update users set funds=funds+? where userid=?",(d_p*data['qty'],data['id']))
                            conn2.commit()
                            conn2.close()
                            if(data['qty']==d_qty):
                                cur.execute("update orders set status_qty=status_qty-?, status='BOOKED',timestamp=datetime(CURRENT_TIMESTAMP, 'localtime')  where ord_id=?",(data['qty'],d_id))
                                conn.commit()
                            else:
                                cur.execute("update orders set status_qty=status_qty-?, status='PARTIAL',timestamp=datetime(CURRENT_TIMESTAMP, 'localtime') where ord_id=?",(data['qty'],d_id))
                                conn.commit()
                            conn.close()
                            conn2=sqlite3.connect(url+"portfolio.db")
                            cur2=conn2.cursor()
                            check=cur2.execute(f"select * from {d_userid} where ticker='{data['ticker']}'")
                            if(len(check.fetchall())==0):
                                cur2.execute(f"insert into {d_userid}(ticker,qty) values('{data['ticker']}',{data['qty']})")
                                conn2.commit()
                            else:
                                cur2.execute(f"update {d_userid} set qty=qty+{data['qty']}, timestamp=datetime(CURRENT_TIMESTAMP, 'localtime') where ticker='{data['ticker']}'")
                                conn2.commit()

                            cur3=conn2.cursor()
                            cur3.execute(f"update {data['id']} set qty=qty-{data['qty']}, timestamp=datetime(CURRENT_TIMESTAMP, 'localtime') where ticker='{data['ticker']}'")
                            conn2.commit()
                            conn2.close()
                            conn4=sqlite3.connect(url+"users.db")
                            cur4=conn4.cursor()
                            cur4.execute("update users set funds=funds-? where userid=?",(d_p*data['qty'],d_userid))
                            conn4.commit()
                            conn4.close()
                            conn5=sqlite3.connect(url+"market.db")
                            cur5=conn5.cursor()
                            cur5.execute("update market set price=?, timestamp=datetime(CURRENT_TIMESTAMP, 'localtime') where ticker=?",(d_p,data['ticker']))
                            conn5.commit()
                            conn5.close()
                            if(data['qty']<d_qty):
                                f=0
                                break
                            data['qty']=quant-d_qty
                            quant=quant-d_qty
                            if(quant==0):
                                f=0
                                break

                    if(f!=0):
                        conn=sqlite3.connect(url+"orders.db")
                        cur=conn.cursor()
                        d_id=cur.execute("select ord_id from orders order by ord_id DESC LIMIT 1")
                        conn2=sqlite3.connect(url+"market.db")
                        cur2=conn2.cursor()
                        d_p=cur2.execute("select price from market where ticker=?",(data['ticker'],))
                        d_p=d_p.fetchall()[0][0]
                        d_id=d_id.fetchall()[0][0]
                        conn2.close()
                        cur.execute("insert into orders(ord_id, userid, ord, order_type, qty, price,ticker,status,status_qty) values(?, ?, ?, ?, ?, ?, ?, ?, ?)",(d_id+1,data['id'],'SELL','MRKT',qty_init,d_p,data['ticker'],'PLACED',data['qty']))
                        conn.commit()
                        conn.close()

    elif(data['order_type']=="LMT"):
        conn=sqlite3.connect(url+"orders.db")
        cur=conn.cursor()
        if(data['ord']=="BUY"):
            query="select * from orders where ticker='"+str(data['ticker'])+"' and ord='SELL' order by timestamp;"
            op=cur.execute(query)
            if(op):
                f=1
                orders=op.fetchall()
                quant=data['qty']
                for i in range(len(orders)):
                    op=orders[i]
                    d_id=op[0]
                    d_p=op[5]
                    d_userid=op[1]
                    d_qty=op[8]
                    d_type=op[3]
                    if (d_qty==0):
                        continue
                    if (d_type=="MRKT"):
                        d_p=data['price']
                    if (d_type=="LMT" and data['price']>=d_p):
                        d_p=(data['price']+d_p)//2.0
                    if (d_type=="LMT" and data['price']<d_p):
                        continue
                    if(int(d_qty)<int(data['qty'])):
                        data['qty']=d_qty
                    conn2=sqlite3.connect(url+"users.db")
                    cur2=conn2.cursor()
                    funds=cur2.execute("select funds from users where userid=?",(data['id'],))
                    funds=funds.fetchone()[0]
                    if(d_p*data['qty']>funds):
                        d={"status":"insufficient"}
                        return d
                    else:
                        conn=sqlite3.connect(url+"orders.db")
                        cur=conn.cursor()
                        cur2.execute("update users set funds=funds-? where userid=?",(d_p*data['qty'],data['id']))
                        conn2.commit()
                        conn2.close()
                        if(data['qty']==d_qty):
                            cur.execute("update orders set status_qty=status_qty-?, status='BOOKED',timestamp=datetime(CURRENT_TIMESTAMP, 'localtime')  where ord_id=?",(data['qty'],d_id))
                            conn.commit()
                        else:
                            cur.execute("update orders set status_qty=status_qty-?, status='PARTIAL',timestamp=datetime(CURRENT_TIMESTAMP, 'localtime') where ord_id=?",(data['qty'],d_id))
                            conn.commit()
                        conn.close()
                        conn2=sqlite3.connect(url+"portfolio.db")
                        cur2=conn2.cursor()
                        check=cur2.execute(f"select * from {data['id']} where ticker='{data['ticker']}'")
                        if(len(check.fetchall())==0):
                            cur2.execute(f"insert into {data['id']}(ticker,qty) values('{data['ticker']}',{data['qty']})")
                            conn2.commit()
                        else:
                            cur2.execute(f"update {data['id']} set qty=qty+{data['qty']}, timestamp=datetime(CURRENT_TIMESTAMP, 'localtime') where ticker='{data['ticker']}'")
                            conn2.commit()

                        cur3=conn2.cursor()
                        cur3.execute(f"update {d_userid} set qty=qty-{data['qty']}, timestamp=datetime(CURRENT_TIMESTAMP, 'localtime') where ticker='{data['ticker']}'")
                        conn2.commit()
                        conn2.close()
                        conn4=sqlite3.connect(url+"users.db")
                        cur4=conn4.cursor()
                        cur4.execute("update users set funds=funds+? where userid=?",(d_p*data['qty'],d_userid))
                        conn4.commit()
                        conn4.close()
                        conn5=sqlite3.connect(url+"market.db")
                        cur5=conn5.cursor()
                        cur5.execute("update market set price=?, timestamp=datetime(CURRENT_TIMESTAMP, 'localtime') where ticker=?",(d_p,data['ticker']))
                        conn5.commit()
                        conn5.close()
                        if(data['qty']<d_qty):
                            f=0
                            break
                        data['qty']=quant-d_qty
                        quant=quant-d_qty
                        if(quant==0):
                            f=0
                            break

                if(f!=0):
                    conn=sqlite3.connect(url+"orders.db")
                    cur=conn.cursor()
                    d_id=cur.execute("select ord_id from orders order by ord_id DESC LIMIT 1")
                    d_id=d_id.fetchall()[0][0]
                    cur.execute("insert into orders(ord_id, userid, ord, order_type, qty, price,ticker,status,status_qty) values(?, ?, ?, ?, ?, ?, ?, ?, ?)",(d_id+1,data['id'],'BUY','LMT',qty_init,data['price'],data['ticker'],'PLACED',data['qty']))
                    conn.commit()
                    conn.close()


        elif(data['ord']=="SELL"):
                query="select * from orders where ticker='"+str(data['ticker'])+"' and ord='BUY' order by timestamp;"
                op=cur.execute(query)
                if(op):
                    f=1
                    orders=op.fetchall()
                    print(orders)
                    quant=data['qty']
                    con=sqlite3.connect(url+"portfolio_"+data['id']+".db")
                    c=con.cursor()
                    qty_check=c.execute("select qty from portfolio where ticker=?",(data['ticker'],))
                    if(qty_check.fetchall()[0][0]<data['qty']):
                        d={"status":"insufficient"}
                        return(d)
                    con.close()
                    for i in range(len(orders)):
                        op=orders[i]
                        d_id=op[0]
                        d_p=op[5]
                        d_userid=op[1]
                        d_qty=op[8]
                        if (d_qty==0):
                            continue
                        if (d_type=="MRKT"):
                            d_p=data['price']
                        if (d_type=="LMT" and data['price']<=d_p):
                            d_p=(data['price']+d_p)//2.0
                        if (d_type=="LMT" and data['price']>d_p):
                            continue
                        if(int(d_qty)<int(data['qty'])):
                            data['qty']=d_qty
                        conn2=sqlite3.connect(url+"users.db")
                        cur2=conn2.cursor()
                        funds=cur2.execute("select funds from users where userid=?",(d_userid,))
                        funds=funds.fetchone()[0]
                        if(d_p*data['qty']>funds):
                            continue
                        else:
                            conn=sqlite3.connect(url+"orders.db")
                            cur=conn.cursor()
                            cur2.execute("update users set funds=funds+? where userid=?",(d_p*data['qty'],data['id']))
                            conn2.commit()
                            conn2.close()
                            if(data['qty']==d_qty):
                                cur.execute("update orders set status_qty=status_qty-?, status='BOOKED',timestamp=datetime(CURRENT_TIMESTAMP, 'localtime')  where ord_id=?",(data['qty'],d_id))
                                conn.commit()
                            else:
                                cur.execute("update orders set status_qty=status_qty-?, status='PARTIAL',timestamp=datetime(CURRENT_TIMESTAMP, 'localtime') where ord_id=?",(data['qty'],d_id))
                                conn.commit()
                            conn.close()
                            conn2=sqlite3.connect(url+"portfolio.db")
                            cur2=conn2.cursor()
                            check=cur2.execute(f"select * from {d_userid} where ticker='{data['ticker']}'")
                            if(len(check.fetchall())==0):
                                cur2.execute(f"insert into {d_userid}(ticker,qty) values('{data['ticker']}',{data['qty']})")
                                conn2.commit()
                            else:
                                cur2.execute(f"update {d_userid} set qty=qty+{data['qty']}, timestamp=datetime(CURRENT_TIMESTAMP, 'localtime') where ticker='{data['ticker']}'")
                                conn2.commit()
                            cur3=conn2.cursor()
                            cur3.execute(f"update {data['id']} set qty=qty-{data['qty']}, timestamp=datetime(CURRENT_TIMESTAMP, 'localtime') where ticker='{data['ticker']}'")
                            conn2.commit()
                            conn2.close()
                            conn4=sqlite3.connect(url+"users.db")
                            cur4=conn4.cursor()
                            cur4.execute("update users set funds=funds-? where userid=?",(d_p*data['qty'],d_userid))
                            conn4.commit()
                            conn4.close()
                            conn5=sqlite3.connect(url+"market.db")
                            cur5=conn5.cursor()
                            cur5.execute("update market set price=?, timestamp=datetime(CURRENT_TIMESTAMP, 'localtime') where ticker=?",(d_p,data['ticker']))
                            conn5.commit()
                            conn5.close()
                            if(data['qty']<d_qty):
                                f=0
                                break
                            data['qty']=quant-d_qty
                            quant=quant-d_qty
                            if(quant==0):
                                f=0
                                break

                    if(f!=0):
                        conn=sqlite3.connect(url+"orders.db")
                        cur=conn.cursor()
                        d_id=cur.execute("select ord_id from orders order by ord_id DESC LIMIT 1")
                        d_id=d_id.fetchall()[0][0]
                        cur.execute("insert into orders(ord_id, userid, ord, order_type, qty, price,ticker,status,status_qty) values(?, ?, ?, ?, ?, ?, ?, ?, ?)",(d_id+1,data['id'],'SELL','LMT',qty_init,data['price'],data['ticker'],'PLACED',data['qty']))
                        conn.commit()
                        conn.close()

    d={"status":"PLACED"}
    return(d)


def register(userid,passwd,name,funds,email):
    data={'userid':userid,'password':passwd,'name':name,'funds':funds,'email':email}
    conn=sqlite3.connect(url+"users.db")
    uc=conn.execute("select userid from users where userid=? or email=?",(data['userid'],data['email']))
    if(len(uc.fetchall())==0):
        conn.execute("insert into users values(?,?,?,?,?)",(data['userid'],data['password'],data['name'],data['funds'],data['email']))
        conn.commit()
        conn=sqlite3.connect(url+"portfolio.db")
        cur=conn.cursor()
        cur.execute(f"create table {data['userid']}(ticker text, qty int, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)")
        conn.commit()
        conn.close()
        return True
    else:
        return False


def login(userid,passwd):
    # data=json.loads(flask.request.data)
    conn=sqlite3.connect(url+'users.db')
    uc=conn.execute("select userid from users where userid=? and password=?",(userid,passwd))
    if(len(uc.fetchall())==0):
        return False
    else:
        return True


def portfolio(userid):
    conn=sqlite3.connect(url+"portfolio.db")
    cur=conn.cursor()
    data=cur.execute(f"select * from {userid}")
    data=data.fetchall()
    conn.close()
    ticker=[]
    qty=[]
    timestmp=[]
    for i in data:
        ticker.append(i[0])
        qty.append(i[1])
        timestmp.append(i[2])
    return [ticker,qty,timestmp]

def orderbook(userid):
    conn=sqlite3.connect(url+"orders.db")
    cur=conn.cursor()
    data=cur.execute("select ord,order_type,ticker,price,status_qty,timestamp,qty from orders where userid=? and status_qty!=0 order by timestamp",(userid,))
    data=data.fetchall()
    conn.close()
    order=[]
    ord_type=[]
    ticker=[]
    price=[]
    status_qty=[]
    timestmp=[]
    for i in data:
        order.append(i[0])
        ord_type.append(i[1])
        ticker.append(i[2])
        price.append(i[3])
        status=f"{i[4]}/{i[6]}"
        status_qty.append(status)
        timestmp.append(i[5])

    return [order, ord_type, ticker, price, status_qty, timestmp]


def market():
    conn=sqlite3.connect(url+"market.db")
    cur=conn.cursor()
    data=cur.execute("select * from market")
    data=data.fetchall()
    conn.close()
    global market_db
    ticker=[]
    ltp=[]
    change=[]
    changep=[]
    timestmp=[]
    for i in data:
        ticker.append(i[0])
        change_=(i[1]-market_db[i[0]])
        change.append(change_)
        ltp.append(i[1])
        timestmp.append(i[2])
        changep.append(change_*100.0/market_db[i[0]])
        market_db[i]=i[1]
    return [ticker,ltp,change,changep,timestmp]


def funds_disp(name):
    conn=sqlite3.connect(url+"users.db")
    cur=conn.cursor()
    cur.execute(f"select funds from users where userid='{name}'")
    data=cur.fetchone()
    conn.close()
    return data[0]

def funds_update(name,fund,flag):
    conn=sqlite3.connect(url+"users.db")
    cur=conn.cursor()
    if(flag=="A"):
        cur.execute(f"update users set funds=funds+{fund} where userid='{name}'")
    elif(flag=="W"):
        cur.execute(f"update users set funds=funds-{fund} where userid='{name}'")
    conn.commit()
    conn.close()
    return "success"

def forgot_password(email,link):
    conn =sqlite3.connect(url+"users.db")
    cur = conn.cursor()
    cur.execute(f"select email,userid from users where email='{email}'")
    data=cur.fetchone()
    conn.close()
    if(len(data)==0):
        return "0"
    else:
        send="miniaturestockexchange@gmail.com"
        recver=email
        message = Message(From=send,
                  To=recver)
        message.Subject = "Reset Password for Miniature Stock Exchange"
        message.Html = f"""<p>Hello!<br><br>
            Here is the <a href="{link}">link</a> to reset your password.<br>
            This link will be valid for only one hour.<br><br>
            Regards,<br> Miniature Stock Exchange Team
            </p>
            """
        try:
            sender = Mailer('smtp.gmail.com',use_tls=True,usr=send,pwd='ministockexchange')
            sender.send(message)
            return data[1]
        except:
            print("error in sending mail!")
            return "1"


def reset_password(pwd,cpwd,name):
    conn =sqlite3.connect(url+"users.db")
    cur = conn.cursor()
    if(pwd==cpwd):
        cur.execute(f"update users set password='{pwd}' where userid='{name}'")
        conn.commit()
        conn.close()
        return "success"
    else:
        return "no_match"
    
    
    
def test():
    conn=sqlite3.connect(url+"market.db")
    cur=conn.cursor()
    data=cur.execute("select * from market")
    data=data.fetchall()
    conn.close()
    global market_db
    d_f={"total": len(data),"totalNotFiltered": len(data), "rows": []}
    for i in data:
        change_=(i[1]-market_db[i[0]])
        d={"ticker":i[0], "ltp":str(i[1]), "change":str(change_), "change_p":str(change_*100.0/market_db[i[0]]), "timestmp":i[2]}
        d_f["rows"].append(d)
        market_db[i]=i[1]
    return d_f
    

