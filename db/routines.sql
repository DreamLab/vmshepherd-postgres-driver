CREATE OR REPLACE FUNCTION lock_preset(IN preset_name CHARACTER)
	RETURNS BOOLEAN AS
$BODY$
DECLARE
	is_locked BOOLEAN;
BEGIN
	SELECT pst_is_locked into is_locked FROM preset_states WHERE pst_name=$1 FOR UPDATE;

	IF NOT FOUND THEN
		INSERT INTO preset_states (pst_name, pst_is_locked) VALUES (preset_name, true);
	ELSE
		IF is_locked THEN
			RETURN FALSE;
		ELSE
			UPDATE preset_states SET pst_is_locked=true where pst_name=preset_name;
		END IF;
	END IF;
	RETURN TRUE;

END;$BODY$
LANGUAGE plpgsql VOLATILE
COST 100;

CREATE OR REPLACE FUNCTION upsert_preset(
	IN preset_name CHARACTER,
	IN last_managed TIMESTAMP WITH TIME ZONE,
	IN last_managed_by CHARACTER,
	IN vms_states JSON)
  RETURNS VOID AS
$BODY$
DECLARE
BEGIN
	PERFORM * FROM preset_states WHERE pst_name=preset_name;

	IF NOT FOUND THEN
		INSERT INTO preset_states (pst_name, pst_last_managed, pst_last_managed_by, pst_vms_states)
        VALUES (preset_name, last_managed, last_managed_by, vms_states);
	ELSE
        UPDATE preset_states
        SET pst_last_managed = last_managed,
            pst_last_managed_by = last_managed_by,
            pst_vms_states = vms_states
        WHERE pst_name = preset_name;
	END IF;
END;$BODY$
LANGUAGE plpgsql VOLATILE
COST 100;

GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO vmshepherd;