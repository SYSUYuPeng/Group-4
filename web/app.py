from flask import Flask,request,jsonify
from functools import wraps
from models import DBSession,User,Coupon,md5
import json,base64

app=Flask(__name__)

def returnsalercoupons(db, username, page):
    coupons = db.query(Coupon).filter(Coupon.username == username).filter(Coupon.left > 0).offset((page-1)*20).limit(20).all()
    data = []
    for coupon in coupons:
        each_coupon = dict()
        each_coupon['name'] = coupon.coupon_name
        each_coupon['amount'] = coupon.amount
        each_coupon['left'] = coupon.left
        each_coupon['stock'] = coupon.stock
        each_coupon['description'] = coupon.description
        data.append(each_coupon)
    if len(data)==0:
        status_code=204
    else:
        status_code=200
    return data,status_code

def returncustomercoupons(db,username):
    coupons=db.query(Coupon).filter(Coupon.username==username).all()
    data = []
    for coupon in coupons:
        each_coupon = dict()
        each_coupon['name'] = coupon.coupon_name
        each_coupon['stock'] = coupon.stock
        each_coupon['description'] = coupon.description
        data.append(each_coupon)
    if len(data)==0:
        status_code=204
    else:
        status_code=200
    return data,status_code

def get_auth_info():
    auth_info = base64.b64decode(request.headers.get('authorization'))
    auth_info = json.loads(auth_info.decode('utf-8'))
    return auth_info

def login_required(f):
    @wraps(f)
    def wrap(*args,**kwargs):
        if request.headers.get('authorization')==None:
            response = jsonify(errMsg="login information required")
            response.status_code = 401
            return response
        try:
            data =get_auth_info()
        except Exception:
            response = jsonify(errMsg="invalid authorization information")
            response.status_code = 401
            return response
        return f(*args,**kwargs)
    return wrap

@app.route('/api/users',methods=['GET','POST'])
def register():
    if request.method=='GET':
        return jsonify(msg="Please register")
    else:
        try:
            data=json.loads(request.data.decode('utf8'))
            username=data.get("username")
            password=data.get("password")
            kind=data.get("kind")
        except Exception:
            response = jsonify(errMsg="wrong format")
            response.status_code = 400
            return response

        if username==None or password==None or kind==None:
            response = jsonify(errMsg="fields not complete")
            response.status_code = 400
            return response
        if kind=="customer":
            kind=0
        elif kind=="saler":
            kind=1
        else:
            response=jsonify(errMsg="fields with illegal value")
            response.status_code=400
            return response

        db=DBSession()
        if db.query(User).filter(User.username==username).count()!=0:
            response=jsonify(errMsg="user already exists")
            response.status_code=400
            DBSession.remove()
            return response
        user=User(username=username,password=md5(password),kind=kind)
        db.add(user)
        db.commit()
        response=jsonify(msg="register successfully")
        response.status_code=201
        DBSession.remove()
        return response

@app.route('/api/auth',methods=['GET','POST'])
def login():
    if request.method=="GET":
        return jsonify(msg="please login")

    try:
        data = json.loads(request.data.decode('utf8'))
        username = data.get("username")
        password = data.get("password")
    except Exception:
        response = jsonify(errMsg="wrong format")
        response.status_code = 400
        return response

    if username==None or password==None:
        response=jsonify(errMsg="fields not complete")
        response.status_code=401
        return response

    db=DBSession()
    results=db.query(User).filter(User.username==username).filter(User.password==md5(password))
    # if successfully logged in
    if results.count()==1:
        user=results.first()
        login_info=dict()
        login_info['user_id']=user.id
        login_info['username']=user.username
        login_info['kind']=user.kind
        authorization=base64.b64encode(json.dumps(login_info).encode('utf-8'))
        if user.kind==0:
            kind="customer"
        else:
            kind="saler"
        response=jsonify(kind=kind)
        response.headers['authorization']=authorization
        response.status_code=200
        DBSession.remove()
        return response
    # if login failed
    response = jsonify(errMsg="login failed")
    response.status_code = 401
    DBSession.remove()
    return response

@app.route("/api/users/<username>/coupons",methods=['GET','POST'])
@login_required
def addreadcoupons(username):
    auth_info=get_auth_info()

    # get method to get the page for different kinds of users
    if request.method=='GET':
        try:
            page=int(request.args.get('page'))
        except Exception:
            page=1
        if page<=0:
            page=1

        #check if username exists
        db = DBSession()
        user=db.query(User).filter(User.username==username).first()
        if not user:
            response=jsonify(errMsg="username does not exist")
            response.status_code=401
            DBSession.remove()
            return response

        # usernames different
        if auth_info['username']!=username:
            # the asked username is a customer
            if user.kind==0:
                response=jsonify(errMsg="usernames different and the asked username is a customer")
                response.status_code=401
                DBSession.remove()
                return response
            # the asked username is a saler
            else:
                # return the left 20 coupons of that saler
                data,status_code=returnsalercoupons(db, username, page)
                response=jsonify(data=data)
                response.status_code=status_code
                DBSession.remove()
                return response
        else:
            # usernames identical
            if auth_info['kind']==1:
                # saler
                # return the left 20 coupons of that saler
                data,status_code=returnsalercoupons(db, username, page)
                response = jsonify(data=data)
                response.status_code=status_code
                DBSession.remove()
                return response
            else:
                # customer
                # return the acquired coupons for that customer
                data,status_code=returncustomercoupons(db,username)
                response = jsonify(data=data)
                response.status_code=status_code
                DBSession.remove()
                return response


    # post method to add coupons
    try:
        coupon_info = json.loads(request.data.decode('utf8'))
    except Exception:
        response = jsonify(errMsg='wrong coupon information')
        response.status_code = 400
        return response

    coupon_name = coupon_info.get('name')
    amount=coupon_info.get('amount')
    description=coupon_info.get('description')
    stock=coupon_info.get('stock')

    # check legality of inputs
    # only salers could create coupons
    if auth_info['kind']!=1:
        response=jsonify(errMsg='Customers can not add a coupon')
        response.status_code=400
        return response
    if coupon_name==None or amount==None or stock==None:
        response=jsonify(errMsg='fields not complete')
        response.status_code=400
        return response
    try:
        amount=int(amount)
        stock=int(stock)
    except ValueError:
        response = jsonify(errMsg='amount or stock must be numbers')
        response.status_code = 400
        return response

    # add coupon to the database
    db=DBSession()
    coupon_info=Coupon(username=auth_info['username'],coupon_name=coupon_name,
                  amount=amount,left=amount,stock=stock,description=description)
    try:
        db.add(coupon_info)
        db.commit()
    except Exception:
        response=jsonify(errMsg="coupons already exists")
        response.status_code=400
        DBSession.remove()
        return response

    response=jsonify(msg="coupon added successfully")
    response.status_code=201
    DBSession.remove()
    return response


@app.route("/api/users/<username>/coupons/<couponname>",methods=['PATCH'])
@login_required
def acquire_coupons(username,couponname):
    # select for update example
    auth_info=get_auth_info()
    if auth_info['kind']!=0:
        response = jsonify(errMsg='saler could not acquire a coupon')
        response.status_code = 400
        return response

    db=DBSession()
    user=db.query(User).filter(User.username==username).first()
    if not user or user.kind==0:
        response = jsonify(errMsg="the username must be valid and a saler")
        response.status_code = 400
        DBSession.remove()
        return response

    # get the coupon of a saler
    coupon=db.query(Coupon).filter(Coupon.username==username)\
        .filter(Coupon.coupon_name == couponname).with_for_update().first()
    if coupon and coupon.left>0:
        db.add(Coupon(username=auth_info['username'],
                      coupon_name=coupon.coupon_name,stock=coupon.stock,description=coupon.description))
        coupon.left-=1
        try:
            db.commit()
        except Exception:
            # the user already has the coupon
            response=jsonify(errMsg="already has the coupon")
            response.status_code=400
            DBSession.remove()
            return response
        # acquire the coupon successfully
        response=jsonify(msg="coupon acquired successfully")
        response.status_code=201
        DBSession.remove()
        return response
    response = jsonify(errMsg="invalid coupon_name or no left coupons")
    response.status_code=400
    DBSession.remove()
    return response


if __name__=="__main__":
    app.run(port=8000,debug=True)