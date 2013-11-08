#!/usr/bin/env python
# -*- coding: utf-8 -*-
#--------------------------------------------------------------------------------------------------
# Program Name:           vis
# Program Description:    Helps analyze music with computers.
#
# Filename:               controllers/indexers/lilypond.py
# Purpose:                LilyPondIndxexer
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

The :class:`LilyPondIndexer` uses the :mod:`OutputLilyPond` module to produces the LilyPond file
that should produce a score of the input.
"""

from music21 import stream
from vis.analyzers import indexer


def indexer_func(obj):
    """
    The function that indexes.

    Parameters for Indexers Using a Score
    ======================================
    :param obj: The simultaneous event(s) to use when creating this index.
    :type obj: list of the types stored in self._types

    Parameters for Indexers Using a Series
    ======================================
    :param obj: The simultaneous event(s) to use when creating this index.
    :type obj: :obj:`pandas.Series` of :obj:`unicode`

    Returns
    =======
    :returns: The value to store for this index at this offset.
    :rtype: :obj:`unicode`
    """
    return None


class LilyPondIndexer(indexer.Indexer):
    """
    Use the :mod:`OutputLilyPond` module to produce the LilyPond file that should produce a score
    of the input.
    """

    required_score_type = stream.Score
    """
    You must provide a :class:`music21.stream.Score` to this Indexer.
    """

    possible_settings = [u'run_lilypond', u'output_pathname']
    """
    Possible settings for the :class:`LilyPondIndexer` include:

    :keyword u'run_lilypond': Whether to run LilyPond; if ``False`` or omitted, simply produce the \
        input file LilyPond requires.
    :type u'run_lilypond': boolean

    :keyword u'output_pathname': Pathname for the resulting LilyPond output file. If \
        ``u'run_lilypond'`` is ``True``, you must include this setting. If u'run_lilypond' is \
        ``False`` and you do not provide ``u'output_pathname'`` then the output file is returned \
        by :meth:`run` as a ``unicode``.
    :type u'output_pathname': ``basestring``
    """

    default_settings = {u'run_lilypond': False, u'output_pathname': None}
    """
    Default settings.
    """

    # error message for when settings say to run LilyPond, but we have no pathname
    error_no_pathname = u'LilyPondIndexer cannot run LilyPond without saving output to a file.'

    def __init__(self, score, settings=None):
        """
        Parameters
        ==========
        :param score: The :class:`Score` object to output to LilyPond.
        :type score: singleton list of :class:`music21.stream.Score`

        :param settings: All required settings.
        :type settings: ``dict`` or :dict:`None`

        Raises
        ======
        :raises: :exc:`RuntimeError` if ``score`` is the wrong type.
        :raises: :exc:`RuntimeError` if ``score`` is not a list of the same types.
        :raises: :exc:`RuntimeError` if required settings are not present in ``settings``.
        :raises: :exc:`RuntimeError` if ``u'run_lilypond'`` is ``True`` but ``u'output_pathname'`` \
            is unspecified.
        """

        # Either we shouldn't be running LilyPond or we need a pathname.
        self._settings = {}
        if u'run_lilypond' in settings and settings[u'run_lilypond'] is True:
            if u'output_pathname' in settings:
                self._settings[u'run_lilypond'] = True
                self._settings[u'output_pathname'] = settings[u'output_pathname']
            else:
                raise RuntimeError(LilyPondIndexer.error_no_pathname)
        elif u'output_pathname' in settings:
            self._settings[u'run_lilypond'] = LilyPondIndexer.default_settings[u'run_lilypond']
            self._settings[u'output_pathname'] = settings[u'output_pathname']
        else:
            self._settings[u'run_lilypond'] = LilyPondIndexer.default_settings[u'run_lilypond']
            self._settings[u'output_pathname'] = LilyPondIndexer.default_settings[u'output_pathname']

        super(LilyPondIndexer, self).__init__(score, None)

        # We won't use an indexer function; run() is just going to pass the Score to OutputLilyPond
        self._indexer_func = None

    def run(self):
        """
        Make a new index of the piece.

        Returns
        =======
        :returns: A list of the new indices. The index of each Series corresponds to the index of
            the Part used to generate it, in the order specified to the constructor. Each element
            in the Series is a basestring.
        :rtype: :obj:`list` of :obj:`pandas.Series`
        """

        # NOTE: We recommend indexing all possible voice combinations, whenever feasible.

        # To calculate each part separately:
        combinations = [[x] for x in xrange(len(self._score))]

        # To calculate all 2-part combinations:
        #for left in xrange(len(self._score)):
        #    for right in xrange(left + 1, len(self._score)):
        #        combinations.append([left, right])

        # This method returns once all computation is complete. The results are returned as a list
        # of Series objects in the same order as the "combinations" argument.
        results = self._do_multiprocessing(combinations)

        # Do applicable post-processing, like adding a label for voice combinations.

        # Return the results.
        return results