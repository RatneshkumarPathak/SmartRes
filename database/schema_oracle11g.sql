
-- SmartRes: Oracle Database 11g schema
-- Run this script in SQL Developer while connected to your schema.

CREATE TABLE sr_resources (
    resource_id NUMBER PRIMARY KEY,
    resource_name VARCHAR2(100) NOT NULL UNIQUE,
    total_units NUMBER(10) NOT NULL,
    CONSTRAINT chk_sr_resource_total CHECK (total_units >= 0)
);

CREATE TABLE sr_processes (
    process_id NUMBER PRIMARY KEY,
    process_name VARCHAR2(100) NOT NULL,
    process_status VARCHAR2(20) DEFAULT 'Active' NOT NULL,
    created_at DATE DEFAULT SYSDATE NOT NULL,
    CONSTRAINT chk_sr_process_status
        CHECK (process_status IN ('Active', 'Terminated'))
);

CREATE TABLE sr_allocations (
    process_id NUMBER NOT NULL,
    resource_id NUMBER NOT NULL,
    max_claim NUMBER(10) NOT NULL,
    allocated_units NUMBER(10) DEFAULT 0 NOT NULL,
    CONSTRAINT pk_sr_allocations
        PRIMARY KEY (process_id, resource_id),
    CONSTRAINT fk_sr_alloc_process
        FOREIGN KEY (process_id) REFERENCES sr_processes(process_id),
    CONSTRAINT fk_sr_alloc_resource
        FOREIGN KEY (resource_id) REFERENCES sr_resources(resource_id),
    CONSTRAINT chk_sr_max_claim CHECK (max_claim >= 0),
    CONSTRAINT chk_sr_allocated CHECK (allocated_units >= 0),
    CONSTRAINT chk_sr_claim_allocated
        CHECK (allocated_units <= max_claim)
);

CREATE TABLE sr_requests (
    request_id NUMBER PRIMARY KEY,
    process_id NUMBER NOT NULL,
    resource_id NUMBER NOT NULL,
    requested_units NUMBER(10) NOT NULL,
    request_status VARCHAR2(20) NOT NULL,
    reason VARCHAR2(500),
    requested_at DATE DEFAULT SYSDATE NOT NULL,
    CONSTRAINT fk_sr_req_process
        FOREIGN KEY (process_id) REFERENCES sr_processes(process_id),
    CONSTRAINT fk_sr_req_resource
        FOREIGN KEY (resource_id) REFERENCES sr_resources(resource_id),
    CONSTRAINT chk_sr_req_units CHECK (requested_units > 0),
    CONSTRAINT chk_sr_req_status
        CHECK (request_status IN ('APPROVED', 'REJECTED'))
);

CREATE TABLE sr_event_logs (
    event_id NUMBER PRIMARY KEY,
    event_type VARCHAR2(50) NOT NULL,
    details VARCHAR2(1000) NOT NULL,
    event_time DATE DEFAULT SYSDATE NOT NULL
);

-- Sequences for Oracle 11g primary-key generation
CREATE SEQUENCE sr_resources_seq START WITH 1 INCREMENT BY 1 NOCACHE;
CREATE SEQUENCE sr_processes_seq START WITH 1 INCREMENT BY 1 NOCACHE;
CREATE SEQUENCE sr_requests_seq START WITH 1 INCREMENT BY 1 NOCACHE;
CREATE SEQUENCE sr_event_logs_seq START WITH 1 INCREMENT BY 1 NOCACHE;

-- Triggers populate IDs when the caller omits them
CREATE OR REPLACE TRIGGER sr_resources_bir
BEFORE INSERT ON sr_resources
FOR EACH ROW
WHEN (NEW.resource_id IS NULL)
BEGIN
    SELECT sr_resources_seq.NEXTVAL
    INTO :NEW.resource_id
    FROM dual;
END;
/

CREATE OR REPLACE TRIGGER sr_processes_bir
BEFORE INSERT ON sr_processes
FOR EACH ROW
WHEN (NEW.process_id IS NULL)
BEGIN
    SELECT sr_processes_seq.NEXTVAL
    INTO :NEW.process_id
    FROM dual;
END;
/

CREATE OR REPLACE TRIGGER sr_requests_bir
BEFORE INSERT ON sr_requests
FOR EACH ROW
WHEN (NEW.request_id IS NULL)
BEGIN
    SELECT sr_requests_seq.NEXTVAL
    INTO :NEW.request_id
    FROM dual;
END;
/

CREATE OR REPLACE TRIGGER sr_event_logs_bir
BEFORE INSERT ON sr_event_logs
FOR EACH ROW
WHEN (NEW.event_id IS NULL)
BEGIN
    SELECT sr_event_logs_seq.NEXTVAL
    INTO :NEW.event_id
    FROM dual;
END;
/