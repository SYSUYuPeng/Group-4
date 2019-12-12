use mysql;
CREATE DATABASE coupons;
CREATE USER 'couponuser'@'%' IDENTIFIED BY '123456';
grant all PRIVILEGES on coupons.* to 'couponuser'@'%';
flush privileges;

