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

CREATE TABLE status_code(
    id SERIAL PRIMARY KEY,
    title varchar(25)
);

INSERT INTO status_code(title) VALUES('Принято');
INSERT INTO status_code(title) VALUES('Отправлено');
INSERT INTO status_code(title) VALUES('В процессе');
INSERT INTO status_code(title) VALUES('Отклонено');
INSERT INTO status_code(title) VALUES('На доработку');

CREATE TABLE document_type(
    id SERIAL PRIMARY KEY,
    title varchar(25)
);

INSERT INTO document_type(title) VALUES('Копия трудовой');
INSERT INTO document_type(title) VALUES('Паспорт');
INSERT INTO document_type(title) VALUES('Выписка (с работы)');
INSERT INTO document_type(title) VALUES('Дополнительный документ');

CREATE TABLE documents(
    id bigserial PRIMARY KEY,
    hash varchar(100),
    user_id bigint REFERENCES public.users(id) ON DELETE CASCADE,
    document_type_id int REFERENCES public.document_type(id),
    photo text,
    dt_upload timestamp without time zone
);

CREATE TABLE document_processing(
    document_id bigint REFERENCES public.documents(id) ON DELETE CASCADE,
    status_code_id int REFERENCES public.status_code(id),
    manager_id bigint REFERENCES public.users(id) ON DELETE CASCADE
);

CREATE TABLE comments(
    document_id bigint REFERENCES public.documents(id) ON DELETE CASCADE,
    manager_id bigint REFERENCES public.users(id) ON DELETE CASCADE,
    comment text
);