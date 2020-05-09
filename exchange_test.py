import flask,json,psycopg2,sqlite3
from pathlib import Path
app=flask.Flask(__name__)

url=str(Path(__file__).parent.absolute())+"\\"

def order():
    data=json.loads(flask.request.data)
    #print(data)
    if(data['order_type']=="MRKT"):
        #conn = psycopg2.connect("dbname=orders user = postgres password=aadhith868")
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
                        conn2=sqlite3.connect(url+"portfolio_"+data['id']+".db")
                        cur2=conn2.cursor()
                        check=cur2.execute("select * from portfolio where ticker=?",(data['ticker'],))
                        if(len(check.fetchall())==0):
                            cur2.execute("insert into portfolio(ticker,qty) values(?,?)",(data['ticker'],data['qty']))
                            conn2.commit()
                        else:
                            cur2.execute("update portfolio set qty=qty+?, timestamp=datetime(CURRENT_TIMESTAMP, 'localtime') where ticker=?",(data['qty'],data['ticker']))
                            conn2.commit()
                        conn2.close()
                        conn3=sqlite3.connect(url+"portfolio_"+d_userid+".db")
                        cur3=conn3.cursor()
                        cur3.execute("update portfolio set qty=qty-?, timestamp=datetime(CURRENT_TIMESTAMP, 'localtime') where ticker=?",(data['qty'],data['ticker']))
                        conn3.commit()
                        conn3.close()
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
                    cur.execute("insert into orders(ord_id, userid, ord, order_type, qty, price,ticker,status,status_qty) values(?, ?, ?, ?, ?, ?, ?, ?, ?)",(d_id+1,data['id'],'BUY','MRKT',data['qty'],d_p,data['ticker'],'PLACED',data['qty']))
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
                            conn2=sqlite3.connect(url+"portfolio_"+d_userid+".db")
                            cur2=conn2.cursor()
                            check=cur2.execute("select * from portfolio where ticker=?",(data['ticker'],))
                            if(len(check.fetchall())==0):
                                cur2.execute("insert into portfolio(ticker,qty) values(?,?)",(data['ticker'],data['qty']))
                                conn2.commit()
                            else:
                                cur2.execute("update portfolio set qty=qty+?, timestamp=datetime(CURRENT_TIMESTAMP, 'localtime') where ticker=?",(data['qty'],data['ticker']))
                                conn2.commit()
                            conn2.close()
                            conn3=sqlite3.connect(url+"portfolio_"+data['id']+".db")
                            cur3=conn3.cursor()
                            cur3.execute("update portfolio set qty=qty-?, timestamp=datetime(CURRENT_TIMESTAMP, 'localtime') where ticker=?",(data['qty'],data['ticker']))
                            conn3.commit()
                            conn3.close()
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
                        cur.execute("insert into orders(ord_id, userid, ord, order_type, qty, price,ticker,status,status_qty) values(?, ?, ?, ?, ?, ?, ?, ?, ?)",(d_id+1,data['id'],'SELL','MRKT',data['qty'],d_p,data['ticker'],'PLACED',data['qty']))
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
                        conn2=sqlite3.connect(url+"portfolio_"+data['id']+".db")
                        cur2=conn2.cursor()
                        check=cur2.execute("select * from portfolio where ticker=?",(data['ticker'],))
                        if(len(check.fetchall())==0):
                            cur2.execute("insert into portfolio(ticker,qty) values(?,?)",(data['ticker'],data['qty']))
                            conn2.commit()
                        else:
                            cur2.execute("update portfolio set qty=qty+?, timestamp=datetime(CURRENT_TIMESTAMP, 'localtime') where ticker=?",(data['qty'],data['ticker']))
                            conn2.commit()
                        conn2.close()
                        conn3=sqlite3.connect(url+"portfolio_"+d_userid+".db")
                        cur3=conn3.cursor()
                        cur3.execute("update portfolio set qty=qty-?, timestamp=datetime(CURRENT_TIMESTAMP, 'localtime') where ticker=?",(data['qty'],data['ticker']))
                        conn3.commit()
                        conn3.close()
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
                    cur.execute("insert into orders(ord_id, userid, ord, order_type, qty, price,ticker,status,status_qty) values(?, ?, ?, ?, ?, ?, ?, ?, ?)",(d_id+1,data['id'],'BUY','LMT',data['qty'],data['price'],data['ticker'],'PLACED',data['qty']))
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
                            conn2=sqlite3.connect(url+"portfolio_"+d_userid+".db")
                            cur2=conn2.cursor()
                            check=cur2.execute("select * from portfolio where ticker=?",(data['ticker'],))
                            if(len(check.fetchall())==0):
                                cur2.execute("insert into portfolio(ticker,qty) values(?,?)",(data['ticker'],data['qty']))
                                conn2.commit()
                            else:
                                cur2.execute("update portfolio set qty=qty+?, timestamp=datetime(CURRENT_TIMESTAMP, 'localtime') where ticker=?",(data['qty'],data['ticker']))
                                conn2.commit()
                            conn2.close()
                            conn3=sqlite3.connect(url+"portfolio_"+data['id']+".db")
                            cur3=conn3.cursor()
                            cur3.execute("update portfolio set qty=qty-?, timestamp=datetime(CURRENT_TIMESTAMP, 'localtime') where ticker=?",(data['qty'],data['ticker']))
                            conn3.commit()
                            conn3.close()
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
                        cur.execute("insert into orders(ord_id, userid, ord, order_type, qty, price,ticker,status,status_qty) values(?, ?, ?, ?, ?, ?, ?, ?, ?)",(d_id+1,data['id'],'SELL','LMT',data['qty'],data['price'],data['ticker'],'PLACED',data['qty']))
                        conn.commit()
                        conn.close()

    d={"status":"PLACED"}
    return(d)


def register(userid,passwd,name,funds):
    data={'userid':userid,'password':passwd,'name':name,'funds':funds}
    conn=sqlite3.connect(url+"users.db")
    uc=conn.execute("select userid from users where userid=?",(data['userid'],))
    if(len(uc.fetchall())==0):
        conn.execute("insert into users values(?,?,?,?)",(data['userid'],data['password'],data['name'],data['funds']))
        conn.commit()
        conn=sqlite3.connect(url+"portfolio_"+data['userid']+".db")
        cur=conn.cursor()
        cur.execute("create table portfolio(ticker text, qty int, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)")
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


def portfolio():
    data=json.loads(flask.request.data)
    userid=data['userid']
    conn=sqlite3.connect(url+"portfolio_"+userid+".db")
    cur=conn.cursor()
    data=cur.execute("select * from portfolio")
    data=data.fetchall()
    conn.close()
    l=[]
    for i in data:
        d={"ticker":i[0],"qty":i[1],"timestamp":i[2]}
        l.append(d)
        d={}
    return json.dumps(l)


def orderbook():
    data=json.loads(flask.request.data)
    userid=data['userid']
    conn=sqlite3.connect(url+"orders.db")
    cur=conn.cursor()
    data=cur.execute("select ord,order_type,ticker,price,status_qty,timestamp from orders where userid=? and status_qty!=0",(userid,))
    data=data.fetchall()
    conn.close()
    l=[]
    for i in data:
        d={"ord":i[0],"ord_type":i[1],"ticker":i[2],"price":i[3],"status_qty":i[4],"timestamp":i[5]}
        l.append(d)
        d={}
    return json.dumps(l)


def market():
    conn=sqlite3.connect(url+"market.db")
    cur=conn.cursor()
    data=cur.execute("select * from market")
    data=data.fetchall()
    conn.close()
    l=[]
    for i in data:
        d={"ticker":i[0],"price":i[1],"timestamp":i[2]}
        l.append(d)
        d={}
    return json.dumps(l)




