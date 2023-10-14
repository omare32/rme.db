select cust_country
from customer
group by cust_country
having min(RECEIVE_AMT) >= 5000;


select cust_name
from customer
where cust_country in (select cust_country
from customer
group by cust_country
having min(RECEIVE_AMT) >= 5000)
order by 1;


select cust_name 
from customer
where cust_code in (select customer.cust_code
from customer inner join orders
on customer.cust_code=orders.cust_code
group by customer.cust_code
having count(ORD_num) >1);

select customer.cust_name,sum(orders.ord_amount)
from customer inner join orders
on customer.cust_code=orders.cust_code
group by customer.cust_name
having count(ORD_num) >1;

select cust_name,cust_country,sum(payment_amt) over()
from customer;

select cust_name,cust_country,sum(payment_amt) over(partition by cust_country)
from customer;

select cust_name,cust_country,sum(payment_amt) over(partition by cust_country order by cust_country)
from customer;

select cust_country,cust_name,PAYMENT_AMT
,row_number() over(partition by cust_country order by PAYMENT_AMT) as rn
from customer;

select cust_country,cust_name,PAYMENT_AMT
,dense_rank() over(partition by cust_country order by PAYMENT_AMT desc ) as rn
from customer;

select  distinct cust_country,payment_amt
from (select cust_country,cust_name,PAYMENT_AMT
,dense_rank() over(partition by cust_country order by PAYMENT_AMT desc) as rn
from customer) as t
where t.rn=2;

select customer.cust_name,orders.ORD_AMOUNT,customer.cust_country
,dense_rank() over(partition by customer.cust_country order by orders.ord_amount desc) as dn
from customer inner join orders
on customer.cust_code=orders.CUST_CODE;


select distinct ord_amount,cust_country
from (select customer.cust_name,orders.ORD_AMOUNT,customer.cust_country
,dense_rank() over(partition by customer.cust_country order by orders.ord_amount desc) as dn
from customer inner join orders
on customer.cust_code=orders.CUST_CODE) as t
where t.dn=2;

select * from customer;

/* insert into table_name (col1,col2,..) values (val_col1,val_col2,..)
*/

select * from orders;

insert into 
orders (ord_num,ord_amount,cust_code,agent_code,advance_amount,ord_date,ord_description)
values (200200,4444,'c00009','A002',2424,'2008-01-08','sdfasdf');



-- update
/* update tble_name set col= val where cond*/

update orders set ord_amount= 5444,ord_description='desc' where ord_num =200200;


select * from orders;
-- Delete
/* delete from table where cond*/

delete from orders where ORD_NUM=200200;


