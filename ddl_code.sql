create table db_admins (
    admin_name varchar(225) NOT NULL,
    admin_email varchar(254) NOT NULL,
    admin_password varchar(225) NOT NULL,
    primary key (admin_email)
);
create table government_officials (
    govt_off_name varchar(225) NOT NULL,
    govt_off_email varchar(254) NOT NULL,
    govt_off_pass varchar(225) NOT NULL,
    primary key (govt_off_email)
);
create table customer (
    customer_name varchar(225) NOT NULL,
    customer_email varchar(254) NOT NULL,
    customer_pass varchar(225) NOT NULL,
    primary key (customer_email)
);
create table time_slot (
    time_slot_id int NOT NULL,
    start_time time NOT NULL,
    end_time time NOT NULL,
    primary key (time_slot_id)
);
create table items (
    item_name varchar(225) NOT NULL,
    item_category varchar(225) NOT NULL,
    max_price numeric(8, 2) NOT NULL,
    min_price numeric(8, 2) NOT NULL,
    item_units varchar(225) NOT NULL,
    primary key (item_name)
);
create table location (
    location_id int NOT NULL,
    x_coordinate real DEFAULT NULL,
    y_coordinate real DEFAULT NULL,
    shop_number int NOT NULL,
    time_slot_id int NOT NULL,
    primary key (location_id),
    foreign key (time_slot_id) references time_slot (time_slot_id)
);
create table requests (
    request_id int NOT NULL,
    item_name varchar(225) NOT NULL,
    quantity FLOAT NOT NULL,
    resolved boolean NOT NULL,
    foreign key (item_name) references items (item_name),
    primary key (request_id)
);
create table vendor (
    vendor_name varchar(225) NOT NULL,
    vendor_email varchar(254) NOT NULL,
    vendor_pass varchar(225) NOT NULL,
    location_id int NOT NULL,
    time_slot_id int NOT NULL,
    foreign key (location_id) references location (location_id),
    foreign key (time_slot_id) references time_slot (time_slot_id),
    primary key (vendor_email)
);
create table fines (
    fine_id int NOT NULL,
    govt_off_email varchar(254) NOT NULL,
    vendor_email varchar(254) NOT NULL,
    details varchar(500) NOT NULL,
    paid boolean NOT NULL,
    foreign key (govt_off_email) references government_officials (govt_off_email),
    foreign key (vendor_email) references vendor (vendor_email),
    primary key (fine_id)
);
create table promotions (
    customer_email varchar(254) NOT NULL,
    vendor_email varchar(254) NOT NULL,
    details varchar(500) NOT NULL,
    ended varchar(254) NOT NULL,
    foreign key (customer_email) references customer (customer_email),
    foreign key (vendor_email) references vendor (vendor_email),
    primary key (customer_email, vendor_email)
);
create table stall (
    time_slot_id int NOT NULL,
    location_id int NOT NULL,
    rent numeric(8, 2) NOT NULL,
    rentee_email varchar(254) DEFAULT NULL,
    foreign key (time_slot_id) references time_slot (time_slot_id),
    foreign key (location_id) references location (location_id),
    foreign key (rentee_email) references vendor (vendor_email),
    primary key (time_slot_id, location_id)
);
create table overall_stock (
    item_name varchar(225) NOT NULL,
    vendor_email varchar(254) NOT NULL,
    selling_price numeric(8, 2) NOT NULL,
    quantity FLOAT NOT NULL,
    foreign key (item_name) references items (item_name),
    foreign key (vendor_email) references vendor (vendor_email),
    primary key (item_name, vendor_email)
);
create table sales (
    sales_id int NOT NULL,
    item_name varchar(225) NOT NULL,
    vendor_email varchar(254) NOT NULL,
    quantity FLOAT NOT NULL,
    price numeric(8, 2) NOT NULL,
    discount numeric(8, 2) NOT NULL,
    time_stamp datetime NOT NULL,
    customer_email varchar(254) NOT NULL,
    foreign key (item_name) references items (item_name),
    foreign key (vendor_email) references vendor (vendor_email),
    foreign key (customer_email) references customer (customer_email),
    primary key(sales_id)
);