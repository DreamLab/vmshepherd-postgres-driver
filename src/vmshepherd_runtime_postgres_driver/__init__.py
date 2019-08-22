from datetime import datetime
import json
import pickle
import logging
import asyncpg
from vmshepherd.runtime import AbstractRuntimeData


queries = {
    'get_preset':
        '''
        SELECT * FROM preset_states 
        WHERE pst_name = $1
        ''',
    'upsert_preset':
        '''
        SELECT * FROM upsert_preset($1, $2, $3, $4::json)   
        ''',
    'lock_preset':
        '''
        SELECT * FROM lock_preset($1)
        ''',
    'unlock_preset':
        '''
        UPDATE preset_states 
        SET pst_is_locked=FALSE 
        WHERE pst_name=$1
        '''
}


class PostgresDriver(AbstractRuntimeData):

    def __init__(self, instance_id, config):
        super().__init__(instance_id)
        self._config = config
        self._pool = None
        self._reconfigure = False

    def reconfigure(self, config):
        if isinstance(self._pool, asyncpg.pool.Pool):
            self._reconfigure = True
        self._config = config

    async def _init_connection(self, conn):
        await conn.set_type_codec(
                'json',
                encoder=json.dumps,
                decoder=json.loads,
                schema='pg_catalog')

    async def _assure_connected(self):
        if self._reconfigure:
            await self._pool.close()
            self._reconfigure = False
        if not isinstance(self._pool, asyncpg.pool.Pool) or self._pool._closed:  # pylint: disable=protected-access
            self._pool = await asyncpg.create_pool(
                host=self._config['host'],
                port=self._config.get('port', 5432),
                database=self._config['database'],
                user=self._config['user'],
                password=self._config['password'],
                min_size=self._config.get('pool_size', 2),
                init=self._init_connection
            )

    async def _set_preset_data(self, preset_name, data):
        last_managed = datetime.fromtimestamp(data['last_managed']['time'])
        last_managed_by = data['last_managed']['id']

        # pickle vms objects
        if 'vms' in data['iaas']:
            data['iaas']['vms'] = pickle.dumps(data['iaas']['vms']).hex()
        vms_states = {'iaas': data['iaas'], 'failed_checks': data['failed_checks']}

        await self._assure_connected()

        await self._pool.execute(
            queries['upsert_preset'],
            preset_name, last_managed, last_managed_by, vms_states
        )

    async def _get_preset_data(self, preset_name):
        await self._assure_connected()

        preset = await self._pool.fetchrow(
            queries['get_preset'],
            preset_name
        )

        if not preset:
            return {}

        # unpickle vms objects
        if 'vms' in preset['pst_vms_states']['iaas']:
            vms = bytes.fromhex(preset['pst_vms_states']['iaas']['vms'])
            preset['pst_vms_states']['iaas']['vms'] = pickle.loads(vms)

        return {
                 'last_managed': {
                   'time': datetime.timestamp(preset['pst_last_managed']),
                   'id': preset['pst_last_managed_by'],
                 },
                 'iaas': preset['pst_vms_states']['iaas'],
                 'failed_checks': preset['pst_vms_states']['failed_checks']
               }

    async def _acquire_lock(self, preset_name):
        await self._assure_connected()
        try:
            async with self._pool.acquire() as con:
                is_locked = await con.fetchval(
                    queries['lock_preset'],
                    preset_name
                )
                return is_locked
        except Exception:
            logging.exception('Lock %s failed.', preset_name)
            return False

    async def _release_lock(self, preset_name):
        await self._assure_connected()
        try:
            await self._pool.execute(
                queries['unlock_preset'],
                preset_name
            )
        except Exception:
            logging.exception('Unlock %s failed.', preset_name)
