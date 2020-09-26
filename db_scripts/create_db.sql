CREATE TABLE public.version (version bigint DEFAULT 0);

CREATE TABLE logs_bad_query(
    id bigserial PRIMARY KEY,
    query text
);

CREATE TABLE users(
    id bigserial PRIMARY KEY,
    number_phone varchar(10) UNIQUE,
    OTP text,
    time_create_OTP timestamp without time zone,
    firstname varchar(255),
    lastname varchar(255),
    patronymic varchar(255),
    photo bytea,
    id_abs text,
    role int,
    status_active boolean DEFAULT true
);

CREATE TABLE login_logs(
    time_login timestamp without time zone,
    ip_address varchar(25),
    user_id bigint REFERENCES public.users(id) ON DELETE CASCADE
);
