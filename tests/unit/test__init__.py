import json
from datetime import datetime
from unittest.mock import ANY, MagicMock, patch

from aiounittest import AsyncTestCase, futurized
from vmshepherd_runtime_postgres_driver import PostgresDriver


def assure_connected(func):
    async def wrapper(*args):
        mock_assure_connected = patch('vmshepherd_runtime_postgres_driver.PostgresDriver._assure_connected',
                                      return_value=futurized([])).start()
        await func(*args)
        mock_assure_connected.assert_called_once()
    return wrapper


class Mock_CM(MagicMock):
    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return None


class TestPostgresDriver(AsyncTestCase):

    def setUp(self):
        self.mock_driver_config = {
            'host': 'localhost',
            'database': 'mock_db_name',
            'user': 'mock_db_user_name',
            'password': 'mock_db_password',
            'min_size': 2,
            'port': 5432
        }
        mock_vmshepherd_instance_id = 'mock_instance_id'

        self.pg_driver = PostgresDriver(mock_vmshepherd_instance_id, self.mock_driver_config)
        self.mock_preset_data = {
            'last_managed': {
                'time': 0,
                'id': 'mock_instance_id'
            },
            'iaas': {},
            'failed_checks': {
                'mock_vm_id_1': {'time': 1520899355.1556408, 'count': 1},
                'mock_vm_id_2': {'time': 1520899355.1556463, 'count': 1}
            }
        }

    def tearDown(self):
        patch.stopall()
        AsyncTestCase.tearDown(self)

    async def test_assure_connected(self):
        mock_new_pool = patch('vmshepherd_runtime_postgres_driver.asyncpg.create_pool',
                              return_value=futurized(None)).start()

        await self.pg_driver._assure_connected()  # pylint: disable=protected-access

        mock_new_pool.assert_called_once_with(**self.mock_driver_config)

    async def _test_assure_connected_reconfigure(self):
        mock_pool = patch.object(self.pg_driver, '_pool').start()
        mock_pool.close.return_value = futurized(None)
        mock_new_pool = patch('vmshepherd_runtime_postgres_driver.asyncpg.create_pool',
                              return_value=futurized(None)).start()
        self.mock_driver_config['min_size'] = 4
        self.pg_driver.reconfigure(self.mock_driver_config)

        await self.pg_driver._assure_connected()  # pylint: disable=protected-access

        mock_pool.close.assert_called_once()
        mock_new_pool.assert_called_once_with(**self.mock_driver_config)

    @assure_connected
    async def test_set_preset_data(self):
        mock_pool = patch.object(self.pg_driver, '_pool').start()
        mock_pool.fetchrow.return_value = futurized([])
        mock_pool.execute.return_value = futurized([])

        await self.pg_driver._set_preset_data('mock_preset_name',  # pylint: disable=protected-access
                                              self.mock_preset_data)

        mock_pool.fetchrow.assert_called_once_with(ANY, 'mock_preset_name')
        mock_pool.execute.assert_called_once_with(
            ANY, 'mock_preset_name',
            datetime(1970, 1, 1, 1, 0), 'mock_instance_id',
            json.dumps({'failed_checks': self.mock_preset_data['failed_checks']})
        )

    @assure_connected
    async def test_set_preset_data_exist(self):
        mock_pool = patch.object(self.pg_driver, '_pool').start()
        mock_pool.fetchrow.return_value = futurized(True)
        mock_pool.execute.return_value = futurized([])

        await self.pg_driver._set_preset_data('mock_preset_name',  # pylint: disable=protected-access
                                              self.mock_preset_data)

        mock_pool.fetchrow.assert_called_once_with(ANY, 'mock_preset_name')
        mock_pool.execute.assert_called_once_with(
            ANY, datetime(1970, 1, 1, 1, 0), 'mock_instance_id',
            json.dumps({'failed_checks': self.mock_preset_data['failed_checks']}), 'mock_preset_name'
        )

    @assure_connected
    async def test_get_preset_data(self):
        mock_pool = patch.object(self.pg_driver, '_pool').start()
        mock_pool.fetchrow.return_value = futurized(None)

        preset = await self.pg_driver._get_preset_data('mock_preset_name')  # pylint: disable=protected-access

        self.assertEqual(preset, {})

    @assure_connected
    async def test_get_preset_data_exist(self):
        mock_pool = patch.object(self.pg_driver, '_pool').start()
        mock_pool.fetchrow.return_value = futurized({
            'pst_last_managed': datetime(1970, 1, 1, 1, 0),
            'pst_last_managed_by': 'mock_instance_id',
            'pst_vms_states': '{"failed_checks": {"mock_vm_id_1": {"time": 0, "count": 2}}}'
        })

        preset = await self.pg_driver._get_preset_data('mock_preset_name')  # pylint: disable=protected-access

        self.assertEqual(preset, {
            'last_managed': {
                'time': 0,
                'id': 'mock_instance_id'
            },
            'iaas': {},
            'failed_checks': {
                'mock_vm_id_1': {'time': 0, 'count': 2}
            }
        })

    @assure_connected
    async def test_acquire_lock_already_locked(self):
        mock_pool = patch.object(self.pg_driver, '_pool').start()
        mock_con = Mock_CM()
        mock_con.fetchval.return_value = futurized(True)
        mock_pool.acquire.return_value = mock_con

        self.assertFalse(await self.pg_driver._acquire_lock('mock_preset_name'))  # pylint: disable=protected-access

    @assure_connected
    async def test_acquire_lock_new_preset_locked(self):
        mock_pool = patch.object(self.pg_driver, '_pool').start()
        mock_con = Mock_CM()
        mock_con.fetchval.return_value = futurized(None)
        mock_con.execute.return_value = futurized(None)
        mock_pool.acquire.return_value = mock_con

        self.assertTrue(await self.pg_driver._acquire_lock('mock_preset_name'))  # pylint: disable=protected-access
        mock_con.execute.assert_called_once_with(ANY, 'mock_preset_name')

    @assure_connected
    async def test_acquire_lock_existing_preset_locked(self):
        mock_pool = patch.object(self.pg_driver, '_pool').start()
        mock_con = Mock_CM()
        mock_con.fetchval.return_value = futurized(False)
        mock_con.execute.return_value = futurized(None)
        mock_pool.acquire.return_value = mock_con

        self.assertTrue(await self.pg_driver._acquire_lock('mock_preset_name'))  # pylint: disable=protected-access
        mock_con.execute.assert_called_once_with(ANY, 'mock_preset_name')
