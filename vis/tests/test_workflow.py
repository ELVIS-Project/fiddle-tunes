#!/usr/bin/env python
# -*- coding: utf-8 -*-
#--------------------------------------------------------------------------------------------------
# Program Name:           vis
# Program Description:    Helps analyze music with computers.
#
# Filename:               controllers_tests/test_workflow.py
# Purpose:                Tests for the WorkflowManager
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
Tests for the WorkflowManager
"""

from subprocess import CalledProcessError
from unittest import TestCase, TestLoader
import mock
from mock import MagicMock
import pandas
from music21.humdrum.spineParser import GlobalReference
from vis.workflow import WorkflowManager
from vis.models.indexed_piece import IndexedPiece
from vis.analyzers.indexers import noterest


# pylint: disable=R0904
# pylint: disable=C0111
class WorkflowTests(TestCase):
    # NB: this class is just for __init__(), load(), and run() (without the run() helper methods)
    def test_init_1(self):
        # with a list of basestrings
        with mock.patch(u'vis.models.indexed_piece.IndexedPiece') as mock_ip:
            in_val = [u'help.txt', 'path.xml', u'why_you_do_this.rtf']
            test_wc = WorkflowManager(in_val)
            self.assertEqual(3, mock_ip.call_count)
            for val in in_val:
                mock_ip.assert_any_call(val)
            self.assertEqual(3, len(test_wc._data))
            for each in test_wc._data:
                self.assertTrue(isinstance(each, mock.MagicMock))
            self.assertEqual(3, len(test_wc._settings))
            for piece_sett in test_wc._settings:
                self.assertEqual(3, len(piece_sett))
                for sett in [u'offset interval', u'voice combinations']:
                    self.assertEqual(None, piece_sett[sett])
                for sett in [u'filter repeats']:
                    self.assertEqual(False, piece_sett[sett])
            exp_sh_setts = {u'n': 2, u'continuer': u'_', u'mark singles': False,
                            u'interval quality': False, u'simple intervals': False,
                            u'include rests': False, u'count frequency': True}
            self.assertEqual(exp_sh_setts, test_wc._shared_settings)

    def test_init_2(self):
        # with a list of IndexedPieces
        in_val = [IndexedPiece(u'help.txt'), IndexedPiece('path.xml'),
                  IndexedPiece(u'why_you_do_this.rtf')]
        test_wc = WorkflowManager(in_val)
        self.assertEqual(3, len(test_wc._data))
        for each in test_wc._data:
            self.assertTrue(each in in_val)
        for piece_sett in test_wc._settings:
            self.assertEqual(3, len(piece_sett))
            for sett in [u'offset interval', u'voice combinations']:
                self.assertEqual(None, piece_sett[sett])
            for sett in [u'filter repeats']:
                self.assertEqual(False, piece_sett[sett])
        exp_sh_setts = {u'n': 2, u'continuer': u'_', u'mark singles': False,
                        u'interval quality': False, u'simple intervals': False,
                        u'include rests': False, u'count frequency': True}
        self.assertEqual(exp_sh_setts, test_wc._shared_settings)

    def test_init_3(self):
        # with a mixed list of valid things
        in_val = [IndexedPiece(u'help.txt'), 'path.xml', u'why_you_do_this.rtf']
        test_wc = WorkflowManager(in_val)
        self.assertEqual(3, len(test_wc._data))
        self.assertEqual(in_val[0], test_wc._data[0])
        for each in test_wc._data[1:]:
            self.assertTrue(isinstance(each, IndexedPiece))
        for piece_sett in test_wc._settings:
            self.assertEqual(3, len(piece_sett))
            for sett in [u'offset interval', u'voice combinations']:
                self.assertEqual(None, piece_sett[sett])
            for sett in [u'filter repeats']:
                self.assertEqual(False, piece_sett[sett])
        exp_sh_setts = {u'n': 2, u'continuer': u'_', u'mark singles': False,
                        u'interval quality': False, u'simple intervals': False,
                        u'include rests': False, u'count frequency': True}
        self.assertEqual(exp_sh_setts, test_wc._shared_settings)

    def test_init_4(self):
        # with mostly basestrings but a few ints
        in_val = [u'help.txt', 'path.xml', 4, u'why_you_do_this.rtf']
        test_wc = WorkflowManager(in_val)
        self.assertEqual(3, len(test_wc._data))
        for each in test_wc._data:
            self.assertTrue(isinstance(each, IndexedPiece))
        for piece_sett in test_wc._settings:
            self.assertEqual(3, len(piece_sett))
            for sett in [u'offset interval', u'voice combinations']:
                self.assertEqual(None, piece_sett[sett])
            for sett in [u'filter repeats']:
                self.assertEqual(False, piece_sett[sett])
        exp_sh_setts = {u'n': 2, u'continuer': u'_', u'mark singles': False,
                        u'interval quality': False, u'simple intervals': False,
                        u'include rests': False, u'count frequency': True}
        self.assertEqual(exp_sh_setts, test_wc._shared_settings)

    def test_load_1(self):
        # that "get_data" is called correctly on each thing
        test_wc = WorkflowManager([])
        test_wc._data = [mock.MagicMock(spec=IndexedPiece) for _ in xrange(5)]
        test_wc.load(u'pieces')
        for mock_piece in test_wc._data:
            mock_piece.get_data.assert_called_once_with([noterest.NoteRestIndexer])
        self.assertTrue(test_wc._loaded)

    def test_load_2(self):
        # that the not-yet-implemented instructions raise NotImplementedError
        test_wc = WorkflowManager([])
        self.assertRaises(NotImplementedError, test_wc.load, u'hdf5')
        self.assertRaises(NotImplementedError, test_wc.load, u'stata')
        self.assertRaises(NotImplementedError, test_wc.load, u'pickle')

    def test_load_3(self):
        # NB: this is more of an integration test
        test_wc = WorkflowManager([u'vis/tests/corpus/try_opus.krn'])
        test_wc.load('pieces')
        self.assertEqual(3, len(test_wc))
        # NOTE: we have to do this by digging until music21 imports metadata from **kern files, at
        #       which point we'll be able to use our very own metadata() method
        exp_names = [u'Alex', u'Sarah', u'Emerald']
        for i in xrange(3):
            # first Score gets some extra metadata
            which_el = 5 if i == 0 else 3
            piece = test_wc._data[i]._import_score()
            self.assertTrue(isinstance(piece[which_el], GlobalReference))
            self.assertEqual(u'COM', piece[which_el].code)
            self.assertEqual(exp_names[i], piece[which_el].value)
        # NOTE: once music21 works:
        #exp_names = [u'Alex', u'Sarah', u'Emerald']
        #for i in xrange(3):
            #self.assertEqual(exp_names[i], test_wc.metadata(i, 'composer'))

    def test_load_4(self):
        # that incorrect instructions cause load() to raise a RuntimeError
        test_wc = WorkflowManager([])
        self.assertRaises(RuntimeError, test_wc.load, u'piece')
        self.assertRaises(RuntimeError, test_wc.load, u'all the data')
        self.assertRaises(RuntimeError, test_wc.load, u'not sure why I wanted three of these')

    def test_run_1(self):
        # properly deals with "intervals" experiment
        mock_path = u'vis.workflow.WorkflowManager._intervs'
        with mock.patch(mock_path) as mock_meth:
            mock_meth.return_value = u'the final countdown'
            test_wc = WorkflowManager([])
            test_wc._loaded = True
            test_wc.run(u'intervals')
            mock_meth.assert_called_once_with()
            self.assertEqual(mock_meth.return_value, test_wc._result)
            self.assertEqual(u'intervals', test_wc._previous_exp)

    def test_run_2(self):
        # properly deals with "interval n-grams" experiment
        mock_path = u'vis.workflow.WorkflowManager._interval_ngrams'
        with mock.patch(mock_path) as mock_meth:
            mock_meth.return_value = u'the final countdown'
            test_wc = WorkflowManager([])
            test_wc._loaded = True
            test_wc.run(u'interval n-grams')
            mock_meth.assert_called_once_with()
            self.assertEqual(mock_meth.return_value, test_wc._result)
            self.assertEqual(u'n-grams', test_wc._previous_exp)

    def test_run_3(self):
        # raise RuntimeError with invalid instructions
        test_wc = WorkflowManager([])
        test_wc._loaded = True
        self.assertRaises(RuntimeError, test_wc.run, u'too short')
        self.assertRaises(RuntimeError, test_wc.run, u'this just is not an instruction you know')

    def test_run_4(self):
        # raise RuntimeError when load() has not been called
        test_wc = WorkflowManager([])
        test_wc._loaded = False
        self.assertRaises(RuntimeError, test_wc.run, u'intervals')


class Output(TestCase):
    def test_output_1(self):
        test_wc = WorkflowManager([])
        self.assertRaises(NotImplementedError, test_wc.output, u'LilyPond')

    def test_output_2(self):
        test_wc = WorkflowManager([])
        self.assertRaises(RuntimeError, test_wc.output, u'LJKDSFLAESFLKJ')

    def test_output_3(self):
        # with self._result as None
        test_wc = WorkflowManager([])
        self.assertRaises(RuntimeError, test_wc.output, u'R histogram')

    @mock.patch(u'vis.workflow.WorkflowManager._get_dataframe')
    @mock.patch(u'subprocess.check_output')
    def test_output_4(self, mock_call, mock_gdf):
        # with specified pathname; last experiment was intervals with 20 pieces; self._result is DF
        test_wc = WorkflowManager([])
        test_wc._previous_exp = u'intervals'
        test_wc._data = [1 for _ in xrange(20)]
        test_wc._result = MagicMock(spec=pandas.DataFrame)
        path = u'pathname!'
        actual = test_wc.output(u'R histogram', path)
        self.assertEqual(0, mock_gdf.call_count)
        expected_args = [u'Rscript', u'--vanilla', WorkflowManager._R_bar_chart_path,
                         path + u'.dta', path + u'.png', u'int', u'20']
        mock_call.assert_called_once_with(expected_args)
        self.assertEqual(path + u'.png', actual)

    @mock.patch(u'vis.workflow.WorkflowManager._get_dataframe')
    @mock.patch(u'subprocess.check_output')
    def test_output_5(self, mock_call, mock_gdf):
        # with unspecified pathname; last experiment was 14-grams with 1 piece; self._result is S
        test_wc = WorkflowManager([])
        test_wc._previous_exp = u'n-grams'
        test_wc._data = [1]
        test_wc._shared_settings[u'n'] = 14
        test_wc._result = MagicMock(spec=pandas.Series)
        path = u'test_output/output_result'
        actual = test_wc.output(u'R histogram')
        mock_gdf.assert_called_once_with(u'freq', None, None)
        expected_args = [u'Rscript', u'--vanilla', WorkflowManager._R_bar_chart_path,
                         path + u'.dta', path + u'.png', u'14', u'1']
        mock_call.assert_called_once_with(expected_args)
        self.assertEqual(path + u'.png', actual)

    @mock.patch(u'vis.workflow.WorkflowManager._get_dataframe')
    @mock.patch(u'subprocess.check_output')
    def test_output_6(self, mock_call, mock_gdf):
        # test_ouput_6, plus top_x and threshold
        test_wc = WorkflowManager([])
        test_wc._previous_exp = u'n-grams'
        test_wc._data = [1]
        test_wc._shared_settings[u'n'] = 14
        test_wc._result = MagicMock(spec=pandas.Series)
        path = u'test_output/output_result'
        actual = test_wc.output(u'R histogram', top_x=420, threshold=1987)
        mock_gdf.assert_called_once_with(u'freq', 420, 1987)
        expected_args = [u'Rscript', u'--vanilla', WorkflowManager._R_bar_chart_path,
                         path + u'.dta', path + u'.png', u'14', u'1']
        mock_call.assert_called_once_with(expected_args)
        self.assertEqual(path + u'.png', actual)

    @mock.patch(u'vis.workflow.WorkflowManager._get_dataframe')
    @mock.patch(u'subprocess.check_output')
    def test_output_7(self, mock_call, mock_gdf):
        # test_output_4() but the subprocess thing fails
        def raiser(*args):
            raise CalledProcessError(u'Bach!', 42, u'CPE')
        mock_call.side_effect = raiser
        test_wc = WorkflowManager([])
        test_wc._previous_exp = u'intervals'
        test_wc._data = [1 for _ in xrange(20)]
        test_wc._result = MagicMock(spec=pandas.DataFrame)
        path = u'pathname!'
        expected_msg = u'Error during call to R: CPE (return code: Bach!)'
        actual = None
        try:
            test_wc.output(u'R histogram', path)
        except RuntimeError as run_e:
            actual = run_e
        self.assertEqual(expected_msg, actual.message)
        self.assertEqual(0, mock_gdf.call_count)
        expected_args = [u'Rscript', u'--vanilla', WorkflowManager._R_bar_chart_path,
                         path + u'.dta', path + u'.png', u'int', u'20']
        mock_call.assert_called_once_with(expected_args)


class Settings(TestCase):
    @mock.patch(u'vis.models.indexed_piece.IndexedPiece')
    def test_settings_1(self, mock_ip):
        # - if index is None and value are None, raise ValueError
        test_wm = WorkflowManager([u'a', u'b', u'c'])
        self.assertEqual(3, mock_ip.call_count)  # to make sure we're using the mock, not real IP
        self.assertRaises(ValueError, test_wm.settings, None, u'filter repeats', None)
        self.assertRaises(ValueError, test_wm.settings, None, u'filter repeats')

    @mock.patch(u'vis.models.indexed_piece.IndexedPiece')
    def test_settings_2(self, mock_ip):
        # - if index is None, field and value are valid, it'll set for all IPs
        test_wm = WorkflowManager([u'a', u'b', u'c'])
        self.assertEqual(3, mock_ip.call_count)  # to make sure we're using the mock, not real IP
        test_wm.settings(None, u'filter repeats', True)
        for i in xrange(3):
            self.assertEqual(True, test_wm._settings[i][u'filter repeats'])

    @mock.patch(u'vis.models.indexed_piece.IndexedPiece')
    def test_settings_3(self, mock_ip):
        # - if index is less than 0 or greater-than-valid, raise IndexError
        test_wm = WorkflowManager([u'a', u'b', u'c'])
        self.assertEqual(3, mock_ip.call_count)  # to make sure we're using the mock, not real IP
        self.assertRaises(IndexError, test_wm.settings, -1, u'filter repeats')
        self.assertRaises(IndexError, test_wm.settings, 20, u'filter repeats')

    @mock.patch(u'vis.models.indexed_piece.IndexedPiece')
    def test_settings_4(self, mock_ip):
        # - if index is 0, return proper setting
        test_wm = WorkflowManager([u'a', u'b', u'c'])
        self.assertEqual(3, mock_ip.call_count)  # to make sure we're using the mock, not real IP
        test_wm._settings[0][u'filter repeats'] = u'cheese'
        self.assertEqual(u'cheese', test_wm.settings(0, u'filter repeats'))

    @mock.patch(u'vis.models.indexed_piece.IndexedPiece')
    def test_settings_5(self, mock_ip):
        # - if index is greater than 0 but valid, set proper setting
        test_wm = WorkflowManager([u'a', u'b', u'c'])
        self.assertEqual(3, mock_ip.call_count)  # to make sure we're using the mock, not real IP
        test_wm.settings(1, u'filter repeats', u'leeks')
        self.assertEqual(u'leeks', test_wm._settings[1][u'filter repeats'])

    @mock.patch(u'vis.models.indexed_piece.IndexedPiece')
    def test_settings_6(self, mock_ip):
        # - if index is valid but the setting isn't, raise AttributeError (with or without a value)
        test_wm = WorkflowManager([u'a', u'b', u'c'])
        self.assertEqual(3, mock_ip.call_count)  # to make sure we're using the mock, not real IP
        self.assertRaises(AttributeError, test_wm.settings, 1, u'drink wine')
        self.assertRaises(AttributeError, test_wm.settings, 1, u'drink wine', True)

    @mock.patch(u'vis.models.indexed_piece.IndexedPiece')
    def test_settings_7(self, mock_ip):
        # - we can properly fetch a "shared setting"
        test_wm = WorkflowManager([u'a', u'b', u'c'])
        self.assertEqual(3, mock_ip.call_count)  # to make sure we're using the mock, not real IP
        test_wm._shared_settings[u'n'] = 4000
        self.assertEqual(4000, test_wm.settings(None, u'n'))

    @mock.patch(u'vis.models.indexed_piece.IndexedPiece')
    def test_settings_8(self, mock_ip):
        # - we can properly set a "shared setting"
        test_wm = WorkflowManager([u'a', u'b', u'c'])
        self.assertEqual(3, mock_ip.call_count)  # to make sure we're using the mock, not real IP
        test_wm.settings(None, u'n', 4000)
        self.assertEqual(4000, test_wm._shared_settings[u'n'])

    @mock.patch(u'vis.models.indexed_piece.IndexedPiece')
    def test_settings_0(self, mock_ip):
        # - if trying to set 'offset interval' to 0, it should actually be set to None
        test_wm = WorkflowManager([u'a', u'b', u'c'])
        self.assertEqual(3, mock_ip.call_count)  # to make sure we're using the mock, not real IP
        # "None" is default value, so first set to non-zero
        test_wm.settings(1, u'offset interval', 4.0)
        self.assertEqual(4.0, test_wm._settings[1][u'offset interval'])
        # now run our test
        test_wm.settings(1, u'offset interval', 0)
        self.assertEqual(None, test_wm._settings[1][u'offset interval'])


class ExtraPairs(TestCase):
    def test_extra_pairs_1(self):
        # testing WorkflowManager._remove_extra_pairs()
        # --> when only desired pairs are present
        vert_ints = {'0,1': 1, '0,2': 2, '1,2': 3}
        combos = [[0, 1], [0, 2], [1, 2]]
        expected = {'0,1': 1, '0,2': 2, '1,2': 3}
        actual = WorkflowManager._remove_extra_pairs(vert_ints, combos)
        self.assertSequenceEqual(expected, actual)

    def test_extra_pairs_2(self):
        # testing WorkflowManager._remove_extra_pairs()
        # --> when no pairs are desired
        vert_ints = {'0,1': 1, '0,2': 2, '1,2': 3}
        combos = []
        expected = {}
        actual = WorkflowManager._remove_extra_pairs(vert_ints, combos)
        self.assertSequenceEqual(expected, actual)

    def test_extra_pairs_3(self):
        # testing WorkflowManager._remove_extra_pairs()
        # --> when there are desired pairs, but they are not present
        vert_ints = {'0,1': 1, '0,2': 2, '1,2': 3}
        combos = [[4, 20], [11, 12]]
        expected = {}
        actual = WorkflowManager._remove_extra_pairs(vert_ints, combos)
        self.assertSequenceEqual(expected, actual)

    def test_extra_pairs_4(self):
        # testing WorkflowManager._remove_extra_pairs()
        # --> when there are lots of pairs, only some of which are desired
        vert_ints = {'4,20': 0, '0,1': 1, '11,12': 4, '0,2': 2, '1,2': 3, '256,128': 12}
        combos = [[0, 1], [0, 2], [1, 2]]
        expected = {'0,1': 1, '0,2': 2, '1,2': 3}
        actual = WorkflowManager._remove_extra_pairs(vert_ints, combos)
        self.assertSequenceEqual(expected, actual)

    def test_extra_pairs_5(self):
        # --> when there are lots of pairs, only some of which are desired, and there are invalid
        vert_ints = {'4,20': 0, '0,1': 1, '11,12': 4, '0,2': 2, '1,2': 3, '256,128': 12}
        combos = [[0, 1], [1, 2, 3, 4, 5], [0, 2], [1, 2], [9, 11, 43], [4]]
        expected = {'0,1': 1, '0,2': 2, '1,2': 3}
        actual = WorkflowManager._remove_extra_pairs(vert_ints, combos)
        self.assertSequenceEqual(expected, actual)


class Export(TestCase):
    def test_export_1(self):
        # --> raise RuntimeError with unrecognized output format
        test_wm = WorkflowManager([])
        test_wm._result = pandas.Series(xrange(100))
        self.assertRaises(RuntimeError, test_wm.export, u'PowerPoint')

    def test_export_2(self):
        # --> raise RuntimeError if run() hasn't been called (i.e., self._result is None)
        test_wm = WorkflowManager([])
        self.assertRaises(RuntimeError, test_wm.export, u'Excel', u'C:\autoexec.bat')

    @mock.patch(u'vis.workflow.WorkflowManager._get_dataframe')
    def test_export_3(self, mock_gdf):
        # --> the method works as expected for CSV, Excel, and Stata when _result is a DataFrame
        test_wm = WorkflowManager([])
        test_wm._result = mock.MagicMock(spec=pandas.DataFrame)
        test_wm.export(u'CSV', u'test_path')
        test_wm.export(u'Excel', u'test_path')
        test_wm.export(u'Stata', u'test_path')
        test_wm.export(u'HTML', u'test_path')
        test_wm._result.to_csv.assert_called_once_with(u'test_path.csv')
        test_wm._result.to_stata.assert_called_once_with(u'test_path.dta')
        test_wm._result.to_excel.assert_called_once_with(u'test_path.xlsx')
        test_wm._result.to_html.assert_called_once_with(u'test_path.html')
        self.assertEqual(0, mock_gdf.call_count)

    @mock.patch(u'vis.workflow.WorkflowManager._get_dataframe')
    def test_export_4(self, mock_gdf):
        # --> test_export_3() with a valid extension already on
        test_wm = WorkflowManager([])
        test_wm._result = mock.MagicMock(spec=pandas.DataFrame)
        test_wm.export(u'CSV', u'test_path.csv')
        test_wm.export(u'Excel', u'test_path.xlsx')
        test_wm.export(u'Stata', u'test_path.dta')
        test_wm.export(u'HTML', u'test_path.html')
        test_wm._result.to_csv.assert_called_once_with(u'test_path.csv')
        test_wm._result.to_stata.assert_called_once_with(u'test_path.dta')
        test_wm._result.to_excel.assert_called_once_with(u'test_path.xlsx')
        test_wm._result.to_html.assert_called_once_with(u'test_path.html')
        self.assertEqual(0, mock_gdf.call_count)

    @mock.patch(u'vis.workflow.WorkflowManager._get_dataframe')
    def test_export_5(self, mock_gdf):
        # --> test_export_3() with a Series that requires calling _get_dataframe()
        test_wm = WorkflowManager([])
        test_wm._result = mock.MagicMock(spec=pandas.Series)
        # CSV
        mock_gdf.return_value = MagicMock(spec=pandas.DataFrame)
        test_wm.export(u'CSV', u'test_path')
        mock_gdf.assert_called_once_with(u'data', None, None)
        mock_gdf.return_value.to_csv.assert_called_once_with(u'test_path.csv')
        mock_gdf.reset_mock()
        # Excel
        test_wm.export(u'Excel', u'test_path', 5)
        mock_gdf.assert_called_once_with(u'data', 5, None)
        mock_gdf.return_value.to_excel.assert_called_once_with(u'test_path.xlsx')
        mock_gdf.reset_mock()
        # Stata
        test_wm.export(u'Stata', u'test_path', 5, 10)
        mock_gdf.assert_called_once_with(u'data', 5, 10)
        mock_gdf.return_value.to_stata.assert_called_once_with(u'test_path.dta')
        mock_gdf.reset_mock()
        # HTML
        test_wm.export(u'HTML', u'test_path', threshold=10)
        mock_gdf.assert_called_once_with(u'data', None, 10)
        mock_gdf.return_value.to_html.assert_called_once_with(u'test_path.html')

    def test_export_6(self):
        # --> the method always outputs a DataFrame, even if self._result isn't a DF yet
        # TODO: I don't know how to test this. I want to mock DataFrame, but it also needs to pass
        #       the isinstance() test, so it can't be a MagicMock unless it's a MagicMock instance
        #       of DataFrame, which is impossible(?) because I have to patch it at
        #       vis.workflow.pandas.DataFrame
        pass


class GetDataFrame(TestCase):
    def test_get_dataframe_1(self):
        # test with name=auto, top_x=auto, threshold=auto
        test_wc = WorkflowManager([])
        test_wc._result = pandas.Series([i for i in xrange(10, 0, -1)])
        expected = pandas.DataFrame({'data': pandas.Series([i for i in xrange(10, 0, -1)])})
        actual = test_wc._get_dataframe()
        self.assertEqual(len(expected.columns), len(actual.columns))
        for i in expected.columns:
            self.assertSequenceEqual(list(expected.loc[:,i].index), list(actual.loc[:,i].index))
            self.assertSequenceEqual(list(expected.loc[:,i].values), list(actual.loc[:,i].values))

    def test_get_dataframe_2(self):
        # test with name='asdf', top_x=3, threshold=auto
        test_wc = WorkflowManager([])
        test_wc._result = pandas.Series([i for i in xrange(10, 0, -1)])
        expected = pandas.DataFrame({'asdf': pandas.Series([10, 9, 8])})
        actual = test_wc._get_dataframe('asdf', 3)
        self.assertEqual(len(expected.columns), len(actual.columns))
        for i in expected.columns:
            self.assertSequenceEqual(list(expected.loc[:,i].index), list(actual.loc[:,i].index))
            self.assertSequenceEqual(list(expected.loc[:,i].values), list(actual.loc[:,i].values))

    def test_get_dataframe_3(self):
        # test with name=auto, top_x=3, threshold=5 (so the top_x still removes after threshold)
        test_wc = WorkflowManager([])
        test_wc._result = pandas.Series([i for i in xrange(10, 0, -1)])
        expected = pandas.DataFrame({'data': pandas.Series([10, 9, 8])})
        actual = test_wc._get_dataframe(top_x=3, threshold=5)
        self.assertEqual(len(expected.columns), len(actual.columns))
        for i in expected.columns:
            self.assertSequenceEqual(list(expected.loc[:,i].index), list(actual.loc[:,i].index))
            self.assertSequenceEqual(list(expected.loc[:,i].values), list(actual.loc[:,i].values))

    def test_get_dataframe_4(self):
        # test with name=auto, top_x=5, threshold=7 (so threshold leaves fewer than 3 results)
        test_wc = WorkflowManager([])
        test_wc._result = pandas.Series([i for i in xrange(10, 0, -1)])
        expected = pandas.DataFrame({'data': pandas.Series([10, 9, 8])})
        actual = test_wc._get_dataframe(top_x=5, threshold=7)
        self.assertEqual(len(expected.columns), len(actual.columns))
        for i in expected.columns:
            self.assertSequenceEqual(list(expected.loc[:,i].index), list(actual.loc[:,i].index))
            self.assertSequenceEqual(list(expected.loc[:,i].values), list(actual.loc[:,i].values))


class AuxiliaryExperimentMethods(TestCase):
    @mock.patch(u'vis.workflow.repeat.FilterByRepeatIndexer')
    @mock.patch(u'vis.workflow.offset.FilterByOffsetIndexer')
    def test_run_off_rep_1(self, mock_off, mock_rep):
        # run neither indexer
        # setup
        workm = WorkflowManager(['', '', ''])
        workm._data = [None, MagicMock(spec=IndexedPiece), None]
        workm.settings(1, 'offset interval', 0)
        workm.settings(1, 'filter repeats', False)
        in_val = 42
        # run
        actual = workm._run_off_rep(1, in_val)
        # test
        self.assertEqual(in_val, actual)
        self.assertEqual(0, workm._data[1].get_data.call_count)

    @mock.patch(u'vis.workflow.repeat.FilterByRepeatIndexer')
    @mock.patch(u'vis.workflow.offset.FilterByOffsetIndexer')
    def test_run_off_rep_2(self, mock_off, mock_rep):
        # run offset indexer
        # setup
        workm = WorkflowManager(['', '', ''])
        workm._data = [None, MagicMock(spec=IndexedPiece), None]
        workm._data[1].get_data.return_value = 24
        workm.settings(1, 'offset interval', 0.5)
        workm.settings(1, 'filter repeats', False)
        in_val = 42
        # run
        actual = workm._run_off_rep(1, in_val)
        # test
        self.assertEqual(workm._data[1].get_data.return_value, actual)
        workm._data[1].get_data.assert_called_once_with([mock_off], {'quarterLength': 0.5}, in_val)

    @mock.patch(u'vis.workflow.repeat.FilterByRepeatIndexer')
    @mock.patch(u'vis.workflow.offset.FilterByOffsetIndexer')
    def test_run_off_rep_3(self, mock_off, mock_rep):
        # run repeat indexer
        # setup
        workm = WorkflowManager(['', '', ''])
        workm._data = [None, MagicMock(spec=IndexedPiece), None]
        workm._data[1].get_data.return_value = 24
        workm.settings(1, 'offset interval', 0)
        workm.settings(1, 'filter repeats', True)
        in_val = 42
        # run
        actual = workm._run_off_rep(1, in_val)
        # test
        self.assertEqual(workm._data[1].get_data.return_value, actual)
        workm._data[1].get_data.assert_called_once_with([mock_rep], {}, in_val)

    @mock.patch(u'vis.workflow.repeat.FilterByRepeatIndexer')
    @mock.patch(u'vis.workflow.offset.FilterByOffsetIndexer')
    def test_run_off_rep_4(self, mock_off, mock_rep):
        # run offset and repeat indexer
        # setup
        workm = WorkflowManager(['', '', ''])
        workm._data = [None, MagicMock(spec=IndexedPiece), None]
        workm._data[1].get_data.return_value = 24
        workm.settings(1, 'offset interval', 0.5)
        workm.settings(1, 'filter repeats', True)
        in_val = 42
        # run
        actual = workm._run_off_rep(1, in_val)
        # test
        self.assertEqual(workm._data[1].get_data.return_value, actual)
        self.assertEqual(2, workm._data[1].get_data.call_count)
        workm._data[1].get_data.assert_any_call([mock_off], {'quarterLength': 0.5}, in_val)
        workm._data[1].get_data.assert_any_call([mock_rep], {}, workm._data[1].get_data.return_value)

    @mock.patch(u'vis.workflow.repeat.FilterByRepeatIndexer')
    @mock.patch(u'vis.workflow.offset.FilterByOffsetIndexer')
    def test_run_off_rep_5(self, mock_off, mock_rep):
        # run neither indexer; input a dict
        # setup
        workm = WorkflowManager(['', '', ''])
        workm._data = [None, MagicMock(spec=IndexedPiece), None]
        workm.settings(1, 'offset interval', 0)
        workm.settings(1, 'filter repeats', False)
        in_val = {'b': 43, 'a': 42, 'c': 44}
        # run
        actual = workm._run_off_rep(1, in_val)
        # test
        self.assertSequenceEqual(in_val, actual)
        self.assertEqual(0, workm._data[1].get_data.call_count)

#-------------------------------------------------------------------------------------------------#
# Definitions                                                                                     #
#-------------------------------------------------------------------------------------------------#
WORKFLOW_TESTS = TestLoader().loadTestsFromTestCase(WorkflowTests)
GET_DATA_FRAME = TestLoader().loadTestsFromTestCase(GetDataFrame)
EXPORT = TestLoader().loadTestsFromTestCase(Export)
EXTRA_PAIRS = TestLoader().loadTestsFromTestCase(ExtraPairs)
SETTINGS = TestLoader().loadTestsFromTestCase(Settings)
OUTPUT = TestLoader().loadTestsFromTestCase(Output)
AUX_METHODS = TestLoader().loadTestsFromTestCase(AuxiliaryExperimentMethods)
