#!/usr/bin/env python
# -*- coding: utf-8 -*-
#--------------------------------------------------------------------------------------------------
# Program Name:           vis
# Program Description:    Helps analyze music with computers.
#
# Filename:               setup.py
# Purpose:                Distutils Information for the VIS Framework
#
# Copyright (C) 2014 Christopher Antila
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#--------------------------------------------------------------------------------------------------
"""
.. codeauthor:: Christopher Antila <christopher@antila.ca>

Distutils information for the VIS Framework.
"""

from setuptools import setup


MAJOR = 1
MINOR = 0
PATCH = 1
VERSION = '%d.%d.%d' % (MAJOR, MINOR, PATCH)

setup(
    name = "vis-framework",
    version = VERSION,
    description = "The VIS Framework for Music Analysis",
    author = "Christopher Antila, Jamie Klassen",
    author_email = "christopher@antila.ca",
    license = "AGPLv3+",
    url = "http://elvisproject.ca/api/",
    download_url = 'https://pypi.python.org/packages/source/v/vis-framework/vis-framework-%s.tar.bz2' % VERSION,
    platforms = 'any',
    keywords = ['music', 'music analysis', 'music theory', 'counterpoint'],
    requires = [
        # NB: keep this in sync with vis/requirements.txt and vis/optional_requirements.txt
        # NB2: I left out the optional requirements and mock, since they aren't *required*
        'music21 (>= 1.7.1)',
        'pandas (>=0.12.0, <0.14)',
        ],
    install_requires = [
        'music21 >=1.7.1',
        'pandas >=0.12.0, <0.14',
        ],
    packages = [
        'vis',
        'vis.models',
        'vis.analyzers',
        'vis.analyzers.indexers',
        'vis.analyzers.experimenters',
        ],
    package_data = {'vis': ['scripts/*']},
    classifiers = [
        "Programming Language :: Python",
        "Natural Language :: English",
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Environment :: Web Environment",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Artistic Software",
        "Topic :: Multimedia :: Sound/Audio",
        "Topic :: Multimedia :: Sound/Audio :: Analysis",
        "Topic :: Scientific/Engineering :: Information Analysis",
        ],
    long_description = """\
The VIS Framework for Music Analysis
------------------------------------

VIS is a Python package that uses the music21 and pandas libraries to build a ridiculously flexible and preposterously easy system for writing computer music analysis programs.
"""
)
