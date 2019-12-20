from sqlalchemy import create_engine,ForeignKey,Column, Integer, String
from sqlalchemy.schema import Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship,sessionmaker,scoped_session
import hashlib
import random,string

engine = create_engine('mysql://couponuser:123456@localhost/coupons', pool_size=600)
Base = declarative_base()
DBSession = scoped_session(sessionmaker(bind=engine))



class User(Base):
    __tablename__ = 'users'
    id=Column(Integer,primary_key=True)
    username=Column(String(20),nullable=False,unique=True,index=True)
    kind=Column(Integer)
    password=Column(String(60),nullable=False)

    coupons=relationship("Coupon",back_populates="user")


    def __repr__(self):
        if self.kind==0:
            k="customer"
        else:
            k="seller"
        return "username:{}; kind:{}".format(self.username,k)

class Coupon(Base):
    __tablename__='coupons'

    id = Column(Integer, primary_key=True)
    username = Column(String(20),ForeignKey('users.username'),nullable=False,index=True)
    coupon_name=Column(String(60), nullable=False, index=True)
    amount=Column(Integer,default=1,nullable=False)
    stock=Column(Integer,nullable=False,default=50)
    left=Column(Integer,default=1,nullable=False)
    description= Column(String(60))

    user=relationship("User",back_populates="coupons")

    def __repr__(self):
        return "username:{}; coupons:{}; amount:{}; left: {}; description: {}"\
            .format(self.username, self.couponname, self.amount, self.left, self.description)

Index('my_index',Coupon.username,Coupon.coupon_name,unique=True)

def md5(password):
    hasher = hashlib.md5()
    password=password.encode("utf-8")
    hasher.update(password)
    return hasher.hexdigest()

if __name__ == '__main__':
    Base.metadata.create_all(engine)
    exit()
    # for final project no need to execute the following codes
    db=DBSession()

    for i in range(1,101):
        username='mycustomer'+str(i)
        db.add(User(username=username, kind=0, password=md5('123456')))
    db.add(User(username="watcher", kind=0, password=md5('123456')))

    for i in range(1,5):
        username='myseller'+str(i)
        db.add(User(username=username, kind=1, password=md5('123456')))


    for i in range(1000):
        username='myseller'+str(random.choice([1,2,3,4]))
        coupon_name ="".join([random.choice(string.ascii_uppercase + string.digits) for _ in range(20)])
        #random.choice(string.ascii_uppercase + string.digits)
        amount=random.randint(1,5)
        left=amount
        stock=random.randint(100,500)
        description="placeholder"
        db.add(Coupon(username=username,coupon_name=coupon_name,amount=amount,left=amount,stock=stock,description=description))
    db.commit()
    DBSession.remove()
