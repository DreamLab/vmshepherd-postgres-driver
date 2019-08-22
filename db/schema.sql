CREATE SEQUENCE seq_pst_id INCREMENT 1 START 1;
CREATE TABLE preset_states (
    pst_name                  VARCHAR(128),
    pst_last_managed          TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    pst_last_managed_by       VARCHAR(64),
    pst_is_locked             BOOLEAN NOT NULL DEFAULT FALSE,
    pst_vms_states            JSON,
    CONSTRAINT pk_preset_states PRIMARY KEY (pst_name)
);

GRANT ALL PRIVILEGES ON preset_states TO vmshepherd;
GRANT ALL PRIVILEGES ON sequence seq_pst_id TO vmshepherd;
