from datetime import datetime
import json
import asyncpg
from vmshepherd.runtime import AbstractRuntimeData


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

    async def _assure_connected(self):
        if self._reconfigure:
            await self._pool.close()
            self._reconfigure = False
        if not isinstance(self._pool, asyncpg.pool.Pool) or self._pool._closed:  # pylint: disable=protected-access
            self._pool = await asyncpg.create_pool(host=self._config['host'],
                                                   port=self._config.get('port', 5432),
                                                   database=self._config['database'],
                                                   user=self._config['user'],
                                                   password=self._config['password'],
                                                   min_size=self._config.get('pool_size', 2))

    async def _set_preset_data(self, preset_name, data):
        last_managed = datetime.fromtimestamp(data['last_managed']['time'])
        last_managed_by = data['last_managed']['id']
        vms_states = json.dumps({'failed_checks': data['failed_checks']})
        await self._assure_connected()
        preset = await self._pool.fetchrow('select * from preset_states where pst_name = $1', preset_name)
        if preset:
            await self._pool.execute('''
                update preset_states set pst_last_managed = $1,
                                         pst_last_managed_by = $2,
                                         pst_vms_states = $3
                where pst_name = $4
                ''', last_managed, last_managed_by, vms_states, preset_name)
        else:
            await self._pool.execute('''
                insert into preset_states (pst_name, pst_last_managed, pst_last_managed_by, pst_vms_states)
                values ($1, $2, $3, $4)
                ''', preset_name, last_managed, last_managed_by, vms_states)

    async def _get_preset_data(self, preset_name):
        await self._assure_connected()
        preset = await self._pool.fetchrow('select * from preset_states where pst_name = $1', preset_name)
        if not preset:
            return {}
        vms_states = json.loads(preset['pst_vms_states'])
        return {
                 'last_managed': {
                   'time': datetime.timestamp(preset['pst_last_managed']),
                   'id': preset['pst_last_managed_by'],
                 },
                 'iaas': {},
                 'failed_checks': vms_states['failed_checks']
               }

    async def _acquire_lock(self, name):
        await self._assure_connected()
        async with self._pool.acquire() as con:
            is_locked = await con.fetchval('select pst_is_locked from preset_states where pst_name=$1 for update', name)
            if is_locked:
                return False
            elif is_locked is None:
                await con.execute('insert into preset_states (pst_name, pst_is_locked) values ($1, true)', name)
            else:
                await con.execute('update preset_states set pst_is_locked=true where pst_name=$1', name)
        return True

    async def _release_lock(self, name):
        await self._pool.execute('update preset_states set pst_is_locked=false where pst_name=$1', name)
        return True
