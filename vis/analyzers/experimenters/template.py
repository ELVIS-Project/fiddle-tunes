#!/usr/bin/env python
# -*- coding: utf-8 -*-
#--------------------------------------------------------------------------------------------------
# Program Name:           vis
# Program Description:    Helps analyze music with computers.
#
# Filename:               controllers/experimenters/template.py
# Purpose:                Template experimenter
#
# Copyright (C) 2013 Christopher Antila
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
.. codeauthor:: Christopher Antila <crantila@fedoraproject.org>

Template for writing a new experimenter. Use this class to help write a new :class`Experimenter` \
subclass. The :class:`TemplateExperimenter` does nothing, and should only be used by programmers.
"""
# NOTE: you should replace my name with yours, in the "codeauthor" directive above

from vis.analyzers import experimenter


class TemplateExperimenter(experimenter.Experimenter):
    """
    Template for an :class:`Experimenter` subclass.
    """

    possible_settings = [u'fake_setting']
    """
    This is a list of basestrings that are the names of the settings used in this experimenter.
    Specify the types and reasons for each setting as though it were an argument list, like this:

    :keyword u'fake_setting': This is a fake setting.
    :type u'fake_setting': boolean
    """

    default_settings = {}
    """
    The default values for settings named in :const:`possible_settings`. If a setting doesn't have
    a value in this constant, then it must be specified to the constructor at runtime, or the
    constructor should raise a :exc:`RuntimeException`.
    """

    def __init__(self, index, settings=None):
        """
        Parameters
        ==========
        :param index: The indices or experimental results to use for this experiment.
        :type index: list, nested lists, or dict of pandas.Series or pandas.DataFrame, or simply
            the pandas object itself.

        :param settings: A dict of all the settings required by this Experimenter. All required
            settings should be listed in subclasses. Default is None.
        :type settings: :obj:`dict` or :obj:`None`

        Raises
        ======
        :raises: :exc:`RuntimeError` if required settings are not present in the ``settings`` \
            argument.
        """

        # Check all required settings are present in the "settings" argument. You must ignore
        # extra settings.
        # If there are no settings, you may safely remove this.
        if settings is None:
            self._settings = {}

        # Change "TemplateExperimenter" to the current class name. The superclass will handle the
        # "index" and "mpc" arguments, but you should have processed "settings" above, so it should
        # not be sent to the superclass constructor.
        super(TemplateExperimenter, self).__init__(index, None)

    def run(self):
        """
        Run an experiment on a piece.

        Returns
        =======
        :returns: The result of the experiment. Each experiment should describe its data storage.
        :rtype: :class:`pandas.Series` or :class:`pandas.DataFrame`
        """

        # NOTE: We recommend experimenting all possible combinations of anything, when feasible.

        # You will need to write this yourself; we recommend you use self._do_multiprocessing()
        # as an easy way to use the MPController for multiprocessing.
        pass
