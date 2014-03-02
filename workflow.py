#!/usr/bin/env python
# -*- coding: utf-8 -*-
#--------------------------------------------------------------------------------------------------
# Program Name:           vis
# Program Description:    Helps analyze music with computers.
#
# Filename:               controllers/workflow.py
# Purpose:                Workflow Controller
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

The ``workflow`` module holds the :class:`WorkflowManager`, which automates several common music
analysis patterns for counterpoint. The :class:`TemplateWorkflow` class is a template for writing
new ``WorkflowManager`` classes.
"""

import ast
import subprocess
import pandas
from vis.models import indexed_piece
from vis.models.aggregated_pieces import AggregatedPieces
from vis.analyzers.indexers import noterest, interval, ngram, offset, repeat
from vis.analyzers.experimenters import frequency, aggregator


class WorkflowManager(object):
    """
    :parameter pathnames: A list of pathnames.
    :type pathnames: ``list`` of ``basestring``

    The :class:`WorkflowManager` automates several common music analysis patterns for counterpoint.
    Use the ``WorkflowManager`` with these four tasks:

    * :meth:`load`, to import pieces from symbolic data formats.
    * :meth:`run`, to perform a pre-defined analysis.
    * :meth:`output`, to output a visualization of the analysis results.
    * :meth:`export`, to output a text-based version of the analysis results.

    Before you analyze, you may wish to use these methods:

    * :meth:`metadata`, to get or set the metadata of a specific :class:`IndexedPiece` managed by \
        this ``WorkflowManager``.
    * :meth:`settings`, to get or set a setting related to analysis (for example, whether to \
        display the quality of intervals).

    You may also treat a ``WorkflowManager`` as a container:

    >>> wm = WorkflowManager('piece1.mxl', 'piece2.krn')
    >>> len(wm)
    2
    >>> ip = wm[1]
    >>> type(ip)
    <class 'vis.models.indexed_piece.IndexedPiece'>
    """

    # Instance Variables
    # - self._data: list of IndexedPieces
    # - self._result: result of the most recent call to run()
    # - self._settings: settings unique per piece
    # - self._shared_settings: settings shared among all piecesd
    # - self._previous_exp: name of the experiments whose results are stored in self._result
    # - self._loaded: whether the load() method has been called

    # path to the R-language script that makes bar charts
    _R_bar_chart_path = u'scripts/R_bar_chart.r'

    def __init__(self, pathnames):
        # create the list of IndexedPiece objects
        self._data = []
        for each_val in pathnames:
            if isinstance(each_val, basestring):
                self._data.append(indexed_piece.IndexedPiece(each_val))
            elif isinstance(each_val, indexed_piece.IndexedPiece):
                self._data.append(each_val)
        # hold the result of the most recent call to run()
        self._result = None
        # hold the IndexedPiece-specific settings
        self._settings = [{} for _ in xrange(len(self._data))]
        for piece_sett in self._settings:
            for sett in [u'offset interval', u'voice combinations']:
                piece_sett[sett] = None
            for sett in [u'filter repeats']:
                piece_sett[sett] = False
        # hold settings common to all IndexedPieces
        self._shared_settings = {u'n': 2, u'continuer': u'_', u'mark singles': False,
                                 u'interval quality': False, u'simple intervals': False,
                                 u'include rests': False, u'count frequency': True}
        # which was the most recent experiment run? Either 'intervals' or 'n-grams'
        self._previous_exp = None
        # whether the load() method has been called
        self._loaded = False

    def __len__(self):
        """
        Return the number of pieces stored in this WorkflowManager.
        """
        return len(self._data)

    def __getitem__(self, index):
        """
        Return the IndexedPiece at a particular index.
        """
        return self._data[index]

    def load(self, instruction, pathname=None):
        """
        Import analysis data from long-term storage on a filesystem. This should primarily be \
        used for the ``u'pieces'`` instruction, to control when the initial music21 import \
        happens.

        Use :meth:`load` with an instruction other than ``u'pieces'`` to load results from a
        previous analysis run by :meth:`run`.

        .. note:: If one of the files imports as a :class:`music21.stream.Opus`, the number of
            pieces and their order *will* change.

        Parameters
        ==========
        :parameter instruction: The type of data to load.
        :type instruction: basestring
        :parameter pathname: The pathname of the data to import; not required for the \
            ``u'pieces'`` instruction.
        :type pathname: basestring

        :raises: :exc:`RuntimeError` if the ``instruction`` is not recognized.

        **Instructions**

        .. note:: only ``u'pieces'`` is implemented at this time.

        * ``u'pieces'``, to import all pieces, collect metadata, and run :class:`NoteRestIndexer`
        * ``u'hdf5'`` to load data from a previous :meth:`export`.
        * ``u'stata'`` to load data from a previous :meth:`export`.
        * ``u'pickle'`` to load data from a previous :meth:`export`.
        """
        # TODO: rewrite this with multiprocessing
        # NOTE: you may want to have the worker process create a new IndexedPiece object, import it
        #       and run the NoteRestIndexer, then pickle it and send that to a callback method
        #       that will somehow unpickle it and replace the *data in* the IndexedPieces here, but
        #       not actually replace the IndexedPieces, since that would inadvertently cancel the
        #       client's pointer to the IndexedPieces, if they have one
        if u'pieces' == instruction:
            for i, piece in enumerate(self._data):
                try:
                    piece.get_data([noterest.NoteRestIndexer])
                except indexed_piece.OpusWarning:
                    new_ips = piece.get_data([noterest.NoteRestIndexer], known_opus=True)
                    self._data = self._data[:i] + self._data[i + 1:] + new_ips
        elif u'hdf5' == instruction or u'stata' == instruction or u'pickle' == instruction:
            raise NotImplementedError(u'The ' + instruction + u' instruction does\'t work yet!')
        else:
            raise RuntimeError(u'Unrecognized load() instruction: "' + unicode(instruction) + '"')
        self._loaded = True

    def run(self, instruction):
        """
        Run an experiment's workflow. Remember to call :meth:`load` before this method.

        :parameter instruction: The experiment to run (refer to "List of Experiments" below).
        :type instruction: basestring

        :returns: The result of the experiment.
        :rtype: :class:`pandas.Series` or :class:`pandas.DataFrame`

        :raises: :exc:`RuntimeError` if the ``instruction`` is not valid for this
            :class:`WorkflowManager`.
        :raises: :exc:`RuntimeError` if you have not called :meth:`load`.
        :raises: :exc:`ValueError` if the voice-pair selection is invalid or unset.

        **List of Experiments**

        * ``u'intervals'``: find the frequency of vertical intervals in 2-part combinations. All \
            settings will affect analysis *except* ``'n'``. No settings are required; if you do \
            not set ``'voice combionations'``, all two-part combinations are included.
        * ``u'interval n-grams'``: find the frequency of n-grams of vertical intervals connected \
            by the horizontal interval of the lowest voice. All settings will affect analysis. \
            You must set the ``'voice combinations'`` setting. The default value for ``'n'`` is \
            ``2``.
        """
        if self._loaded is not True:
            raise RuntimeError(u'Please call load() before you call run()')
        # NOTE: do not re-order the instructions or this method will break
        possible_instructions = [u'intervals',
                                 u'interval n-grams']
        error_msg = u'WorkflowManager.run() could not parse the instruction'
        post = None
        # run the experiment
        if len(instruction) < min([len(x) for x in possible_instructions]):
            raise RuntimeError(error_msg)
        if instruction.startswith(possible_instructions[0]):
            self._previous_exp = u'intervals'
            post = self._intervs()
        elif instruction.startswith(possible_instructions[1]):
            self._previous_exp = u'n-grams'
            post = self._interval_ngrams()
        else:
            raise RuntimeError(error_msg)
        self._result = post
        return post

    def _interval_ngrams(self):
        """
        Prepare a list of frequencies of interval n-grams in all pieces.

        This method automatically uses :met:`_two_part_modules` and :meth:`_all_part_modules`
        when relevant.

        These indexers and experimenters will be run:

        * :class:`~vis.analyzers.indexers.interval.IntervalIndexer`
        * :class:`~vis.analyzers.indexers.interval.HorizontalIntervalIndexer`
        * :class:`~vis.analyzers.indexers.ngram.NGramIndexer`
        * :class:`~vis.analyzers.experimenters.frequency.FrequencyExperimenter`
        * :class:`~vis.analyzers.experimenters.aggregator.ColumnAggregator`

        Settings are parsed automatically by piece. If the ``offset interval`` setting has a value,
        :class:`~vis.analyzers.indexers.offset.FilterByOffsetIndexer` is run with that value. If
        the ``filter repeats`` setting is ``True``, the
        :class:`~vis.analyzers.repeat.FilterByRepeatIndexer` is run (after the offset indexer, if
        relevant).

        :returns: Result of the :class:`~vis.analyzers.experimenters.aggregator.ColumnAggregator`
            or a list of outputs from :class:`~vis.analyzers.indexers.ngram.NGramIndexer`,
            depending on the ``count frequency`` setting.

        .. note:: To compute more than one value of ``n``, call :meth:`_interval_ngrams` many times.
        """
        self._result = []
        # user helpers to fetch results for each piece
        for i in xrange(len(self._data)):
            # figure out which combinations we need... this might raise a ValueError, but there's
            # not much we can do to save the situation, so we might as well let it go up
            combos = unicode(self.settings(i, u'voice combinations'))
            if combos != u'all' and combos != u'all pairs':
                combos = ast.literal_eval(combos)

            if u'all' == self.settings(i, u'voice combinations'):
                self._result.append(self._all_part_modules(i))
            elif u'all pairs' == self.settings(i, u'voice combinations'):
                self._result.append(self._two_part_modules(i))
            else:
                self._result.append(self._variable_part_modules(i))
        # aggregate results across all pieces
        if self.settings(None, u'count frequency') is True:
            self._run_freq_agg()
        return self._result

    def _variable_part_modules(self, index):
        """
        Prepare a list of frequencies of variable-part interval n-grams in a piece. This method is
        called by :meth:`_interval_ngrams` when required (i.e., when we are not analyzing all parts
        at once or all two-part combinations).

        These indexers and experimenters will run:

        * :class:`~vis.analyzers.indexers.interval.IntervalIndexer`
        * :class:`~vis.analyzers.indexers.interval.HorizontalIntervalIndexer`
        * :class:`~vis.analyzers.indexers.ngram.NGramIndexer`

        :param index: The index of the IndexedPiece on which to the experiment, as stored in
            ``self._data``.
        :type index: int

        :returns: The result of :class:`NGramIndexer` for a single piece.
        :rtype: list of :class:`pandas.Series`

        .. note:: If the piece has an invalid part-combination list, the method returns ``None``.
        """
        piece = self._data[index]
        # make settings for interval indexers
        settings = {u'quality': self.settings(index, u'interval quality')}
        settings[u'simple or compound'] = u'simple' if self.settings(None, u'simple intervals') \
                                          is True else u'compound'
        vert_ints = piece.get_data([noterest.NoteRestIndexer, interval.IntervalIndexer], settings)
        horiz_ints = piece.get_data([noterest.NoteRestIndexer, interval.HorizontalIntervalIndexer],
                                    settings)
        # run the offset and repeat indexers, if required
        vert_ints = self._run_off_rep(index, vert_ints)
        horiz_ints = self._run_off_rep(index, horiz_ints)
        # figure out which combinations we need... this might raise a ValueError, but there's not
        # much we can do to save the situation, so we might as well let it go up
        needed_combos = ast.literal_eval(unicode(self.settings(index, u'voice combinations')))
        # each key in vert_ints corresponds to a two-voice combination we should use
        post = []
        for combo in needed_combos:
            # make the list of parts
            parts = [vert_ints[str(i) + u',' + str(combo[-1])] for i in combo[:-1]]
            parts.append(horiz_ints[combo[-1]])
            # assemble settings
            setts = {u'vertical': range(len(combo[:-1])), u'horizontal': [len(combo[:-1])]}
            setts[u'mark singles'] = self.settings(None, u'mark singles')
            setts[u'continuer'] = self.settings(None, u'continuer')
            setts[u'n'] = self.settings(None, u'n')
            if self.settings(None, u'include rests') is not True:
                setts[u'terminator'] = u'Rest'
            # run NGramIndexer, then append the result to the corresponding index of the dict
            post.append(piece.get_data([ngram.NGramIndexer], setts, parts)[0])
        return post

    def _two_part_modules(self, index):
        """
        Prepare a list of frequencies of two-part interval n-grams in a piece. This method is
        called by :meth:`_interval_ngrams` when required.

        These indexers and experimenters will run:

        * :class:`~vis.analyzers.indexers.interval.IntervalIndexer`
        * :class:`~vis.analyzers.indexers.interval.HorizontalIntervalIndexer`
        * :class:`~vis.analyzers.indexers.ngram.NGramIndexer`

        :param index: The index of the IndexedPiece on which to the experiment, as stored in
            ``self._data``.
        :type index: int

        :returns: The result of :class:`NGramIndexer` for a single piece.
        :rtype: list of :class:`pandas.Series`
        """
        piece = self._data[index]
        # make settings for interval indexers
        settings = {u'quality': self.settings(index, u'interval quality')}
        settings[u'simple or compound'] = u'simple' if self.settings(None, u'simple intervals') \
                                          is True else u'compound'
        vert_ints = piece.get_data([noterest.NoteRestIndexer, interval.IntervalIndexer], settings)
        horiz_ints = piece.get_data([noterest.NoteRestIndexer, interval.HorizontalIntervalIndexer],
                                    settings)
        # run the offset and repeat indexers, if required
        vert_ints = self._run_off_rep(index, vert_ints)
        horiz_ints = self._run_off_rep(index, horiz_ints)
        # each key in vert_ints corresponds to a two-voice combination we should use
        post = []
        for combo in vert_ints.iterkeys():
            # which "horiz" part to use?
            horiz_i = interval.key_to_tuple(combo)[1]
            # make the list of parts
            parts = [vert_ints[combo], horiz_ints[horiz_i]]
            # assemble settings
            setts = {u'vertical': [0], u'horizontal': [1]}
            setts[u'mark singles'] = self.settings(None, u'mark singles')
            setts[u'continuer'] = self.settings(None, u'continuer')
            setts[u'n'] = self.settings(None, u'n')
            if self.settings(None, u'include rests') is not True:
                setts[u'terminator'] = u'Rest'
            # run NGramIndexer, then append the result to the corresponding index of the dict
            post.append(piece.get_data([ngram.NGramIndexer], setts, parts)[0])
            #post.append(piece.get_data([ngram.NGramIndexer], setts, parts))  # DEBUG
        return post

    def _all_part_modules(self, index):
        """
        Prepare a list of frequencies of all-part interval n-grams in a piece. This method is
        called by :meth:`_interval_ngrams` when required.

        These indexers and experimenters will run:

        * :class:`~vis.analyzers.indexers.interval.IntervalIndexer`
        * :class:`~vis.analyzers.indexers.interval.HorizontalIntervalIndexer`
        * :class:`~vis.analyzers.indexers.ngram.NGramIndexer`

        :param index: The index of the IndexedPiece on which to the experiment, as stored in
            ``self._data``.
        :type index: int

        :returns: The result of :class:`NGramIndexer` for a single piece (for this method, always
            a single-element list).
        :rtype: list of :class:`pandas.Series`
        """
        piece = self._data[index]
        # make settings for interval indexers
        settings = {u'quality': self.settings(index, u'interval quality')}
        settings[u'simple or compound'] = u'simple' if self.settings(None, u'simple intervals') \
                                          is True else u'compound'
        vert_ints = piece.get_data([noterest.NoteRestIndexer, interval.IntervalIndexer],
                                   settings)
        horiz_ints = piece.get_data([noterest.NoteRestIndexer,
                                     interval.HorizontalIntervalIndexer],
                                    settings)
        # run the offset and repeat indexers, if required
        vert_ints = self._run_off_rep(index, vert_ints)
        horiz_ints = self._run_off_rep(index, horiz_ints)
        # figure out the weird string-index things for the vertical part combos
        lowest_part = len(piece.metadata(u'parts')) - 1
        vert_combos = [str(x) + u',' + str(lowest_part) for x in xrange(lowest_part)]
        # make the list of parts
        parts = [vert_ints[x] for x in vert_combos]
        parts.append(horiz_ints[-1])  # always the lowest voice
        # assemble settings
        setts = {u'vertical': range(len(parts) - 1), u'horizontal': [len(parts) - 1]}
        setts[u'mark singles'] = self.settings(None, u'mark singles')
        setts[u'continuer'] = self.settings(None, u'continuer')
        setts[u'n'] = self.settings(None, u'n')
        if self.settings(None, u'include rests') is not True:
            setts[u'terminator'] = u'Rest'
        # run NGramIndexer, then append the result to the corresponding index of the dict
        result = [piece.get_data([ngram.NGramIndexer], setts, parts)[0]]
        return result

    def _intervs(self):
        """
        Prepare a list of the intervals found between two parts in all pieces. If particular voice
        pairs are specified for a piece, only those pairs are included. These  analyzers will run:

        * :class:`~vis.analyzers.indexers.interval.IntervalIndexer`

        :returns: the result of :class:`~vis.analyzers.indexers.interval.IntervalIndexer`
        :rtype: dict of :class:`pandas.Series`

        .. note:: The return value is automatically stored in ``self._result``.

        Settings are parsed automatically by piece. For part combinations, ``[all]``,
        ``[all pairs]``, and ``None`` are treated as equivalent. If the ``offset interval`` setting
        has a value, :class:`~vis.analyzers.indexers.offset.FilterByOffsetIndexer` is run with that
        value. If the ``filter repeats`` setting is ``True``, the
        :class:`~vis.analyzers.repeat.FilterByRepeatIndexer` is run (after the offset indexer, if
        relevant).

        .. note:: The voice combinations must be pairs. Voice combinations with fewer or greater
        than two parts are ignored, which may result in one or more pieces being omitted from the
        results if you aren't careful with settings.
        """
        self._result = []
        # shared settings for the IntervalIndexer
        setts = {u'quality': self.settings(None, u'interval quality')}
        setts[u'simple or compound'] = u'simple' if self.settings(None, u'simple intervals') \
                                       is True else u'compound'
        for i, piece in enumerate(self._data):
            vert_ints = piece.get_data([noterest.NoteRestIndexer, interval.IntervalIndexer], setts)
            # figure out which combinations we need... this might raise a ValueError, but there's
            # not much we can do to save the situation, so we might as well let it go up
            combos = unicode(self.settings(i, u'voice combinations'))
            if combos != u'all' and combos != u'all pairs' and combos != u'None':
                combos = ast.literal_eval(combos)
                vert_ints = WorkflowManager._remove_extra_pairs(vert_ints, combos)
            # we no longer need to know the combinations' names, so we can make a list
            vert_ints = list(vert_ints.itervalues())
            # run the offset and repeat indexers, if required
            post = self._run_off_rep(i, vert_ints)
            # remove the "Rest" entries, if required
            if self.settings(None, u'include rests') is not True:
                # we'll just get a view that omits the "Rest" entries in the Series
                for i, pair in enumerate(post):
                    post[i] = pair[pair != u'Rest']
            self._result.append(post)
        if self.settings(None, 'count frequency') is True:
            self._run_freq_agg()
        return self._result

    def _run_off_rep(self, index, so_far):
        """
        Run the filter-by-offset and filter-by-repeat indexers, as required by the piece's settings:

        * :class:`~vis.analyzers.indexers.offset.FilterByOffsetIndexer`
        * :class:`~vis.analyzers.indexers.repeat.FilterByRepeatIndexer`

        Use this method from other :class:`WorkflowManager` methods for filtering by note-start
        offset and repetition.

        .. note:: If the relevant settings (``'offset interval'`` and ``'filter repeats'``) do not
            require running either indexer, ``so_far`` will be returned unchanged.

        :param index: Index of the piece to run.
        :type index: :``int``
        :param so_far: Return value of :meth:`get_data` that we should run through the offset and
            repeat indexers.
        :type so_far: As specified in :class:`~vis.analyzers.indexers.offset.FilterByOffsetIndexer`
            or :class:`~vis.analyzers.indexers.repeat.FilterByRepeatIndexer`.

        :returns: The filtered results.
        :rtype: As specified in :class:`~vis.analyzers.indexers.offset.FilterByOffsetIndexer` or
            :class:`~vis.analyzers.indexers.repeat.FilterByRepeatIndexer`.
        """
        # If we're given a dictionary (the output from IntervalIndexer), we must return one, and
        # we have to preserve the indexing. Thankfully, indexers preserve sequential ordering, so
        # all we need is to remember the dict keys in the same order.
        dict_keys = so_far.keys() if isinstance(so_far, dict) else None
        if dict_keys is not None:  # dict-to-list in a known order
            so_far = [so_far[key] for key in dict_keys]
        if self.settings(index, u'offset interval') is not None:
            off_sets = {u'quarterLength': self.settings(index, u'offset interval')}
            so_far = self._data[index].get_data([offset.FilterByOffsetIndexer], off_sets, so_far)
        if self.settings(index, u'filter repeats') is True:
            so_far = self._data[index].get_data([repeat.FilterByRepeatIndexer], {}, so_far)
        if dict_keys is not None:  # known-order-list-to-dict
            so_far = {dict_keys[i]: so_far[i] for i in xrange(len(dict_keys))}
        return so_far

    def _run_freq_agg(self):
        """
        Run the frequency and aggregation experimenters:

        * :class:`~vis.analyzers.experimenters.frequencyFrequencyExperimenter`
        * :class:`~vis.analyzers.experimenters.aggregator.ColumnAggregator`

        Use this method from other :class:`WorkflowManager` methods for counting frequency.

        .. note:: This method runs on, then overwrites, values stored in :attr:`self._result`.

        :returns: Aggregated frequency counts for everything stored in :attr:`self._result`.
        :rtype: :class:`pandas.Series`
        """
        # NB: there's no "logic" here, so I didn't bother testing the method
        agg_p = AggregatedPieces(self._data)
        self._result = agg_p.get_data([aggregator.ColumnAggregator],
                                      [frequency.FrequencyExperimenter],
                                      {},
                                      self._result)
        self._result.sort(ascending=False)
        return self._result

    @staticmethod
    def _remove_extra_pairs(vert_ints, combos):
        """
        From the result of IntervalIndexer, remove those voice pairs that aren't required. This is
        a separate function to improve test-ability.

        **Parameters:**
        :param vert_ints: The results of IntervalIndexer.
        :type vert_ints: dict of any
        :param combos: The voice pairs to keep. Note that any element in this list longer than 2
            will be silently ignored.
        :type combos: list of list of int

        **Returns:**
        :returns: Only the voice pairs you want.
        :rtype: dict of any
        """
        these_pairs = []
        for pair in combos:
            if 2 == len(pair):
                these_pairs.append(unicode(pair[0]) + u',' + unicode(pair[1]))
        if 0 == len(these_pairs):
            return {}
        else:
            delete_these = []
            for key in vert_ints.iterkeys():
                if key not in these_pairs:
                    delete_these.append(key)
            for key in delete_these:
                del vert_ints[key]
            return vert_ints

    def _get_dataframe(self, name=u'data', top_x=None, threshold=None):
        """
        "Convert" ``self._result`` into a :class:`DataFrame`, including only the top ``X`` results
        that are greater than ``threshold``. Note that the threshold filter is applied first.

        :param name: String to use for the column name of the Series currently held in self._result.
            The default is u'data'.
        :type name: ``basestring``
        :param top_x: This is the "X" in "only show the top X results." The default is ``None``.
        :type top_x: ``int``
        :param threshold: If a result is strictly less than this number, it won't be included. The
            default is ``None``.
        :type threshold: number

        :returns: A DataFrame with self._result as the only column.
        :rtype: :class:`DataFrame`
        """
        post = None
        if threshold is not None:
            post = self._result[self._result > threshold]
        else:
            post = self._result
        if top_x is not None:
            post = post[:top_x]
        return pandas.DataFrame({name: post})

    def output(self, instruction, pathname=None, top_x=None, threshold=None):
        """
        Create a visualization from the most recent result of :meth:`run` and save it to a file.

        :parameter instruction: The type of visualization to output.
        :type instruction: basestring
        :parameter pathname: The pathname for the output. The default is
            ``'test_output/output_result``. A file extension is applied automatically.
        :type pathname: basestring
        :param top_x: This is the "X" in "only show the top X results." The default is ``None``.
        :type top_x: int
        :param threshold: If a result is strictly less than this number, it will be left out. The
            default is ``None``.
        :type threshold: number

        :returns: The pathname of the outputted visualization.
        :rtype: unicode

        :raises: :exc:`NotImplementedError` if you use the ``u'LilyPond'`` instruction.
        :raises: :exc:`RuntimeError` for unrecognized instructions.
        :raises: :exc:`RuntimeError` if :meth:`run` has never been called.
        :raises: :exc:`RuntiemError` if a call to R encounters a problem.

        **Instructions:**

        * ``u'R histogram'``: a histogram with ggplot2 in R.
        """
        if instruction == u'LilyPond':
            raise NotImplementedError(u'I didn\'t write that part yet!')
        elif instruction == u'R histogram':
            # ensure we have some results
            if self._result is None:
                raise RuntimeError(u'Call run() before calling export()')
            else:
                # properly set output paths
                pathname = u'test_output/output_result' if pathname is None else unicode(pathname)
                stata_path = pathname + u'.dta'
                png_path = pathname + u'.png'
                # ensure we have a DataFrame
                if not isinstance(self._result, pandas.DataFrame):
                    out_me = self._get_dataframe(u'freq', top_x, threshold)
                else:
                    out_me = self._result
                out_me.to_stata(stata_path)
                token = None
                if u'intervals' == self._previous_exp:
                    token = u'int'
                elif u'n-grams' == self._previous_exp:
                    token = unicode(self.settings(None, u'n'))
                else:
                    token = u'things'
                call_to_r = [u'Rscript', u'--vanilla', WorkflowManager._R_bar_chart_path,
                             stata_path, png_path, token, str(len(self._data))]
                try:
                    subprocess.check_output(call_to_r)
                except subprocess.CalledProcessError as cpe:
                    raise RuntimeError(u'Error during call to R: ' + unicode(cpe.output) + \
                                       u' (return code: ' + unicode(cpe.returncode) + u')')
                return png_path
        else:
            raise RuntimeError(u'Unrecognized instruction: ' + unicode(instruction))

    def export(self, form, pathname=None, top_x=None, threshold=None):
        """
        Save data from the most recent result of :meth:`run` to a file.

        Parameters
        ==========
        :parameter form: The output format you want.
        :type form: :obj:`basestring`
        :parameter pathname: The pathname for the output. The default is
            ``test_output/output_result``. File extensions are applied automatically.
        :type pathname: :obj:`basestring`
        :param top_x: This is the "X" in "only show the top X results." The default is ``None``.
        :type top_x: :obj:`int`
        :param threshold: If a result is strictly less than this number, it won't be included. The
            default is :obj:`None`.
        :type threshold: :obj:`int` or :obj:`float`

        Returns
        =======
        :returns: The pathname of the outputted file.
        :rtype: :obj:`unicode`

        Raises
        ======
        :raises: :exc:`RuntimeError` for unrecognized instructions.
        :raises: :exc:`RuntimeError` if :meth:`run` has never been called.

        Formats:

        * ``u'CSV'``: output a Series or DataFrame to a CSV file.
        * ``u'Stata'``: output a Stata file for importing to R.
        * ``u'Excel'``: output an Excel file for Peter Schubert.
        * ``u'HTML'``: output an HTML table, as used by the vis PyQt4 GUI.
        """
        # ensure we have some results
        if self._result is None:
            raise RuntimeError(u'Call run() before calling export()')
        # ensure we have a DataFrame
        if not isinstance(self._result, pandas.DataFrame):
            export_me = self._get_dataframe(u'data', top_x, threshold)
        else:
            export_me = self._result
        # key is the instruction; value is (extension, export_method)
        directory = {u'CSV': (u'.csv', export_me.to_csv),
                     u'Stata': (u'.dta', export_me.to_stata),
                     u'Excel': (u'.xlsx', export_me.to_excel),
                     u'HTML': (u'.html', export_me.to_html)}
        # ensure we have a valid output format
        if form not in directory:
            raise RuntimeError(u'Unrecognized output format: ' + unicode(form))
        # ensure we have an output path
        pathname = u'test_output/no_path' if pathname is None else unicode(pathname)
        # ensure there's a file extension
        if directory[form][0] != pathname[-1 * len(directory[form][0]):]:
            pathname += directory[form][0]
        # call the to_whatever() method
        directory[form][1](pathname)
        return pathname

    def metadata(self, index, field, value=None):
        """
        Get or set a metadata field. The valid field names are determined by :class:`IndexedPiece`
        (refer to the documentation for :meth:`~vis.models.indexed_piece.IndexedPiece.metadata`).

        A metadatum is a salient musical characteristic of a particular piece, and does not change
        across analyses.

        :param index: The index of the piece to access. The range of valid indices is ``0`` through
            one fewer than the return value of calling :func:`len` on this :class:`WorkflowManager`.
        :type index: :obj:`int`
        :param field: The name of the field to be accessed or modified.
        :type field: :obj:`basestring`
        :param value: If not ``None``, the new value to be assigned to ``field``.
        :type value: :obj:`object` or :obj:`None`

        :returns: The value of the requested field or ``None``, if assigning, or if accessing a
            non-existant field or a field that has not yet been initialized.
        :rtype: :obj:`object` or :obj:`None`

        :raises: :exc:`TypeError` if ``field`` is not a ``basestring``.
        :raises: :exc:`AttributeError` if accessing an invalid ``field``.
        :raises: :exc:`IndexError` if ``index`` is invalid for this ``WorkflowManager``.
        """
        return self._data[index].metadata(field, value)

    def settings(self, index, field, value=None):
        """
        Get or set a value related to analysis. The valid values are listed below.

        A setting is related to this particular analysis, and is not a salient musical feature of
        the work itself.

        Refer to :meth:`run` for a list of settings required or used by each experiment.

        :param index: The index of the piece to access. The range of valid indices is ``0`` through
            one fewer than the return value of calling :func:`len` on this WorkflowManager. If
            ``value`` is not ``None`` and ``index`` is ``None``, you can set a field for all pieces.
        :type index: int or ``None``
        :param field: The name of the field to be accessed or modified.
        :type field: basestring
        :param value: If not ``None``, the new value to be assigned to ``field``.
        :type value: object or ``None``

        :returns: The value of the requested field or ``None``, if assigning, or if accessing a
            non-existant field or a field that has not yet been initialized.
        :rtype: object or ``None``

        :raises: :exc:`AttributeError` if accessing an invalid ``field`` (see valid fields below).
        :raises: :exc:`IndexError` if ``index`` is invalid for this ``WorkflowManager``.
        :raises: :exc:`ValueError` if ``index`` and ``value`` are both ``None``.

        **Piece-Specific Settings**

        Pieces do not share these settings.

        * ``offset interval``: If you want to run the \
            :class:`~vis.analyzers.indexers.offset.FilterByOffsetIndexer`, specify a value for this
            setting. To avoid running the :class:`FilterByOffsetIndexer`, set this to ``0``.
            setting that will become the ``quarterLength`` duration between observed offsets.
        * ``filter repeats``: If you want to run the \
            :class:`~vis.analyzers.indexers.repeat.FilterByRepeatIndexer`, set this setting to \
            ``True``.
        * ``voice combinations``: If you want to consider certain specific voice combinations, \
            set this setting to a list of a list of iterables. The following value would analyze \
            the highest three voices with each other: ``'[[0,1,2]]'`` while this would analyze the \
            every part with the lowest for a four-part piece: ``'[[0, 3], [1, 3], [2, 3]]'``. This \
            should always be a ``basestring`` that nominally represents a list (except the special \
            values for ``'all'`` parts at once or ``'all pairs'``).

        **Shared Settings**

        All pieces share these settings. The value of ``index`` is ignored for shared settings, so
        it can be anything.

        * ``n``: As specified in :attr:`vis.analyzers.indexers.ngram.NGramIndexer.possible_settings`
        * ``continuer``: As specified in \
            :attr:`vis.analyzers.indexers.ngram.NGramIndexer.possible_settings`
        * ``interval quality``: If you want to display interval quality, set this setting to \
            ``True``.
        * ``simple intervals``: If you want to display all intervals as their single-octave \
            equivalents, set this setting to ``True``.
        * ``include rests``: If you want to include ``u'Rest'`` tokens as vertical intervals, \
            change this setting to ``True``. The default is ``False``.
        * ``count frequency``: When set to ``True`` (the default), experiments will return the \
            number of occurrences of each token (i.e., "each interval" or "each interval n-gram").\
            When set to ``False``, the moment-by-moment analysis of each piece is retained. We \
            recommend you only request spreadsheet-formatted output when ``count frequency`` is \
            ``False``.
        """
        if field in self._shared_settings:
            if value is None:
                return self._shared_settings[field]
            else:
                self._shared_settings[field] = value
        elif index is None:
            if value is None:
                raise ValueError(u'If "index" is None, "value" must not be None.')
            else:
                for i in xrange(len(self._settings)):
                    self.settings(i, field, value)
        elif not 0 <= index < len(self._settings):
            raise IndexError(u'Invalid piece index :' + unicode(index))
        elif field not in self._settings[index]:
            raise AttributeError(u'Invalid setting: ' + unicode(field))
        elif value is None:
            return self._settings[index][field]
        elif field == u'offset interval' and value == 0:  # can't set directly to None :(
            self._settings[index][field] = None
        else:
            self._settings[index][field] = value
