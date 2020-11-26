# Makefile for meme_creator
#
# This Makefile has the following targets:
#
# package_managers - Sets up package managers (pipenv, node)
# clean_pipenv - Deactivates the pyenv setup
# dependencies - Installs all dependencies for a project (including mac dependencies)
# setup - Sets up the entire development environment (pyenv and dependencies)
# clean_docs - Clean the documentation folder
# clean - Clean any generated files (including documentation) and the environment
# open_docs - Open any docs generated with "make docs"
# docs - Generated sphinx docs
# validate - Run code validation
# test - Run tests
# run - Run any services for local development (databases, CSS compiliation, etc)
# version - Show the version of the package

OS = $(shell uname -s)

MODULE_NAME=meme_creator


# Print usage of main targets when user types "make" or "make help"
help:
	@echo "Please choose one of the following targets: \n"\
	      "    setup: Setup your development environment and install dependencies\n"\
	      "    test: Run tests\n"\
	      "    validate: Validate code and documentation\n"\
	      "    docs: Build Sphinx documentation\n"\
	      "    open_docs: Open built documentation\n"\
	      "    clean_setup: Teardown the entire development environment\n"\
	      "\n"\
	      "View the Makefile for more documentation about all of the available commands"
	@exit 2


# Sets up pyenv, pipenv, and node
.PHONY: package_managers
package_managers:
ifeq (${OS}, Darwin)
	brew install pyenv pipenv 2> /dev/null || true
# Ensure we remain up to date with pyenv so that new python versions are available for installation
	brew upgrade pyenv 2> /dev/null || true
endif


# Updates .env files with the template
.PHONY: update_env_files
update_env_files:
	@echo "\nThis will clobber any modifications you've made to .env and replace it with .env.template. Proceed? (Y/n): "
	@read update_env; if [ "$$update_env" = "n" ] || [ "$$update_env" = "N" ]; then exit 1; fi
	rm -f .env
	cp .env.template .env


# Builds all dependencies for a project
.PHONY: dependencies
dependencies: package_managers
ifeq (${OS}, Darwin)
# For local doc deployment
	brew install libmagic 2> /dev/null || true
endif
	pipenv sync --dev
	pipenv check


# Sets up the database and the environment files for the first time
.PHONY: db_and_env_setup
db_and_env_setup:
ifeq (${OS}, Darwin)
	pipenv run python manage.py makemigrations auction && pipenv run python manage.py migrate auction && pipenv run python manage.py migrate
endif


# Performs the full development environment setup
.PHONY: setup
setup: clean_pipenv dependencies db_and_env_setup createsuperuser
	pipenv shell

# Clean the documentation folder
.PHONY: clean_docs
clean_docs:
	cd docs && make clean


# Open the build docs (only works on Mac)
.PHONY: open_docs
open_docs:
	open docs/_build/html/index.html


# Build Sphinx autodocs
.PHONY: docs
docs: clean_docs  # Ensure docs are clean, otherwise weird render errors can result
	cd docs && make html


# Run code validation
.PHONY: validate
validate:
	pipenv run flake8 .
# Find all python modules in root directory and run pylint
	find . -type f -name '__init__.py' -maxdepth 2 | grep -o "\(.*\)/" | xargs pipenv run pylint
	make docs  # Ensure docs can be built during validation


# Run tests
.PHONY: test
test:
	pipenv run pytest --cov

# Migrate and create superuser
.PHONY: migrate
migrate:
	pipenv run python.py makemigrations auction && pipenv run python.py migrate.py auction && pipenv run python.py migrate

# Create super user
.PHONY: createsuperuser
createsuperuser:
	DJANGO_SUPERUSER_PASSWORD=testing321  python manage.py createsuperuser --username DJANGO_SUPERUSER_USERNAME --email mp@mp.com --noinput

# Run the Django development server
.PHONY: run
run:
	pipenv run python manage.py runserver


# Drop the database
.PHONY: drop_db
drop_db:
	psql postgres -c "DROP USER ${MODULE_NAME};" || true
	psql postgres -c "DROP DATABASE ${MODULE_NAME};" || true


# Cleans the pip virtualenv
.PHONY: clean_pipenv
clean_pipenv:
	pipenv --rm || true


# Clean the entire dev environment
.PHONY: clean_setup
clean_setup: clean_pipenv drop_db
	rm -f .env


# Distribution helpers for determining the version of the package
VERSION=$(shell python setup.py --version | sed 's/\([0-9]*\.[0-9]*\.[0-9]*\).*$$/\1/')

.PHONY: version
version:
	@echo ${VERSION}
