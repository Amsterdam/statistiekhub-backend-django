# This Makefile is based on the Makefile defined in the Python Best Practices repository:
# https://git.datapunt.amsterdam.nl/Datapunt/python-best-practices/blob/master/dependency_management/
#
# VERSION = 2020.01.29

PYTHON = python3

dc = docker compose
run = $(dc) run --remove-orphans --rm -u ${UID}:${GID}
manage = $(run) dev python manage.py

help:                               ## Show this help.
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's/\\$$//' | sed -e 's/##//'

pip-tools:
	pip install pip-tools

install: pip-tools                  ## Install requirements and sync venv with expected state as defined in requirements.txt
	pip-sync requirements.txt requirements_dev.txt

requirements: pip-tools             ## Upgrade requirements (in requirements.in) to latest versions and compile requirements.txt
	## The --allow-unsafe flag should be used and will become the default behaviour of pip-compile in the future
	## https://stackoverflow.com/questions/58843905
	pip-compile --upgrade --output-file requirements.txt --allow-unsafe requirements.in
	pip-compile --upgrade --output-file requirements_linting.txt --allow-unsafe requirements_linting.in
	pip-compile --upgrade --output-file requirements_dev.txt --allow-unsafe requirements_dev.in

upgrade: requirements install       ## Run 'requirements' and 'install' targets

build:                              ## Build docker image
	$(dc) build

push: build                         ## Push docker image to registry
	$(dc) push

push_semver:
	VERSION=$${VERSION} $(MAKE) push
	VERSION=$${VERSION%\.*} $(MAKE) push
	VERSION=$${VERSION%%\.*} $(MAKE) push

clean:                              ## Clean docker stuff
	$(dc) down -v --remove-orphans

app:
	$(dc) up app


dev: migrate
	$(run) --service-ports dev

load_fixtures:  migrate                  ## Load initial data into database by django fixtures
	$(manage) loaddata import_theme.json \
	import_unit.json \
	import_temporaldimensiontype.json \
	import_spatialdimensiontype.json


test: lint							## Execute tests
	$(run) test pytest -m 'not integration' $(ARGS)

loadtest: migrate
	$(manage) make_partitions $(ARGS)
	$(run) locust $(ARGS)

test_data:
	$(manage) generate_test_data --num_days 25 --num_rows_per_day 2000

pdb:
	$(run) dev pytest --pdb $(ARGS)

bash:
	$(run) dev bash

shell:
	$(manage) shell_plus

dbshell:
	$(manage) dbshell

migrate:
	$(manage) migrate

migrations:
	$(manage) makemigrations $(ARGS)

trivy: 	    						## Detect image vulnerabilities
	$(dc) build --no-cache app
	trivy image --ignore-unfixed docker-registry.secure.amsterdam.nl/datapunt/statistiek_hub

kustomize:
	kustomize build manifests/overlays/local | kubectl apply -f -

undeploy_kustomize:
	kustomize build manifests/overlays/local | kubectl delete -f -

lintfix:                            ## Execute lint fixes
	$(run) linting black /app/src/$(APP) /app/tests/$(APP)
	$(run) linting autoflake /app/src --recursive --in-place --remove-unused-variables --remove-all-unused-imports --quiet
	$(run) linting isort /app/src/$(APP) /app/tests/$(APP)


lint:                               ## Execute lint checks
	$(run) linting autoflake /app/src --check --recursive --quiet
	$(run) linting isort --skip migrations --diff --check /app/src/$(APP) /app/tests/$(APP)

diff:
	@python3 ./deploy/diff.py
