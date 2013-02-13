#! /usr/bin/python
# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Program Name:              vis
# Program Description:       Measures sequences of vertical intervals.
#
# Filename: Importer.py
# Purpose: Holds the Importer controller.
#
# Copyright (C) 2012 Jamie Klassen, Christopher Antila
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#-------------------------------------------------------------------------------
'''
Holds the Importer controller.
'''



# Imports from...
# python
from os import path
from multiprocessing import Process, Value
# PyQt4
from PyQt4.QtCore import pyqtSignal, pyqtSlot, Qt
# music21
from music21 import converter
from music21.stream import Score
# vis
from controllers.controller import Controller
from models import importing, analyzing



class Importer(Controller):
   '''
   This class knows how to keep a list of filenames with pieces to be analyzed,
   and how to import the files with music21.

   The ListOfFiles model is always stored in the list_of_files property.
   '''



   # PyQt4 Signals
   # -------------
   # a list of str filenames to add to the list of files to analyze
   add_pieces_signal = pyqtSignal(list)
   # a list of str filenames to remove from the list of files to analyze
   remove_pieces_signal = pyqtSignal(list)
   # whether the add/remove operation was successful
   add_remove_success = pyqtSignal(bool)
   # create a ListOfPieces from the ListOfFiles
   run_import = pyqtSignal(analyzing.ListOfPieces)
   # the result of importer_import
   import_finished = pyqtSignal()
   # description of an error in the Importer
   error = pyqtSignal(str)
   # signal for each individual import
   piece_gotten = pyqtSignal(Score, str)
   # informs the GUI of the status for a currently-running import (if two or
   # three characters followed by a '%' then it should try to update a
   # progress bar, if available)
   status = pyqtSignal(str)



   def __init__(self, *args):
      '''
      Create a new Importer instance.
      '''
      # signals
      super(Controller, self).__init__() # required for signals
      self.piece_gotten.connect(self.catch_score)
      self.run_import.connect(self.import_pieces)
      self.add_pieces_signal.connect(self.add_pieces)
      self.remove_pieces_signal.connect(self.remove_pieces)
      # other things
      self._list_of_files = importing.ListOfFiles()
      self.post = analyzing.ListOfPieces()
      self.tasks_completed = 0



   def add_piece(self, piece):
      '''
      Call add_pieces() with the given argument.
      '''
      return self.add_pieces(piece)



   @pyqtSlot(list)
   def add_pieces(self, pieces):
      '''
      Add the filenames to the list of filenames that should be imported. The
      argument is a list of strings. If a filename is a directory, all the files
      in that directory (and its subdirectories) are added to the list.

      This method emits the Importer.error signal, with a description, in the
      following situations:
      - a pathname does not exist
      - a pathname is already in the list

      Emits the Importer.add_remove_success signal with True if there were no
      errors, or with False if there was at least one error.
      '''
      # Track whether there was an error
      we_are_error_free = True

      # Filter out paths that do not exist
      paths_that_exist = []
      for pathname in pieces:
         if path.exists(pathname):
            paths_that_exist.append(pathname)
         else:
            self.error.emit('Path does not exist: ' + str(pathname))
            we_are_error_free = False

      # If there's a directory, expand to the files therein
      directories_expanded = []
      for pathname in paths_that_exist:
         if path.isdir(pathname):
            pass # TODO: ??
         else:
            directories_expanded.append(pathname)

      # Ensure there will be no duplicates
      no_duplicates_list = []
      for pathname in directories_expanded:
         if not self._list_of_files.isPresent(pathname):
            no_duplicates_list.append(pathname)
         else:
            self.error.emit('Filename already on the list: ' + str(pathname))
            we_are_error_free = False

      # If there are no remaining files in the list, just return now
      if 0 == len(no_duplicates_list):
         return we_are_error_free

      # Add the number of rows we need
      first_index = self._list_of_files.rowCount()
      last_index = first_index + len(no_duplicates_list)
      self._list_of_files.insertRows(first_index, len(no_duplicates_list))

      # Add the files to the list
      for list_index in xrange(first_index, last_index):
         index = self._list_of_files.createIndex(list_index, 0)
         self._list_of_files.setData(index,
                                     no_duplicates_list[list_index-first_index],
                                     Qt.EditRole)

      return we_are_error_free



   @pyqtSlot(list)
   def remove_pieces(self, pieces):
      '''
      Remove the filenames from the list of filenames that should be imported.
      The argument is a list of strings. If a filename is a directory, all the
      files in that directory (and its subdirectories) are removed from the
      list.

      If the argument is a string, it is treated like a single filename.

      If a filename is not in the list, it is ignored.

      Emits the Importer.add_remove_success signal with True or
      False, depending on whether the operation succeeded. Returns that same
      value.
      '''
      # Is the argument a string? If so, make it a one-element list.
      if isinstance(pieces, str):
         pieces = [pieces]

      for piece_to_remove in pieces:
         # isPresent() either returns False or a QModelIndex referring to the
         # file we want to remove
         piece_index = self._list_of_files.isPresent(piece_to_remove)
         if piece_index is not False:
            # if the piece is actually in the list, remove it
            self._list_of_files.removeRows(piece_index.row(), 1)

      # I don't yet know of a situation that warrants a failure, so...
      self.add_remove_success.emit(True)
      return True


   @pyqtSlot(analyzing.ListOfPieces)
   def import_pieces(self, the_pieces):
      # TODO: replace this with the following version, which uses multiprocessing
      '''
      Transforms the current ListOfFiles into a ListOfPieces by importing the
      files specified, then extracting data as needed.

      Emits Importer.error if a file cannot be imported, but continues to
      import the rest of the files.

      Emits Importer.import_finished with the ListOfPieces when the import
      operation is completed, and returns the ListOfPieces.
      '''
      # NB: I must initialize the offset_intervals field to [0.5]
      # NB: I must initialize the parts_combinations field to []

      # hold the ListOfPieces that we'll return
      post = the_pieces

      for each_path in self._list_of_files:
         # Try to import the piece
         this_piece = self._get_piece(each_path)
         # Did it fail? Report the error
         if this_piece is None:
            self.error.emit('Unable to import this file: ' + str(each_path))
         # Otherwise keep working
         else:
            # prepare the ListOfPieces!
            post.insertRows(post.rowCount(), 1)
            new_row = post.rowCount() - 1
            post.setData((new_row, analyzing.ListOfPieces.filename),
                         each_path,
                         Qt.EditRole)
            post.setData((new_row, analyzing.ListOfPieces.score),
                         (this_piece, Importer._find_piece_title(this_piece)),
                         Qt.EditRole)
            post.setData((new_row, analyzing.ListOfPieces.parts_list),
                         Importer._find_part_names(this_piece),
                         Qt.EditRole)
            # Leave offset-interval and parts-combinations at defaults
      # return
      self.import_finished.emit()
      return post

   # TODO: make this version work (it's the one with multiprocessing)
   #@pyqtSlot(analyzing.ListOfPieces)
   #def import_pieces(self, the_pieces):
      #'''
      #Transforms the current ListOfFiles into a ListOfPieces by importing the
      #files specified, then extracting data as needed.

      #The argument is the ListOfPieces into which to load the data.

      #Emits Importer.error if a file cannot be imported, but continues to
      #import the rest of the files.

      #Emits Importer.import_finished with the ListOfPieces when the import
      #operation is completed, and returns the ListOfPieces.
      #'''
      ## NB: I must initialize the offset_intervals field to [0.5]
      ## NB: I must initialize the parts_combinations field to []
      #print('Len of _list_of_files: ' + str(self._list_of_files.rowCount())) # DEBUGGING

      ## hold the ListOfPieces that we'll return
      ##self.post = analyzing.ListOfPieces()
      #self.post = the_pieces
      #self.tasks_completed = 0
      #jobs = []
      #for each_path in self._list_of_files:
         ## Try to import the piece
         #p = Process(target=self._get_piece, args=(each_path,))
         #jobs.append(p)
         #p.start()
      #for job in jobs:
         #job.join()
      ## return
      #print('Len of pre-signal _list_of_pieces: ' + str(self.post.rowCount())) # DEBUGGING
      ##self.import_finished.emit(self.post) # commented for DEBUGGING
      #self.import_finished.emit()
      #return self.post



   # TODO: uncomment this when you need it, which will be for the multiprocessing version of import_pieces()
   @pyqtSlot(Score, str)
   def catch_score(self, score, path):
      pass
      #'''
      #Slot for the Importer.piece_getter_finished signal. Adds the analyzed piece
      #to the list of currently-imported pieces.
      #'''
      ## NB: I must initialize the offset_intervals field to [0.5]
      ## NB: I must initialize the parts_combinations field to []
      ## Did it fail? Report the error
      #if score is None:
         #self.error.emit('Unable to import this file: ' + str(path))
      ## Otherwise keep working
      #else:
         ## prepare the ListOfPieces!
         #self.post.insertRows(self.post.rowCount(), 1)
         #new_row = self.post.rowCount() - 1
         #self.post.setData((new_row, analyzing.ListOfPieces.filename),
                      #path,
                      #Qt.EditRole)
         #self.post.setData((new_row, analyzing.ListOfPieces.score),
                      #(score, Importer._find_piece_title(score)),
                      #Qt.EditRole)
         #self.post.setData((new_row, analyzing.ListOfPieces.parts_list),
                      #Importer._find_part_names(score),
                      #Qt.EditRole)
         ## Leave offset-interval and parts-combinations at defaults
      #self.tasks_completed += 1
      #percentage = float(self.tasks_completed)/len([f for f in self._list_of_files])*100
      #self.status.emit('{0:f}%'.format(percentage))



   def _get_piece(self, pathname):
      '''
      Wrapper for _piece_getter to manage signals.
      '''
      post = None
      try:
         post = self._piece_getter(pathname)
      except converter.ArchiveManagerException, converter.PickleFilterException:
         self.error.emit('Unable to import this file: ' + str(pathname))
      except converter.ConverterException, converter.ConverterFileException:
         self.error.emit('Unable to import this file: ' + str(pathname))
      self.piece_gotten.emit(post, pathname)
      return post # TODO: we only need this for the non-multiprocessing version!



   @staticmethod
   def _piece_getter(pathname):
      '''
      Load a file and import it to music21. Return the Score object.

      This method should only be called by the Importer.import_pieces() method,
      which coordinates multiprocessing.
      '''
      post = converter.parseFile(pathname)
      return post



   @staticmethod
   def _find_part_names(the_score):
      '''
      Returns a list with the names of the parts in the given Score.
      '''
      # hold the list of part names
      post = []

      # First try to find Instrument objects. If that doesn't work, use the "id"
      for each_part in the_score.parts:
         instr = each_part.getInstrument()
         if instr is not None and instr.partName != '':
            post.append(instr.partName)
         else:
            post.append(each_part.id)

      # Make sure none of the part names are just numbers; if they are, use
      # a part name like "Part 1" instead.
      for part_index in xrange(len(post)):
         try:
            int(post[part_index])
            # if that worked, the part name is just an integer...
            post[part_index] = 'Part ' + str(part_index+1)
         except ValueError:
            pass

      return post



   @staticmethod
   def _find_piece_title(the_score):
      '''
      Returns the title of this Score or an empty string.
      '''
      # hold the piece title
      post = ''

      # First try to get the title from a Metadata object, but if it doesn't
      # exist, use the filename without directory.
      if the_score.metadata is not None:
         post = the_score.metadata.title
      else:
         post = path.basename(the_score.filePath)

      # Now check that there is no file extension. This could happen either if
      # we used the filename or if music21 did a less-than-great job at the
      # Metadata object.
      post = path.splitext(post)[0]

      return post
# End class Importer -----------------------------------------------------------
