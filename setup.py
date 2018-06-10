import io
import re
from os.path import abspath, dirname, join

from setuptools import find_packages, setup


def read(name):
    here = abspath(dirname(__file__))
    return io.open(
        join(here, name), encoding='utf8'
    ).read()


setup(
    name="vmshepherd-runtime-postgres-driver",
    version="1.0.0",
    author='Dreamlab - PaaS KRK',
    author_email='paas-support@dreamlab.pl',
    url='https://github.com/Dreamlab/vmshepherd-runtime-postgres-driver',
    description='Runtime and lock management based on Postgres for VmShepherd',
    long_description='%s\n%s' % (
        read('README.rst'),
        re.sub(':[a-z]+:`~?(.*?)`', r'``\1``', read('CHANGELOG.rst'))
    ),
    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    install_requires=read('requirements.txt').split('\n'),
    dependency_links=[
        'http://pypi-repo.onet/pypi/vmshepherd/'
    ],
    zip_safe=False,
    entry_points={
        'vmshepherd.driver.runtime':
        ['PostgresDriver = vmshepherd_runtime_postgres_driver:PostgresDriver'],
    },
    keywords=['vmshepherd', 'openstack', 'postgres', 'runtime', 'lock'],
    classifiers=[
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Operating System :: POSIX'
    ]
)
