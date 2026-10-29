# MySQL setup

## Models

Category and Service are already defined in services/models.py and have migrations.

One Category has many Services. Each Service belongs to one Category via a
protected foreign key. A category with services cannot be deleted accidentally.
Categories and services have independent active flags. Inquiries optionally
reference a Service.

Examples:
- AC Maintenance → AC servicing
- Plumbing → Plumbing repairs
- Moving & Shifting → House & apartment shifting, Office relocation, Packing &
  unpacking, Furniture dismantling & reassembly

Django admin supports adding more categories, creating services within a category
page, filtering services by category, editing prices and SEO fields, and reviewing
inquiries.

## Install and configure

    python -m pip install -r requirements.txt
    Copy-Item .env.example .env

Edit .env locally with the real DB_USER and DB_PASSWORD. Never commit .env.
The configured cPanel database is qatarmov_qatar_handyman at localhost:3306. Shell environment values
override .env values. MySQL is the default backend; connection failures do not
silently switch to SQLite.

Django 5.0 supports MySQL 8.0.11+ or MariaDB 10.4+. Use an InnoDB database with
utf8mb4. MySQL settings enable STRICT_TRANS_TABLES and read-committed isolation.
Official reference: https://docs.djangoproject.com/en/5.0/ref/databases/#mysql-notes

## Create the database

If the database and application user do not exist, run the following from your
MySQL administration client as a user with permission to create databases/users.
Replace the example password before executing:

    CREATE DATABASE IF NOT EXISTS qatar_handyman
        CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    CREATE USER 'qatar_handyman'@'127.0.0.1'
        IDENTIFIED BY 'replace-with-a-real-password';
    GRANT ALL PRIVILEGES ON qatar_handyman.*
        TO 'qatar_handyman'@'127.0.0.1';

Set .env to that user's credentials. If you have an existing MySQL user, use that
user's credentials instead and grant access to this database.

## Initialise a new MySQL catalogue

    python manage.py check --database default
    python manage.py migrate
    python manage.py seed_services
    python manage.py createsuperuser
    python manage.py runserver

The seed command creates seven categories and eleven sample services. It preserves
existing entries. Do not run the seed command before importing existing catalogue
data if you want to retain the old records and IDs.

## Existing SQLite data

Your current db.sqlite3 is left in place. Switching backends does not copy its
records. To preserve existing categories, services and inquiries, first export
them from SQLite, then migrate and load them into the empty MySQL database:

    $env:DB_ENGINE = 'sqlite'
    python manage.py dumpdata services --indent 2 --output services-backup.json
    $env:DB_ENGINE = 'mysql'
    python manage.py migrate
    python manage.py loaddata services-backup.json

This exports only the services app, including inquiries; users/admin accounts are
not copied. Store the export privately because it may contain customer data.
Create your MySQL administrator account separately. Check record counts and the
site before removing any backup. Do not import into a catalogue already seeded.

## Checks

MySQL integration tests require a MySQL user permitted to create and drop the
isolated test database test_qatar_handyman:

    python manage.py test services

To run application tests without a configured MySQL account, explicitly select
SQLite in that shell session:

    $env:DB_ENGINE = 'sqlite'
    python manage.py check
    python manage.py test services
    Remove-Item Env:DB_ENGINE

Passing SQLite tests does not establish MySQL connectivity.


## This site's cPanel database deployment

A private `.env.cpanel` is prepared locally for the owner-supplied database
credentials. It is ignored by Git and is not automatically used by local Django.
Upload it into the PRIVATE cPanel application root and rename the server copy to
`.env`. Do not place it inside public_html or commit it. It contains a generated
production secret; retain that key across later deployments.

The database name is `qatarmov_qatar_handyman`. Verify the full user name in
cPanel's Manage My Databases: the host may add an account prefix. Add that user
to the database and grant the application's privileges. Change the shared
password before launch, updating DB_PASSWORD in the private server file. The
localhost host value refers to MySQL on the cPanel server when deployed, not a
remote connection from your development computer. Use a host-supplied alternate
hostname only if your provider specifies one.

After backing up any existing live database, activate the cPanel Python 3.12
environment, open the app root, and run:

    python manage.py check --database default
    python manage.py migrate --plan
    python manage.py migrate --noinput
    python manage.py collectstatic --noinput

Restart the Python application. `migrate` creates/updates tables but does not
copy local categories, services, reviews, users or images. Transfer an existing
MySQL database using a private SQL export/import into the intended empty target,
or use the SQLite export instructions above if SQLite is your source. Keep the
source database unchanged and never import over live enquiries without a backup.
Copy uploaded media separately. The cPanel browser session link does not grant
this local tool remote database or hosting access; live connectivity and
migration execution must be verified from the hosting environment.
