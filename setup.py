#!/usr/bin/env python3
""" Setup.py """

import os
import sys

from setuptools import find_packages, setup

sys.path.append(os.path.abspath("django_leeway"))
# pylint: disable=wrong-import-position

setup(
    name="leeway",
    version="1.0.0",
    packages=find_packages("django_leeway"),
    package_dir={"": "django_leeway"},
    include_package_data=True,
    scripts=["django_leeway/manage.py"],
    author="Tür an Tür Digitalfabrik gGmbH",
    author_email="info@integreat-app.de",
    description="Leeway simulation",
    license="Apache2.0",
    keywords="SAR Search Rescue Leeway Simulation OceanDrift",
    url="http://github.com/Digitalfabrik/leeway",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.9",
    ],
)

