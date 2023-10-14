select CUST_NAME,CUST_CITY FROM customer
select COUNT(Distinct CUST_COUNTRY) from customer 
select * from customer where CUST_CITY= 'london'
select * from customer where CUST_CODE = 'C00015'
select * from customer where CUST_COUNTRY IN ('USA' , 'India')
select * from customer where CUST_CITY != 'Bangalore'
select * from customer order by CUST_CITY desc 
select max(ORD_AMOUNT) as Maximum_amount from orders 
select count(ORD_NUM) from orders
select avg(ORD_AMOUNT) as Average_Amount from orders 
select * from customer where CUST_NAME like 'm%'
select * from customer where CUST_NAME like 's%'
select * from customer where CUST_COUNTRY IN ('Australia' , 'USA' , 'UK') 
select * from orders where ORD_DATE between '2008-01-01' and '2008-01-31'
select * from customer join orders where ORD_AMOUNT between 1000 and 4000
select * from customer join orders 