# Makefile for Django_auction
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
	

.PHONY: populate_db
populate_db:
	 pipenv run python manage.py shell -c "from auction.models import Category; Category.objects.bulk_create([ \
	 Category(description='Sell your laptops here!', name='laptops'), \
	 Category(description='Sell your tools here!', name='tools'), \
	 Category(description='Sell your phones here!', name='phones'), \
	 Category(description='Sell your kids toys here!', name='toys')])"; \
	 pipenv run python manage.py shell -c "from auction.models import Auction, Category; from datetime import datetime; Auction.objects.bulk_create([ \
	 Auction(title='Makita drill', item_category=Category(name='tools'), description='Makita Drill description', min_value=90, buy_now=100, date_added=datetime.now(), is_active=1, total_auction_duration=1440, author_id=1), \
	 Auction(title='Laptop #1', item_category=Category(name='laptops'), description='Laptop #1 description', min_value=100, buy_now=1000, date_added=datetime.now(), is_active=1, total_auction_duration=340, author_id=2), \
	 Auction(title='Phone #1', item_category=Category(name='phones'), description='Phone #1 description', min_value=800, buy_now=1100, date_added=datetime.now(), is_active=1, total_auction_duration=40, author_id=2), \
	 Auction(title='Teddy Bear #1', item_category=Category(name='toys'), description='Phone #1 description', min_value=20, buy_now=25, date_added=datetime.now(), is_active=1, total_auction_duration=240, author_id=1)])";
	 pipenv run python manage.py shell -c "from auction.models import Auction, AuctionImage; AuctionImage.objects.bulk_create([ \
	 AuctionImage(auction=Auction(id=1), image='images/drill.png'), \
	 AuctionImage(auction=Auction(id=2), image='images/laptop.jpg'), \
	 AuctionImage(auction=Auction(id=3), image='images/phone.jpg'), \
	 AuctionImage(auction=Auction(id=4), image='images/bear.png')])"


# Sets up the database and the environment files for the first time
.PHONY: db_and_env_setup
db_and_env_setup:
	pipenv run python manage.py makemigrations auction && pipenv run python manage.py migrate auction && pipenv run python manage.py migrate


# Performs the full development environment setup
.PHONY: setup
setup: clean_pipenv dependencies db_and_env_setup createsuperuser populate_db
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
	pipenv run python3 manage.py makemigrations auction && pipenv run python3 manage.py migrate.py auction && pipenv run python3 manage.py migrate

# Create super user
.PHONY: createsuperuser
createsuperuser:
	pipenv run python manage.py shell -c "from auction.models import CustomUser; \
	CustomUser.objects.create_superuser('mp', 'mp@mp.com', 'testing321'); \
	CustomUser.objects.create_superuser('mp1', 'mp1@mp.com', 'testing321')" 

# Run the Django development server
.PHONY: run
run:
	pipenv run python manage.py runserver

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
