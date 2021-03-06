#!/usr/bin/env python
# -*- coding: utf-8 -*-
#--------------------------------------------------------------------------------------------------
# Program Name:           vis
# Program Description:    Helps analyze music with computers.
#
# Filename:               controllers/indexers/interval.py
# Purpose:                Index vertical intervals.
#
# Copyright (C) 2013, 2014 Christopher Antila
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

Index intervals. Use the :class:`IntervalIndexer` to find vertical (harmonic) intervals between two
parts. Use the :class:`HorizontalIntervalIndexer` to find horizontal (melodic) intervals in the
same part.
"""

# disable "string statement has no effect"... it's for sphinx
# pylint: disable=W0105

from numpy import isnan
import pandas
from music21 import note, interval, pitch
from vis.analyzers import indexer


def key_to_tuple(key):
    """
    Transforms a key in the results of :meth:`IntervalIndexer.run` into a 2-tuple with the indices
    of the parts held therein.

    :param key: The key from :class:`IntervalIndexer`.
    :type key: unicode string
    :returns: The indices of parts referred to by the key.
    :rtype: tuple of int

    >>> key_to_tuple(u'5,6')
    (5, 6)
    >>> key_to_tuple(u'234522,98100')
    (234522, 98100)
    >>> var = key_to_tuple(u'1,2')
    >>> key_to_tuple(str(var[0]) + u',' + str(var[1]))
    (1, 2)
    """
    post = key.split(u',')
    return int(post[0]), int(post[1])


def interval_to_int(interv, nan_is=1):
    """
    Convert a simple interval in a string to an integer. This basically drops the quality, maintains
    direction, and converts to an integer.

    :obj:`numpy.nan` becomes the value specified by the ``nan_is`` parameter.

    :param interv: The simple interval to convert.
    :type interv: basestring or :obj:`numpy.nan`
    :param any nan_is: The value to return when ``interv`` is :obj:`numpy.nan`. The default is 1.
    :returns: An integer representation of the interval **or** the string ``'Rest'``.
    :rtype: int or string

    >>> interval_to_int('M3')
    3
    >>> interval_to_int('3')
    3
    >>> interval_to_int('-M3')
    -3
    >>> interval_to_int('-3')
    -3
    >>> interval_to_int(numpy.nan)
    1
    >>> interval_to_int('P12')  # this is a compound interval
    2  # this does not work
    >>> interval_to_int(numpy.nan, nan_is=42)
    42
    """
    # NOTE: so far this is only used by the dissonance.SuspensionIndexer, but it belongs here
    # NOTE: the first branch eliminates rests; we can't *just* use ('Rest' == interv) because
    #       the function sometimes receives "t" from the SuspensionIndexer.
    if isinstance(interv, basestring) and interv.endswith('t'):
        return 'Rest'
    elif not isinstance(interv, basestring) and isnan(interv):
        return nan_is
    elif interv.startswith('-'):  # descending motion
        return int(interv[-1:]) * -1
    else:
        return int(interv[-1:])


def real_indexer(simultaneity, simple, quality, byTones):
    """
    Used internally by the :class:`IntervalIndexer` and :class:`HorizontalIntervalIndexer`.

    :param simultaneity: A two-item iterable with the note names for the higher and lower parts,
        respectively.
    :type simultaneity: list of basestring
    :param simple: Whether intervals should be reduced to their single-octave version.
    :type simple: boolean
    :param quality: Whether the interval's quality should be prepended.
    :type quality: boolean
    :param byTones: whether the interval should be calculated using distance by tones
    :type byTones: boolean

    :returns: ``'Rest'`` if one or more of the parts is ``'Rest'``; otherwise, the interval
        between the parts.
    :rtype: unicode string
    """

    if 2 != len(simultaneity):
        return None
    else:
        try:
            upper, lower = simultaneity
            interv = interval.Interval(note.Note(lower), note.Note(upper))
        except pitch.PitchException:
            return u'Rest'
        post = u'-' if interv.direction < 0 else u''
        if quality:
            # We must get all of the quality, and none of the size (important for AA, dd, etc.)
            q_str = u''
            for each in interv.name:
                if each in u'AMPmd':
                    q_str += each
            post += q_str
        elif byTones:
            # Set post to the float of semitones/2 --> tones
            tone_flt = float(interv.semitones)/2.0
            post = tone_flt
        if simple and quality:
            post += u'8' if 8 == interv.generic.undirected \
                else unicode(interv.generic.simpleUndirected)
        elif quality:
            post += unicode(interv.generic.undirected)
        elif simple and byTones:
            post = post % 6.0 if post >= 0 else post % (-6.0)
        return post


# We give these functions to the multiprocessor; they're pickle-able, they let us choose settings,
# and the function still only requires one argument at run-time from the Indexer.mp_indexer().
def indexer_tones_simple(ecks):
    """
    Used internally by the :class:`IntervalIndexer` and :class:`HorizontalIntervalIndexer`.

    Call :func:`real_indexer` with settings to print simple intervals with quality.
    """
    return real_indexer(ecks, True, False, True)

def indexer_tones_comp(ecks):
    """
    Used internally by the :class:`IntervalIndexer` and :class:`HorizontalIntervalIndexer`.

    Call :func:`real_indexer` with settings to print simple intervals with quality.
    """
    return real_indexer(ecks, False, False, True)

def indexer_qual_simple(ecks):
    """
    Used internally by the :class:`IntervalIndexer` and :class:`HorizontalIntervalIndexer`.

    Call :func:`real_indexer` with settings to print simple intervals with quality.
    """
    return real_indexer(ecks, True, True, False)


def indexer_qual_comp(ecks):
    """
    Used internally by the :class:`IntervalIndexer` and :class:`HorizontalIntervalIndexer`.

    Call :func:`real_indexer` with settings to print compound intervals with quality.
    """
    return real_indexer(ecks, False, True, False)


def indexer_nq_simple(ecks):
    """
    Used internally by the :class:`IntervalIndexer` and :class:`HorizontalIntervalIndexer`.

    Call :func:`real_indexer` with settings to print simple intervals without quality.
    """
    return real_indexer(ecks, True, False, False)


def indexer_nq_comp(ecks):
    """
    Used internally by the :class:`IntervalIndexer` and :class:`HorizontalIntervalIndexer`.

    Call :func:`real_indexer` with settings to print compound intervals without quality.
    """
    return real_indexer(ecks, False, False, False)


class IntervalIndexer(indexer.Indexer):
    """
    Use :class:`music21.interval.Interval` to create an index of the vertical (harmonic) intervals
    between two-part combinations.

    You should provide the result of the :class:`~vis.analyzers.indexers.noterest.NoteRestIndexer`.
    However, to increase your flexibility, the constructor requires only a list of :class:`Series`.
    You may also provide a :class:`DataFrame` exactly as outputted by the
    :class:`NoteRestIndexer`.
    """

    required_score_type = 'pandas.Series'
    possible_settings = [u'simple or compound', u'quality', u'byTones']
    """
    A list of possible settings for the :class:`IntervalIndexer`.

    :keyword unicode u'simple or compound': Whether intervals should be represented in their \
        single-octave form (either ``u'simple'`` or ``u'compound'``).
    :keyword boolean u'quality': Whether to display an interval's quality.
    :keyword boolean u'byTones': Whether to calculate intervals by distance in whole-tones. Overrides quality.
    """

    default_settings = {u'simple or compound': u'compound', u'quality': False, u'byTones': False}
    "A dict of default settings for the :class:`IntervalIndexer`."

    def __init__(self, score, settings=None):
        """
        :param score: The output of :class:`NoteRestIndexer` for all parts in a piece, or a list of
            :class:`Series` of the style produced by the :class:`NoteRestIndexer`.
        :type score: list of :class:`pandas.Series` or :class:`pandas.DataFrame`
        :param dict settings: Required and optional settings. Refer to descriptions in \
            :const:`possible_settings`.
        """

        if settings is None:
            settings = {}

        # Check all required settings are present in the "settings" argument
        self._settings = {}
        if 'simple or compound' in settings:
            self._settings['simple or compound'] = settings['simple or compound']
        else:
            self._settings['simple or compound'] = \
                IntervalIndexer.default_settings['simple or compound']  # pylint: disable=C0301
        if 'quality' in settings:
            self._settings['quality'] = settings['quality']
        else:
            self._settings['quality'] = IntervalIndexer.default_settings['quality']
        if 'byTones' in settings:
            self._settings['byTones'] = settings['byTones']
        else:
            self._settings['byTones'] = IntervalIndexer.default_settings['byTones']

        super(IntervalIndexer, self).__init__(score, None)

        # Which indexer function to set?
        if self._settings['byTones']:
            if 'simple' == self._settings['simple or compound']:
                self._indexer_func = indexer_tones_simple
            else:
                self._indexer_func = indexer_tones_comp
        elif self._settings['quality']:
            if 'simple' == self._settings['simple or compound']:
                self._indexer_func = indexer_qual_simple
            else:
                self._indexer_func = indexer_qual_comp
        else:
            if 'simple' == self._settings['simple or compound']:
                self._indexer_func = indexer_nq_simple
            else:
                self._indexer_func = indexer_nq_comp

    def run(self):
        """
        Make a new index of the piece.

        :returns: A :class:`DataFrame` of the new indices. The columns have a :class:`MultiIndex`;
            refer to the example below for more details.
        :rtype: :class:`pandas.DataFrame`

        **Example:**

        >>> the_score = music21.converter.parse('sibelius_5-i.mei')
        >>> the_score.parts[5]
        (the first clarinet Part)
        >>> the_notes = NoteRestIndexer(the_score).run()
        >>> the_notes['noterest.NoteRestIndexer']['5']
        (the first clarinet Series)
        >>> the_intervals = IntervalIndexer(the_notes).run()
        >>> the_intervals['interval.IntervalIndexer']['5,6']
        (Series with vertical intervals between first and second clarinet)
        """
        combinations = []
        combination_labels = []
        # To calculate all 2-part combinations:
        for left in xrange(len(self._score)):
            for right in xrange(left + 1, len(self._score)):
                combinations.append([left, right])
                combination_labels.append(unicode(left) + u',' + unicode(right))

        # This method returns once all computation is complete. The results are returned as a list
        # of Series objects in the same order as the "combinations" argument.
        results = self._do_multiprocessing(combinations)

        # Return the results.
        return self.make_return(combination_labels, results)


class HorizontalIntervalIndexer(IntervalIndexer):
    """
    Use :class:`music21.interval.Interval` to create an index of the horizontal (melodic) intervals
    in a single part.

    You should provide the result of :class:`~vis.analyzers.noterest.NoteRestIndexer`.
    """

    def __init__(self, score, settings=None):
        """
        The output format is described in :meth:`run`.

        :param score: The output of :class:`NoteRestIndexer` for all parts in a piece.
        :type score: list of :class:`pandas.Series`
        :param dict settings: Required and optional settings. See descriptions in \
            :const:`IntervalIndexer.possible_settings`.
        """
        super(HorizontalIntervalIndexer, self).__init__(score, settings)

    def run(self):
        """
        Make a new index of the piece, with the horizontal (melodic) intervals of every individual
        part. In the output, an interval's offset is the same as that of the first note that
        comprises the interval.

        :returns: The new indices. Refer to the example below.
        :rtype: :class:`pandas.DataFrame`

        **Example:**

        >>> the_score = music21.converter.parse('sibelius_5-i.mei')
        >>> the_score.parts[5]
        (the first clarinet Part)
        >>> the_notes = NoteRestIndexer(the_score).run()
        >>> the_notes['noterest.NoteRestIndexer']['5']
        (the first clarinet Series)
        >>> the_intervals = HorizontalIntervalIndexer(the_notes).run()
        >>> the_intervals['interval.HorizontalIntervalIndexer']['5']
        (Series with melodic intervals of the first clarinet)
        """
        # This indexer is a little tricky, since we must fake "horizontality" so we can use the
        # same _do_multiprocessing() method as in the IntervalIndexer.

        # First we'll make two copies of each part's NoteRest index. One copy will be missing the
        # first element, and the other will be missing the last element. We'll also use the index
        # values starting at the second element, so that each "horizontal" interval is presented
        # as occurring at the offset of the second note involved.
        combination_labels = [unicode(x) for x in xrange(len(self._score))]
        new_parts = [x.iloc[1:] for x in self._score]
        self._score = [pandas.Series(x.values[:-1], index=x.index.tolist()[1:]) for x in self._score]

        new_zero = len(self._score)
        self._score.extend(new_parts)

        # Calculate each voice with its copy. "new_parts" is put first, so it's considered the
        # "upper voice," so ascending intervals don't get a direction.
        combinations = [[new_zero + x, x] for x in xrange(new_zero)]

        results = self._do_multiprocessing(combinations)
        # START DEBUG (this hack makes the indices start with offset 0.0, rather than the first thing after that)
        #beaches = [[0.0] for _ in xrange(len(results))]
        #for i, each_beach in enumerate(beaches):
            #each_beach.extend(results[i].index.tolist()[:-1])
        #results = [pandas.Series(x.values, index=beaches[i]) for i, x in enumerate(results)]
        # END DEBUG
        return  self.make_return(combination_labels, results)

class VariableHorizontalIntervalIndexer(IntervalIndexer):

    def __init__(self, score, settings=None):

        super(VariableHorizontalIntervalIndexer, self).__init__(score, settings)

        if settings is None or u'intervalDistance' not in settings:
            raise RuntimeError(u'VariableHorizontalIntervalIndexer requires an intervalDistance setting.')
        elif settings[u'intervalDistance'] < 0.001:
            raise RuntimeError(u'VariableHorizontalIntervalIndexer requires an intervalDistance setting no smaller than 0.001.')
        else:
            self._settings[u'intervalDistance'] = settings[u'intervalDistance']

    def run(self):

        # Get the offsets output from previous score, assume equal distribution -- i.e. noterest or filterbyoffset filters
        score_offsets = self._score[0].index.values
        # The difference in offset of each event... == quarterlength if using FilterByOffset
        increment_size = score_offsets[-1]/(len(score_offsets)-1)
        #print score_offsets 
        #print increment_size
        # Factor by which intervalDistance is more than increments
        distance_increment_factor = self._settings['intervalDistance']/increment_size
        #print int(distance_increment_factor)

        combination_labels = [unicode(x) for x in xrange(len(self._score))]
        new_parts = [x.iloc[int(distance_increment_factor):] for x in self._score]
        self._score = [pandas.Series(x.values[:-int(distance_increment_factor)], index=x.index.tolist()[int(distance_increment_factor):]) for x in self._score]

        new_zero = len(self._score)
        self._score.extend(new_parts)

        combinations = [[new_zero + x, x] for x in xrange(new_zero)]

        results = self._do_multiprocessing(combinations)

        return  self.make_return(combination_labels, results)
