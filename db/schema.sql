create sequence seq_pst_id increment 1 start 1;
create table preset_states (
  pst_id                    bigint not null default nextval('seq_pst_id'),
  pst_name                  varchar(128),
  pst_last_managed          timestamp with time zone default null,
  pst_last_managed_by       varchar(64),
  pst_is_locked             boolean not null default false,
  pst_vms_states            json,
  constraint pk_preset_states primary key (pst_id),
  constraint uq_pst_name unique (pst_name)
);
create index i_pst_name on preset_states using btree (pst_name);
grant all privileges on preset_states to vmshepherd;
grant all privileges on sequence seq_pst_id to vmshepherd;
