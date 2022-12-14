[![GitHub Workflow Status](https://github.com/digitalfabrik/opendrift-leeway-webgui/workflows/Tests/badge.svg)](https://github.com/digitalfabrik/opendrift-leeway-webgui/actions?query=workflow%3ATests)
[![Pylint](https://img.shields.io/badge/pylint-10.00-brightgreen)](https://www.pylint.org/)
[![PyPi](https://img.shields.io/pypi/v/opendrift-leeway-webgui.svg)](https://pypi.org/project/opendrift-leeway-webgui/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

# About

This is a little Django web application that does an [OpenDrift](https://github.com/OpenDrift/opendrift) [Leeway](https://opendrift.github.io/choosing_a_model.html) simulation with a set of provided parameters via a web form. The result is sent to a user via e-mail.

This is an experimental tool to help Search and Rescue operations. An experimental service is available at [leeway.tuerantuer.org](https://leeway.tuerantuer.org).

Sample output from the leeway tool (100 points, 1km radius, south of Lampedusa):

![Example leeway output](./.github/leeway-simulation-output.png)

# Usage

Django users have to be created in the CRUD backend, available at https://leeway.example.com/admin. E-mail addresses should be added for users as they receive the result via e-mail.

The program regularly fetches incoming mails via IMAP and starts simulations from key-value-pairs in the mail subject or text body. The sender of the mail needs to have an associated account. Allowed keys via e-mail are: `longitude`, `latitude`, `object_type`, `radius`, `duration`, `start_time`. The separator between key and value is `=`. Key-value-pairs are separated by `;` in the subject and by new lines in the text body. The date format for start date is `YYYY-MM-DD HH:MM:SS`.

# Installation

**Prerequisite:** _Python 3.8 or later is required._

1. Clone this repository and change into the new directory:
   ```bash
   gh repo clone digitalfabrik/leeway
   cd leeway
   ```
2. Create a virtual environment and activate it:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. Install the dependencies:
   ```bash
   pip install -e .[dev]
   ```
4. Create minimal config file `/etc/opendrift-leeway-webgui.ini` to enable `DEBUG` mode:
   ```dosini
   [base]
   DEBUG = True
   ```
5. Initialize the database:
   ```bash
   cd opendrift_leeway_webgui
   python3 manage.py migrate
   python3 manage.py createsuperuser
   ```

# Development Server

1. Switch into the cloned project and then into the `opendrift_leeway_webgui` subdirectory.
2. Open two terminals:
   1. In the first terminal run:
      ```bash
      source ../.venv/bin/activate
      python3 manage.py runserver
      ```
   2. In the second terminal run:
      ```bash
      source ../.venv/bin/activate
      celery -A leeway worker -l INFO
      ```


# Releasing

Run `bumpver update` to perform the following tasks with one command:

1. Bump the version in `pyproject.toml`
2. Create a version bump commit
3. Create a new version tag
4. Push the commit and tag
5. Create a new release on PyPI via GitHub Actions


# Production Server

This details the installation on Debian with Apache2 and mod_wsgi.

1. Create target directory on the production system:
   ```bash
   sudo mkdir /opt/iopendrift-leeway-webgui
   sudo chown www-data:www-data /opt/opendrift-leeway-webgui
   ```
2. Create the virtual environment:
   ```bash
   sudo -u www-data bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. Install the application into the virtual environment:
   ```bash
   pip install opendrift-leeway-webgui
   ```
4. Copy the example config file to `/etc/opendrift-leeway-webgui.ini` and fill in the template
5. Install Docker and add the `docker` group to the `www-data` user.
6. Create symlink to facilitate the Apache configuration:
   ```bash
   ln -s $(python -c "from opendrift_leeway_webgui.core import wsgi; print(wsgi.__file__)") .
   ```
7. Configure Apache2 according to the example.
8. Set up Celery worker with `leeway-celery.service` and start the service.
