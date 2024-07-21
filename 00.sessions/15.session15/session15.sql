use db;
-- 

/* 
select [cols] 
from [tables]
*/
select * from customer;

select cust_code,cust_name 
from customer;

select *
from customer
where cust_country ='usa';



select *
from customer
where cust_country !='uk';

select *
from customer
where payment_amt>4000;

select *
from customer
where payment_amt<4000;

select *
from customer
where payment_amt>=4000;

select *
from customer
where payment_amt >=4000 and payment_amt <=7000;

select *
from customer
where payment_amt between 4000 and 7000;

select *
from customer
where payment_amt not between 4000 and 7000;

select *
from customer
where cust_country='usa' or cust_country='uk' or cust_country='india';

select *
from customer
where cust_country in ('usa','uk','india');


select *
from customer
where cust_name like 'a%' ;-- % zero or more characters

select * 
from customer
where cust_name like '_a%'; -- _ one character 

select *
from orders;

select *
from orders
where ord_date like '%-01-%';

select *
from orders
where ord_description is not null;

select *
from customer
where cust_country ='usa'
order by payment_amt;

select *
from customer
where cust_country ='usa'
order by receive_amt desc ,payment_amt desc;

select *
from customer
where cust_country = 'uk'
limit 2,3;

select payment_amt
from customer
order by payment_amt desc
limit 1;

select max(payment_amt)
from customer;

select count(*) as row_c
from customer;

select min(receive_amt)
from customer;

select avg(receive_amt)
from customer;


select sum(receive_amt)
from customer;

select concat(cust_name,'__') as Nm
from customer;

select payment_amt+receive_Amt as ss
from customer;

select cust_country,max(payment_amt)
from customer
group by cust_country
order by cust_country;

select cust_country,payment_amt
from customer
order by cust_country;

select avg(payment_amt)
from customer
group by cust_country;

select avg(payment_amt)
from customer
group by cust_country
having avg(payment_amt) >7000;

select cust_country,avg(payment_amt)
from customer
group by cust_country
having min(receive_amt) >4000;

select cust_country , count(cust_country)
from customer
group by cust_country
having avg(payment_amt) > 6000;

select month(ord_date) 
from orders;

select *
from orders
where month(ord_date)=1;

select cust_country,avg(payment_amt),count(*)
from customer
where cust_country in ('uk','usa')
group by cust_country
having min(payment_amt) >2000;



select cust_country,count(*)
from customer
where payment_amt =3000
group by cust_country;


select cust_city
from customer 
where cust_country='india';

select curdate(),current_time();



-- -- 

select cust_country
from customer
group by cust_country
having min(receive_amt) >4000;

-- sub query
select cust_city
from customer
where cust_country in (select cust_country
from customer
group by cust_country
having min(receive_amt) >4000);

select distinct(cust_country)
from customer;


-- window functions

select *
from (select cust_code,cust_name,payment_amt
, row_number() over( order by payment_amt desc) as rn
from customer) as tb
where tb.rn=4;

select *
from (select cust_code,cust_name,payment_amt
, dense_rank() over( order by payment_amt desc) as dn
from customer) as tb
where tb.dn=1;

select distinct(cust_country)
from (select cust_code,cust_name,cust_country,payment_amt
, dense_rank() over( partition by cust_country order by payment_amt desc) as dn
from customer) as t
where t.dn=2;

select cust_code,cust_name,cust_country,payment_amt
, rank() over( partition by cust_country order by payment_amt desc) as rk
from customer;

select cust_code,cust_country,cust_name,sum(payment_amt) over(partition by cust_country)
from customer;

select cust_country,cust_name,sum(payment_amt)
from customer
group by cust_country;


select customer.cust_code,cust_name,ord_amount
from customer  inner join orders 
on customer.cust_code=orders.cust_code;

select customer.cust_code,cust_name,ord_amount
from customer  left join orders 
on customer.cust_code=orders.cust_code;

select customer.cust_code,cust_name,ord_amount
from customer  right join orders 
on customer.cust_code=orders.cust_code;

select customer.cust_code,cust_name,ord_amount
from customer  join orders 
on customer.cust_code=orders.cust_code;

select * 
from agents  join orders 
on agents.agent_code=orders.agent_code;

select cust_country,ord_amount,agent_name,sum(ord_amount) over()
from customer inner join orders
on customer.cust_code=orders.cust_code
inner join agents
on agents.agent_code=orders.agent_code
where ord_amount > 2000;

