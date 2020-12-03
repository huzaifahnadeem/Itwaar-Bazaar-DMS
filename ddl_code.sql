create table time_slot (
    time_slot_id int,
    start_time time,
    end_time time,
    primary key (time_slot_id)
);
create table stall (
    time_slot_id int,
    location_id int,
    rent numeric(8, 2),
    -- using numeric(8,2) for currency
    foreign key (time_slot_id) references time_slot (time_slot_id),
    foreign key (location_id) references location (location_id),
    primary key (time_slot_id, location_id)
);
create table promotions (
    customer_email varchar(254),
    vendor_email varchar(254),
    details varchar(500),
    ended boolean,
    foreign key (customer_email) references customer (customer_email),
    foreign key (vendor_email) references vendor (vendor_email),
    primary key (customer_email, vendor_email)
);
create table location (
    location_id int,
    x_coordinate real,
    y_coordinate real,
    shop_number int,
    time_slot_id int,
    primary key (location_id),
    foreign key (time_slot_id) references time_slot (time_slot_id)
);
create table customer (
    customer_name varchar(225),
    customer_email varchar(254),
    customer_pass varchar(225),
    primary key (customer_email)
);
create table sales (
    sales_id int,
    -- item_id int,
    item_name varchar(225),
    vendor_email varchar(254),
    quantity FLOAT,
    price numeric(8, 2),
    -- before discount i.e. the standard price e.g. per kg
    discount numeric(8, 2),
    time_stamp datetime,
    customer_email varchar(254),
    foreign key (item_name) references items (item_name),
    foreign key (vendor_email) references vendor (vendor_email),
    foreign key (customer_email) references customer (customer_email),
    primary key(sales_id)
);
create table vendor (
    vendor_name varchar(225),
    vendor_email varchar(254),
    -- email char length limit according to the relevent standard
    vendor_pass varchar(225),
    location_id int,
    time_slot_id int,
    foreign key (location_id) references location (location_id),
    foreign key (time_slot_id) references time_slot (time_slot_id),
    primary key (vendor_email)
);
create table items (
    -- item_id int,
    --remove , item_name is new primary
    item_name varchar(225),
    item_category varchar(225),
    max_price numeric(8, 2),
    min_price numeric(8, 2),
    item_units varchar(225),
    primary key (item_name)
);
create table overall_stock (
    -- overall stock of the itwaar bazaar using each vendor's stock 
    -- item_id int,
    item_name varchar(225),
    vendor_email varchar(254),
    selling_price numeric(8, 2),
    quantity FLOAT,
    foreign key (item_name) references items (item_name),
    foreign key (vendor_email) references vendor (vendor_email),
    primary key (item_name, vendor_email)
);
create table requests (
    request_id int,
    -- item_id int,
    item_name varchar(225),
    quantity FLOAT,
    resolved boolean,
    foreign key (item_name) references items (item_name),
    primary key (request_id)
);
create table government_officials (
    govt_off_name varchar(225),
    govt_off_email varchar(254),
    -- email char length limit according to the relevent standard
    govt_off_pass varchar(225),
    primary key (govt_off_email)
);
create table db_admins (
    admin_name varchar(225),
    admin_email varchar(254),
    -- email char length limit according to the relevent standard
    admin_password varchar(225),
    primary key (admin_email)
);
create table fines (
    fine_id int,
    govt_off_email varchar(254),
    vendor_email varchar(254),
    details varchar(500),
    paid boolean,
    foreign key (govt_off_email) references government_officials (govt_off_email),
    foreign key (vendor_email) references vendor (vendor_email),
    primary key (fine_id)
);