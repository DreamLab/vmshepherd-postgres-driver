PGVER = 9.2
PGHOST = $(shell hostname -f)
PGADMIN = postgres
PGPASSWORD = postgres

db: clean-db requirements-db run-postgres deploy-db info-db

requirements-db:
		@sudo apt-get install -y -q docker.io >/dev/null
		@sudo apt-get install -y -q postgresql-client >/dev/null

run-postgres:
		sudo docker run --name pg_vmshepherd -p 5432:5432 -e POSTGRES_PASSWORD=$(PGPASSWORD) -e POSTGRES_USER=$(PGADMIN) -d postgres:9.2
		@sleep 5

deploy-db:
		echo "CREATE USER vmshepherd UNENCRYPTED PASSWORD 'vmshepherd';" | PGPASSWORD=$(PGPASSWORD) psql -h $(PGHOST) -U $(PGADMIN)
		echo "CREATE DATABASE vmshepherd WITH OWNER vmshepherd;" | PGPASSWORD=$(PGPASSWORD) psql -h $(PGHOST) -U $(PGADMIN)
		@echo "$(PGHOST):5432:vmshepherd:vmshepherd:vmshepherd" > ~/.pgpass
		@chmod 0600 ~/.pgpass
		cat db/schema.sql | PGPASSWORD=$(PGPASSWORD) psql -h $(PGHOST) -U $(PGADMIN) vmshepherd

clean-db:
		-sudo docker stop pg_vmshepherd
		-sudo docker rm pg_vmshepherd

info-db:
		@printf '%*s\n' "$${COLUMNS:-$$(tput cols)}" '' | tr ' ' =
		@echo 'Info'
		@echo -e '\tHost: '$(PGHOST)' (or localhost)'
		@echo -e '\tDatabase: vmshepherd\n\tPort: 5432'
		@echo -e '\tUser: vmshepherd Password: vmshepherd\n\tAdmin: $(PGADMIN) Password: $(PGPASSWORD)'
		@echo -e " \n\n\tPGPASSWORD=vmshepherd psql -h $(PGHOST)  -U vmshepherd vmshepherd"
		@printf '%*s\n' "$${COLUMNS:-$$(tput cols)}" '' | tr ' ' =

dump:
		@PGPASSWORD=$(PGPASSWORD) pg_dump -h $(PGHOST) -U $(PGADMIN) -s -f schema-full.sql vmshepherd
		@echo '> db/schema-full.sql updated'

schema-full: dump

.PHONY: run-postgres deploy-db clean-db requirements-db db info-db dump schema-full



install: requirements
		pipenv install --three

test: requirements
		pipenv run tox -r

run: db install
		@pipenv run python setup.py install
		pipenv run vmshepherd -c config/settings.example.yaml

develop:
		@pipenv run python setup.py develop
		pipenv run vmshepherd -c config/settings.example.yaml

requirements:
		@which pip3 &>/dev/null || (echo 'ERROR: Install python3 and pip3 (sudo apt-get install python3-pip)' && exit 1)
		@which pipenv || pip3 install --user pipenv -i https://pypi.python.org/pypi

clean:
		rm -rf `find . -name __pycache__`
		rm -f `find . -type f -name '*.py[co]' `
		rm -rf dist build htmlcov .tox
		rm install

.PHONY: install test show-docs run clean requirements
