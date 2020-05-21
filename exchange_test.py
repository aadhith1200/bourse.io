import flask,json,sqlite3
from mailer import Mailer
from mailer import Message
from pathlib import Path
from datetime import datetime
from time import time
app=flask.Flask(__name__)

url=str(Path(__file__).parent.absolute())+"\\"
def order(order,order_type,price,ticker,qty,name):
    response="no"
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
                            cur2.execute(f"insert into {data['id']}(ticker,qty,avgprice) values('{data['ticker']}',{data['qty']},{data['qty']*d_p})")
                            conn2.commit()
                        else:
                            cur2.execute(f"update {data['id']} set qty=qty+{data['qty']}, timestamp=datetime(CURRENT_TIMESTAMP, 'localtime'), avgprice=avgprice+{data['qty']*d_p} where ticker='{data['ticker']}'")
                            conn2.commit()

                        cur3=conn2.cursor()
                        cur3.execute(f"select avgprice,qty from {d_userid} where ticker='{data['ticker']}'")
                        avglist=cur3.fetchone()
                        avgprice=avglist[0]/avglist[1]
                        cur3.execute(f"update {d_userid} set qty=qty-{data['qty']}, timestamp=datetime(CURRENT_TIMESTAMP, 'localtime'),avgprice={avgprice*(avglist[1]-data['qty'])} where ticker='{data['ticker']}'")
                        conn2.commit()
                        conn2.close()
                        conn4=sqlite3.connect(url+"users.db")
                        cur4=conn4.cursor()
                        cur4.execute("update users set funds=funds+? where userid=?",(d_p*data['qty'],d_userid))
                        conn4.commit()
                        conn4.close()
                        conn5=sqlite3.connect(url+"market.db")
                        cur5=conn5.cursor()
                        cur5.execute(f"select price from market where ticker='{data['ticker']}'")
                        mrktprice=cur5.fetchone()[0]
                        change=d_p-mrktprice
                        change_p=(change*100)/mrktprice
                        cur5.close()
                        cur6=conn5.cursor()
                        cur6.execute("update market set price=?, timestamp=datetime(CURRENT_TIMESTAMP, 'localtime'), change=?, change_p=?  where ticker=?",(d_p,change,change_p,data['ticker']))
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
                    response="yes"


        elif(data['ord']=="SELL"):
                query="select * from orders where ticker='"+str(data['ticker'])+"' and ord='BUY' order by timestamp;"
                op=cur.execute(query)
                if(op):
                    f=1
                    orders=op.fetchall()
                    quant=data['qty']
                    con=sqlite3.connect(url+"portfolio.db")
                    c=con.cursor()
                    qty_check=c.execute(f"select qty from {data['id']} where ticker=?",(data['ticker'],))
                    qt=qty_check.fetchone()
                    if(qt==None):
                        d={"status":"insufficient"}
                        return(d)
                    elif(qt[0]<data['qty']):
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
                                cur2.execute(f"insert into {d_userid}(ticker,qty,avgprice) values('{data['ticker']}',{data['qty']},{data['qty']*d_p})")
                                conn2.commit()
                            else:
                                cur2.execute(f"update {d_userid} set qty=qty+{data['qty']}, timestamp=datetime(CURRENT_TIMESTAMP, 'localtime'),avgprice=avgprice+{data['qty']*d_p} where ticker='{data['ticker']}'")
                                conn2.commit()

                            cur3=conn2.cursor()
                            cur3.execute(f"select avgprice,qty from {data['id']} where ticker='{data['ticker']}'")
                            avglist=cur3.fetchone()
                            avgprice=avglist[0]/avglist[1]
                            cur3.execute(f"update {data['id']} set qty=qty-{data['qty']}, timestamp=datetime(CURRENT_TIMESTAMP, 'localtime'),avgprice={avgprice*(avglist[1]-data['qty'])} where ticker='{data['ticker']}'")
                            conn2.commit()
                            conn2.close()
                            conn4=sqlite3.connect(url+"users.db")
                            cur4=conn4.cursor()
                            cur4.execute("update users set funds=funds-? where userid=?",(d_p*data['qty'],d_userid))
                            conn4.commit()
                            conn4.close()
                            conn5=sqlite3.connect(url+"market.db")
                            cur5=conn5.cursor()
                            cur5.execute(f"select price from market where ticker='{data['ticker']}'")
                            mrktprice=cur5.fetchone()[0]
                            change=d_p-mrktprice
                            change_p=(change*100)/mrktprice
                            cur5.close()
                            cur6=conn5.cursor()
                            cur6.execute("update market set price=?, timestamp=datetime(CURRENT_TIMESTAMP, 'localtime'), change=?, change_p=?  where ticker=?",(d_p,change,change_p,data['ticker']))
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
                        response="yes"

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
                        d_p=d_p
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
                            cur2.execute(f"insert into {data['id']}(ticker,qty,avgprice) values('{data['ticker']}',{data['qty']},{data['qty']*d_p})")
                            conn2.commit()
                        else:
                            cur2.execute(f"update {data['id']} set qty=qty+{data['qty']}, timestamp=datetime(CURRENT_TIMESTAMP, 'localtime'),avgprice=avgprice+{data['qty']*d_p} where ticker='{data['ticker']}'")
                            conn2.commit()
                        cur3=conn2.cursor()
                        cur3.execute(f"select avgprice,qty from {d_userid} where ticker='{data['ticker']}'")
                        avglist=cur3.fetchone()
                        avgprice=avglist[0]/avglist[1]
                        cur3.execute(f"update {d_userid} set qty=qty-{data['qty']}, timestamp=datetime(CURRENT_TIMESTAMP, 'localtime'),avgprice={avgprice*(avglist[1]-data['qty'])} where ticker='{data['ticker']}'")
                        conn2.commit()
                        conn2.close()
                        conn4=sqlite3.connect(url+"users.db")
                        cur4=conn4.cursor()
                        cur4.execute("update users set funds=funds+? where userid=?",(d_p*data['qty'],d_userid))
                        conn4.commit()
                        conn4.close()
                        conn5=sqlite3.connect(url+"market.db")
                        cur5=conn5.cursor()
                        cur5.execute(f"select price from market where ticker='{data['ticker']}'")
                        mrktprice=cur5.fetchone()[0]
                        change=d_p-mrktprice
                        change_p=(change*100)/mrktprice
                        cur5.close()
                        cur6=conn5.cursor()
                        cur6.execute("update market set price=?, timestamp=datetime(CURRENT_TIMESTAMP, 'localtime'), change=?, change_p=?  where ticker=?",(d_p,change,change_p,data['ticker']))
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
                    response="yes"

        elif(data['ord']=="SELL"):
                query="select * from orders where ticker='"+str(data['ticker'])+"' and ord='BUY' order by timestamp;"
                op=cur.execute(query)
                if(op):
                    f=1
                    orders=op.fetchall()
                    quant=data['qty']
                    con=sqlite3.connect(url+"portfolio.db")
                    c=con.cursor()
                    qty_check=c.execute(f"select qty from {data['id']} where ticker=?",(data['ticker'],))
                    qt=qty_check.fetchone()
                    if(qt==None):
                        d={"status":"insufficient"}
                        return(d)
                    elif(qt[0]<data['qty']):
                        d={"status":"insufficient"}
                        return(d)
                    con.close()
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
                        if (d_type=="LMT" and data['price']<=d_p):
                            d_p=d_p
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
                                cur2.execute(f"insert into {d_userid}(ticker,qty,avgprice) values('{data['ticker']}',{data['qty']},{data['qty']*d_p})")
                                conn2.commit()
                            else:
                                cur2.execute(f"update {d_userid} set qty=qty+{data['qty']}, timestamp=datetime(CURRENT_TIMESTAMP, 'localtime'),avgprice=avgprice+{data['qty']*d_p} where ticker='{data['ticker']}'")
                                conn2.commit()
                            cur3=conn2.cursor()
                            cur3.execute(f"select avgprice,qty from {data['id']} where ticker='{data['ticker']}'")
                            avglist=cur3.fetchone()
                            avgprice=avglist[0]/avglist[1]
                            cur3.execute(f"update {data['id']} set qty=qty-{data['qty']}, timestamp=datetime(CURRENT_TIMESTAMP, 'localtime'),avgprice={avgprice*(avglist[1]-data['qty'])} where ticker='{data['ticker']}'")
                            conn2.commit()
                            conn2.close()
                            conn4=sqlite3.connect(url+"users.db")
                            cur4=conn4.cursor()
                            cur4.execute("update users set funds=funds-? where userid=?",(d_p*data['qty'],d_userid))
                            conn4.commit()
                            conn4.close()
                            conn5=sqlite3.connect(url+"market.db")
                            cur5=conn5.cursor()
                            cur5.execute(f"select price from market where ticker='{data['ticker']}'")
                            mrktprice=cur5.fetchone()[0]
                            change=d_p-mrktprice
                            change_p=(change*100)/mrktprice
                            cur5.close()
                            cur6=conn5.cursor()
                            cur6.execute("update market set price=?, timestamp=datetime(CURRENT_TIMESTAMP, 'localtime'), change=?, change_p=?  where ticker=?",(d_p,change,change_p,data['ticker']))
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
                        response="yes"

    d={"status":"PLACED","response":response}
    return(d)


def register(userid,passwd,name,funds,email):
    data={'userid':userid,'password':passwd,'name':name,'funds':funds,'email':email}
    conn=sqlite3.connect(url+"users.db")
    uc=conn.execute("select userid from users where userid=? or email=?",(data['userid'],data['email']))
    if(len(uc.fetchall())==0):
        conn.execute("insert into users values(?,?,?,?,?,?)",(data['userid'],data['password'],data['name'],data['funds'],data['email'],""))
        conn.commit()
        conn=sqlite3.connect(url+"portfolio.db")
        cur=conn.cursor()
        cur.execute(f"create table {data['userid']}(ticker text, qty int, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, avgprice int, primaryqty int default 0)")
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


def orderbook(reqtype,userid):
    conn=sqlite3.connect(url+"orders.db")
    if (reqtype=="open"):
        cur=conn.cursor()
        cur.execute("select ord,order_type,ticker,price,status_qty,timestamp,qty from orders where userid=? and status_qty!=0 order by timestamp",(userid,))
        data=cur.fetchall()
        cur.close()
        conn.close()
        d_f={"total": len(data),"totalNotFiltered": len(data), "rows": []}
        for i in data:
            d={"order":i[0],"order_type":i[1],"ticker":i[2],"price":round(i[3],2),"qty_status":str(i[4])+"/"+str(i[6]),"timestmp":i[5]}
            d_f["rows"].append(d)
        return d_f

    if (reqtype=="exec"):
        cur=conn.cursor()
        cur.execute("select ord,order_type,ticker,price,status_qty,timestamp,qty from orders where userid=? and status_qty==0 order by timestamp",(userid,))
        data=cur.fetchall()
        cur.close()
        conn.close()
        d_f={"total": len(data),"totalNotFiltered": len(data), "rows": []}
        for i in data:
            d={"order":i[0],"order_type":i[1],"ticker":i[2],"price":round(i[3],2),"qty_status":i[6],"timestmp":i[5]}
            d_f["rows"].append(d)
        return d_f


def stockdata(sname):
    conn=sqlite3.connect(url+"market.db")
    cur=conn.cursor()
    cur.execute(f"select * from market where ticker='{sname}'")
    data=cur.fetchone()
    data=list(data)
    data[-4]=round(data[-4],2)
    data[-3]=str(datetime.strptime(data[-3], '%Y-%m-%d %H:%M:%S').strftime("%d %B %Y %I:%M:%S %p"))
    data[0]=time()*1000
    return data


def watchlist(userid,sname,status):
    conn=sqlite3.connect(url+"users.db")
    cur=conn.cursor()
    cur.execute(f"select watchlist from users where userid='{userid}'")
    data=cur.fetchone()[0]
    try:
        wlist=data.split(",")
    except:
        wlist=[]
    if(sname=="0"):
        cur.close()
        conn.close()
        qstring=""
        for i in wlist:
            qstring+="'"+i+"'"+","
        qstring="("+qstring[:-1]+")"
        conn2=sqlite3.connect(url+"market.db")
        cur2=conn2.cursor()
        cur2.execute(f"select * from market where ticker in {qstring} order by ticker")
        data=cur2.fetchall()
        cur2.close()
        conn2.close()
        d_f={"total": len(data),"totalNotFiltered": len(data), "rows": []}
        for i in data:
             d={"ticker":i[0],"ltp":round(i[1],2),"change":round(i[2],2),"change_p":round(i[3],2),"timestmp":i[4]}
             d_f["rows"].append(d)
        return d_f
    elif(status=="remove"):
            wlist.remove(sname)
            qstring=",".join(wlist)
            cur.execute(f"update users set watchlist='{qstring}' where userid='{userid}'")
            conn.commit()
            cur.close()
            conn.close()
            return "success"
    elif(status=="add"):
        if(sname in wlist):
            return "already exist"
        else:
            wlist.append(sname)
            qstring=",".join(wlist)
            cur.execute(f"update users set watchlist='{qstring}' where userid='{userid}'")
            conn.commit()
            cur.close()
            conn.close()
            return "success"


def pandl(userid,status):
    conn=sqlite3.connect(url+"portfolio.db")
    cur=conn.cursor()
    url1=url+"market.db"
    url2=url+"portfolio.db"
    cur.execute(f"attach '{url1}' as 'market'")
    cur.execute(f"attach '{url2}' as 'port'")
    cur.execute(f"select avgprice,qty,price,a.ticker from port.{userid} a inner join market.market b on b.ticker=a.ticker and qty!=0")
    data=cur.fetchall()
    conn.close()
    if(len(data)==0):
        return "portfolio empty"
    elif(status=="total"):
        pl=0
        pl_change=0
        for i in data:
            plc=(i[2]-(i[0]/i[1]))*i[1]
            pl+=plc
            pl_change+=i[0]
        return [round(pl,3),round(plc*100/pl_change,3)]
    elif(status=="table"):
        d_f={"total": len(data),"totalNotFiltered": len(data), "rows": []}
        for i in data:
             pl=(i[2]-(i[0]/i[1]))*i[1]
             pl_change=(pl*100)/i[0]
             d={"ticker":i[3],"change":round(pl,2),"change_p":round(pl_change,2)}
             d_f["rows"].append(d)
        return d_f


def portfolio(userid):
    conn=sqlite3.connect(url+"portfolio.db")
    cur=conn.cursor()
    url1=url+"market.db"
    url2=url+"portfolio.db"
    cur.execute(f"attach '{url1}' as 'market'")
    cur.execute(f"attach '{url2}' as 'port'")
    cur.execute(f"select a.ticker,price,change,change_p,qty from port.{userid} a inner join market.market b on b.ticker=a.ticker and qty!=0")
    data=cur.fetchall()
    conn.close()
    if(len(data)==0):
        return "portfolio empty"
    else:
        d_f={"total": len(data),"totalNotFiltered": len(data), "rows": []}
        for i in data:
            d={"ticker":i[0],"ltp":round(i[1],2),"change":round(i[2],2),"change_p":round(i[3],2),"qty":i[4]}
            d_f["rows"].append(d)
        return d_f


def checkticker(sname):
    conn=sqlite3.connect(url+"market.db")
    cur=conn.cursor()
    cur.execute(f"select * from market where ticker='{sname}'")
    if(len(cur.fetchall())==0):
        conn.close()
        return 0
    else:
        conn.close()
        return 1

def cancelorder(timestmp,userid):
    conn=sqlite3.connect(url+"orders.db")
    cur=conn.cursor()
    cur.execute(f"select qty,status_qty,status,ord_id from orders where timestamp='{timestmp}' and userid='{userid}'")
    data=cur.fetchone()
    if(data[2]=="PLACED"):
        cur.execute(f"delete from orders where ord_id={data[3]}")
        conn.commit()
        conn.close()
        return "success"
    elif(data[2]=="PARTIAL"):
        cur.execute(f"update orders set qty={data[0]-data[1]}, status='BOOKED', status_qty=0 where ord_id={data[3]}")
        conn.commit()
        conn.close()
        return"success"

def primaryorder(ticker,qty,userid):
    conn=sqlite3.connect(url+"portfolio.db")
    cur=conn.cursor()
    url1=url+"market.db"
    url2=url+"portfolio.db"
    cur.execute(f"attach '{url1}' as 'market'")
    cur.execute(f"attach '{url2}' as 'port'")
    cur.execute(f"select a.primaryqty, b.primaryprice, b.primaryqty from port.{userid} a inner join market.market b on b.ticker=a.ticker where a.ticker='{ticker}'")
    data=cur.fetchall()[0]
    if(data[0]+qty>10):
        return ["primary limit",10-data[0]]
    elif(data[2]+qty>100):
        return ["primary market limit",100-data[2]]
    elif(data[2]+qty<=100 and data[0]+qty<=10):
        cur.execute(f"update market.market set primaryqty=primaryqty+{qty} where ticker='{ticker}'")
        conn.commit()
        cur.execute(f"update port.{userid} set primaryqty=primaryqty+{qty}, qty=qty+{qty}, avgprice=avgprice+{qty*data[1]}, timestamp=datetime(CURRENT_TIMESTAMP, 'localtime') where ticker='{ticker}'")
        conn.commit()
        conn.close()
        conn2=sqlite3.connect(url+"users.db")
        cur2=conn2.cursor()
        cur2.execute(f"update users set funds=funds-{data[1]*qty} where userid='{userid}'")
        conn2.commit()
        conn2.close()
        return ["success",data[1]]
    else:
        return ["error",0]






