#! /usr/bin/python
# -*- coding: utf-8 -*-

#--------------------------------------------------------------------------------------------------
# Program Name:           vis
# Program Description:    Helps analyze music with computers.
#
# Filename:               models/indexed_piece.py
# Purpose:                Hold the model representing an indexed and analyzed piece of music.
#
# Copyright (C) 2013 Christopher Antila
#
# This program is free software: you can redistribute it and/or modify it under the terms of the
# GNU General Public License as published by the Free Software Foundation, either version 3 of
# the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
# even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with this program.
# If not, see <http://www.gnu.org/licenses/>.
#--------------------------------------------------------------------------------------------------
"""
The model representing an indexed and analyzed piece of music.
"""

# Imports
from music21 import converter


class IndexedPiece(object):
    """
    Holds the indexed data from a musical score.

    Here is a list of all the metadata we'll have about a piece:
    From vis:
    - pathname
    - parts (an ordered list of part names)
    - quarterLength duration of anacrusis, if applicable
    From music21.metadata.Metadata:
    - alternativeTitle
    - composer
    - composers
    - date
    - localeOfComposition
    - movementName
    - movementNumber
    - number
    - opusNumber
    - title (only required field; at worst, it's the filename without extension)
    """

    # About the Data Model (for self._data)
    # =====================================
    # - All the indices are stored in a dict.
    # - Indices of the dict will be unicode()-format class names of the Indexer, as returned by
    #   each Indexer subclass's "name()" function.
    # - how can we store multiple results from the same Indexer, generated with different settings?

    # - For an Indexer, the stored item will be a dict of pandas.Series objects.
    #    - Access a particular index by specifying the Indexer name, the settings, and either the
    #      index of the part in the Score object or a list of parts in a part combination.
    #      Examples:
    #      - self._data[u'NoteRestIndexer'][u'{}'][0]
    #         Notes-and-rests index of the highest part; Indexer has no settings.
    #         NB: since this is a single-part reference, it is a list. Indices are integers.
    #      - self._data[u'IntervalIndexer'][u'{u'quality': False, u'simple or compound': u'simple'}'][u'[0, 1]']
    #         Intervals index of the two highest parts.
    #         NB: since this lists part combinations, it is a dict. Indices are list-like strings.
    #    - Be aware that settings can be tricky to deal with, since a dict object does not always
    #      present its keys to str() in the same order. The only way to know whether specific
    #      settings are present in an IndexedPiece is to eval() the settings strings and compare
    #      them to another settings dict.
    #    - Each of the objects you get is a pandas.Series, where:
    #      - each element is an instance music21.base.ElementWrapper
    #      - each element has an "offset" corresponding to its place in the score
    #      - each element has its proper "duration" attribute

    # - For an Experimenter, results are stored in the same way as for an Indexer.
    #   There are two differences:
    #   - There is an additional part specification: u'all'. This may appear alongside or instead
    #     of other parts or part combinations.
    #   - The Experimenter's output may be either a pandas.Series or pandas.DataFrame.

    def __init__(self, pathname):
        super(IndexedPiece, self).__init__()
        self._metadata = {'pathname': pathname}
        self._data = {}

    def __repr__(self):
        pass

    def __str__(self):
        pass

    def __unicode__(self):
        pass

    def _import_score(self):
        """
        Import the score to music21 format. Uses multiprocessin, but blocks until the import is
        complete.

        Returns
        =======
        music21.stream.Score or Opus
            The score.
        """
        # TODO: actually write this method
        return converter.parse(self._metadata['pathname'])

    def metadata(self, field, value=None):
        """
        Get or set metadata about the piece, like filename, title, and composer.

        It'll be like this:
        >>> piece = IndexedPiece('a_sibelius_symphony.mei')
        >>> piece.metadata('composer')
        u'Jean Sibelius'
        >>> piece.metadata('year', 1919)
        >>> piece.metadata('year')
        1919
        >>> piece.metadata('parts')
        [u'Flute 1', u'Flute 2', u'Oboe 1', u'Oboe 2', u'Clarinet 1', u'Clarinet 2', ... ]

        If the piece hasn't yet been imported, and none of the file-derived metadata are available
        yet, an exception will be raised (KeyError) *unless* the field has been set manually, in
        which case its value is returned. If the piece *has* been imported, and you try to get a
        metadatum that isn't available, we'll just return None.
        """
        pass

    def indexers_used(self):
        """
        Return a list of the names of the indexers used so far in this IndexedPiece.
        """
        pass

    def add_index(self, which_indexers, which_settings=None):
        """
        Run an indexer (or some indexers) on the score and save the results. If the indexer has
        already been run with the same settings, it will not be run again.

        During the initial import/indexation stage, you'll just call this method with a list of
        indices to add, in which case we'll run the indexation processes in parallel. If only one
        indexer is given, we'll not use multiprocessing. Not sure this is possible quite like
        this, but I guess we'll figure it out.

        This method checks whether the piece has ever been imported yet. If not, it'll be done now,
        and the offsets will be indexed first, since it's needed for everything else, and the
        metadata will also be collected from the file.

        Also, since the Score object is never actually retained after the add_indexation() method
        finishes, it makes sense to supply a list of all the indices you'll want, all at the same
        time, so that the import need only happen once.

        Access the result with "get_parts()".

        Parameters
        ==========
        which_indexers : [string]
            A list of the vis.controllers.indexer.Indexer subclasses to run on the IndexedPiece. If
            you are using a built-in Indexer (the code for which is stored in
            "analyzers/indexer.py"), the string should look like this:
                u'IntervalIndexer'
            If you are using an Indexer not stored there, you should add the name of the
            subdirectory, so the string should look like this:
                u'my_indexers.MyIndexer'

        which_settings : dict
            A dict of the settings to provide the Indexers. Default is {}. This is the same for all
            Indexers in "which_indexers", so you may specify settings that apply only to one or some
            of the Indexers, but you may not specify different settings of the same name for
            different Indexers.

        Raises
        ======
        RuntimeException :
            - If one of the "which_indexers" refers to an unknown Indexer subclass. All the other
              Indexers will still be run.
            - If a required setting for an Indexer is absent. All the other Indexers will still run.

        Side Effects
        ============
        Results from the Indexer, and any additional Indexer subclasses required for the
        "which_index" Indexer subclass, are saved in the IndexedPiece.
        """
        if not which_settings: which_settings = {}
        # TODO: for testing...
        # - the "missing_indexers" handling
        # - built-in Indexers
        # - add-on Indexers
        # - required indexer already there
        # - required indexer not already there

        # Just in case
        if isinstance(which_indexers, basestring):
            which_indexers = [which_indexers]

        # If one of the indexers doesn't exist, add its name to this list.
        missing_indexers = []
        missing_settings = []

        # Hold the music21 Score object, if we use it
        the_score = None

        # If one of the indexers requires another indexer, we'll run it automatically. If the user
        # specifies pre-requisite indexers out of order (i.e., which_indexers is
        # [u'InertvalIndexer', u'NoteRestIndexer']), then we'll find the NoteRestIndexer is already
        # calculated, and skip it.
        for this_indexer in which_indexers:
            # Does this Indexer exist?
            # TODO: handle add-on Indexers
            try:
                i_module = __import__(u'analyzers.indexer',
                                      globals(),
                                      locals(),
                                      this_indexer,
                                      -1)
            except ImportError:
                missing_indexers.append(this_indexer)
                continue

            # Make a dict of the settings relevant for this Indexer
            # We'll check all the possible settings for this Indexer. If the setting isn't given by
            # the user, we'll use the default; if there is no default, we can't use the Indexer.
            poss_sett = eval(u'i_module.' + this_indexer + u'.possible_settings')
            def_sett = eval(u'i_module.' + this_indexer + u'.default_settings')
            this_settings = {}
            for sett in poss_sett:
                if sett in which_settings:
                    this_settings[sett] = which_settings[sett]
                elif sett in def_sett:
                    this_settings[sett] = def_sett[sett]
                else:
                    this_settings = u'spoiled'
                    break
            if u'spoiled' == this_settings:
                missing_settings.append(this_indexer)
                continue

            # Do we already have this index with the same settings?
            if this_indexer in self._data:
                # Is there an index with the same settings?
                for each_setts in self._data[this_indexer].iterkeys():
                    if eval(each_setts) == this_settings:
                        this_settings = u'found'
                        break
            if u'found' == this_settings:
                continue

            # Does the Indexer require the Score?
            required_score = None
            if eval(u'i_module.' + this_indexer + u'.requires_score'):
                if the_score is None:
                    the_score = self._import_score()
                required_score = [the_score.parts[i] for i in xrange(len(the_score.parts))]
                # TODO: what about imports to Opus objects?
                # TODO: find and store metadata
            else:
                req_ind = eval(u'i_module.' + this_indexer + u'.required_indices')
                for ind in req_ind:
                    if ind not in self._data:
                        self.add_index(ind, which_settings)

            # Run the Indexer and store the results
            indexer_instance = eval(u'i_module.' +
                                    this_indexer +
                                    u'(required_score, this_settings)')
            if this_indexer not in self._data:
                self._data[this_indexer] = {}
            self._data[this_indexer][unicode(this_settings)] = indexer_instance.run()

            # Be explicit about memory
            del indexer_instance
            del this_settings

        # If one of the Indexers doesn't exist
        if missing_indexers:
            msg = u'Unable to import requested Indexers: ' + unicode(missing_indexers)
            raise RuntimeError(msg)
        # If one of the Indexers is missing a required setting
        elif missing_settings:
            msg = u'Indexers missing required settings: ' + unicode(missing_indexers)
            raise RuntimeError(msg)

    def remove_index(self, **args):
        """
        To save on memory, or for some other reason like it's suddenly invalied, remove certain
        information from this IndexedPiece.

        You might want to do this, for example, after parsing chords from a piano texture.
        """
        pass

    def experimenters_used(self):
        """
        Return a list of the names of the experimenters used so far in this IndexedPiece.
        """
        pass

    def add_experiment(self, which_experimenters, which_settings=None):
        """
        Run an experimenter (or some experimenters) on the score and save the results. If the
        experimenter has already been run with the same settings, the previously-calculated
        results are returned.

        This method checks whether the required indexers have been run. If not, they will be run
        now, and the indices saved in this object, but not returned.

        Parameters
        ==========
        which_experimenters : list
            A list of the vis.controllers.experimenter.Experimenter subclasses to run.

        which_settings : dict
            A dict of the settings to provide the Experimenter. Default is {}.

        Returns
        =======
        pandas.Series or pandas.DataFrame :
            The result produced by the Experimenter subclass.

        Raises
        ======
        RuntimeException :
            If "which_experimenters" refers to an unknown Experimenter subclass, or the Experimenter
            subclass raises an exception.

        Side Effects
        ============
        Results from the Indexer, and any additional Indexer subclasses required for the
        "which_index" Indexer subclass, are saved in the IndexedPiece.
        """
        if not which_settings: which_settings = {}
        pass

    def remove_experiment(self, **args):
        """
        To save on memory, or for some other reason like it's suddenly invalied, remove certain
        information from this IndexedPiece.

        You might want to do this, for example, after re-calculating an index on which an
        Experimenter depends, but which you do not wish to recalculate.
        """
        pass

    def iter(self, index, parts, offset=None, repeated=False):
        """
        Get an iterable for events from the beginning to the end of the piece.

        Parameters
        ==========
        index : subclass of vis.controllers.indexers.Indexer
            The indexer whose output you wish to access.

        parts : list or integer
            Either an integer, corresponding to the part whose index you want, or a list of the
            integers corresponding to the parts whose indices you want.

        offset : float or None
            Either the quarterLength offset between events you wish to consider, or "None," which
            is the default, which returns every recorded event.

        repeated : boolean
            Whether to return events that are identical to the previously-returned event. Default
            is False.

        Returns
        =======
        Either a music21.base.ElementWrapper (if "parts" was an integer) or else a list of
        ElementWrapper objects. The "obj" attribute of an ElementWrapper instance holds the
        indexed data.

        Raises
        ======
        RuntimeError :
            - If the "index" class has not been used in this IndexedPiece.
        """
        pass

    def get_parts(self, parts, index):
        """
        Get a list of an index of specific parts.

        Parameters
        ==========
        parts : [int] or [[int]]
            A list of the integers or a list of integer lists corresponding to the parts or part
            combinations you want. The indices are the same as the result of "metadata('parts')".

        index : string
            The name of the index you want, as provided to "add_index()". This is the string-wise
            representation of the Indexer class's name.

        Returns
        =======
        [pandas.Series]
            A list of the specified index for each requested part.

        Raises
        ======
        RuntimeError :
            - If the index has not yet been calculated.
            - If the parts or part combinations are invalid (i.e., the part index does not exist in
              the IndexedPiece or the part combination has not been calculated for this index).

        Examples
        ========
        >>> piece = IndexedPiece('test_corpus/bwv77.mxl')
        >>> piece.metadata('parts')
        [u'Soprano', u'Alto', u'Tenor', u'Bass']
        >>> piece.add_index(u'NoteRestIndexer')
        >>> piece.get_parts([0, 3], u'NoteRestIndexer')
        [<Series with Soprano NoteRestIndexer>, <Series with Bass NoteRestIndexer>]
        >>> piece.add_index(u'IntervalIndexer')
        >>> piece.get_parts([[0, 3]], u'IntervalIndexer')
        [[<Series with Soprano-and-Bass interval index>]]
        """
        pass

    @staticmethod
    def _find_part_names(the_score):
        """
        Copy this from importer.py
        """
        pass

    @staticmethod
    def _find_piece_title(the_score):
        """
        Copy this from importer.py
        """
        pass
