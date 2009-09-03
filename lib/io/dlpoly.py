# MolMod is a collection of molecular modelling tools for python.
# Copyright (C) 2007 - 2008 Toon Verstraelen <Toon.Verstraelen@UGent.be>
#
# This file is part of MolMod.
#
# MolMod is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# MolMod is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>
#
# --
"""Readers for DLPoly file formats"""


from molmod.units import picosecond, amu, angstrom, atm, deg
from molmod.io.common import slice_match, FileFormatError

import numpy


__all__ = ["DLPolyHistoryReader", "DLPolyOutputReader"]


class DLPolyHistoryReader(object):
    """A Reader for the DLPoly history file format.

       Use this object as an iterator:

       >>> hr = HistoryReader("somefile.txt")
       >>> for frame in hr:
       ...     print frame["cell"]
    """
    def __init__(self, filename, sub=slice(None), pos_unit=angstrom,
        vel_unit=angstrom/picosecond, frc_unit=amu*angstrom/picosecond**2,
        time_unit=picosecond, mass_unit=amu
    ):
        """Initialize a DLPoly history reader

           Arguments:
             filename  --  the file with the history data
             sub  --  a slice indicating the frames to be skipped/selected
             pos_unit, vel_unit, frc_unit, time_unit, mass_unit
                  --  The conversion factors for the unit conversion from the
                      units in the data file to atomic units. The defaults
                      of these optional arguments correspond to the defaults of
                      dlpoly.
        """
        self._f = file(filename)
        self._sub = sub
        self.pos_unit = pos_unit
        self.vel_unit = vel_unit
        self.frc_unit = frc_unit
        self.time_unit = time_unit
        self.mass_unit = mass_unit
        try:
            self.header = self._f.next()[:-1]
            integers = tuple(int(word) for word in self._f.next().split())
            if len(integers) != 3:
                raise FileFormatError("Second line must contain three integers.")
            self.keytrj, self.imcon, self.num_atoms = integers
        except StopIteration:
            raise FileFormatError("File is too short. Could not read header.")
        except ValueError:
            raise FileFormatError("Second line must contain three integers.")
        self._counter = 1
        self._frame_size = 4 + self.num_atoms*(self.keytrj+2)

    def __del__(self):
        self._f.close()

    def __iter__(self):
        return self

    def next(self):
        """Read the next frame

           This method is part of the iterator protocol.
        """
        # auxiliary read function
        def read_three(msg):
            """Read three words as floating point numbers"""
            line = self._f.next()
            try:
                return [float(line[:12]), float(line[12:24]), float(line[24:])]
            except ValueError:
                raise FileFormatError(msg)

        # skip frames as requested
        while not slice_match(self._sub, self._counter):
            for i in xrange(self._frame_size):
                self._f.next()
            self._counter += 1

        frame = {}
        # read the frame header line
        words = self._f.next().split()
        if len(words) != 6:
            raise FileFormatError("The first line of each time frame must contain 6 words. (%i'th frame)" % self._counter)
        if words[0] != "timestep":
            raise FileFormatError("The first word of the first line of each time frame must be 'timestep'. (%i'th frame)" % self._counter)
        try:
            step = int(words[1])
            frame["step"] = step
            if int(words[2]) != self.num_atoms:
                raise FileFormatError("The number of atoms has changed. (%i'th frame, %i'th step)" % (self._counter, step))
            if int(words[3]) != self.keytrj:
                raise FileFormatError("keytrj has changed. (%i'th frame, %i'th step)" % (self._counter, step))
            if int(words[4]) != self.imcon:
                raise FileFormatError("imcon has changed. (%i'th frame, %i'th step)" % (self._counter, step))
            frame["timestep"] = float(words[5])*self.time_unit
            frame["time"] = frame["timestep"]*step # this is ugly, or wait ... dlpoly is a bit ugly. we are not to blame!
        except ValueError:
            raise FileFormatError("Could not convert all numbers on the first line of the current time frame. (%i'th frame)" % self._counter)
        # the three cell lines
        cell = numpy.zeros((3, 3), float)
        frame["cell"] = cell
        cell_msg = "The cell lines must consist of three floating point values. (%i'th frame, %i'th step)" % (self._counter, step)
        for i in xrange(3):
            cell[:, i] = read_three(cell_msg)
        cell *= self.pos_unit
        # the atoms
        symbols = []
        frame["symbols"] = symbols
        masses = numpy.zeros(self.num_atoms, float)
        frame["masses"] = masses
        charges = numpy.zeros(self.num_atoms, float)
        frame["charges"] = charges
        pos = numpy.zeros((self.num_atoms, 3), float)
        frame["pos"] = pos
        if self.keytrj > 0:
            vel = numpy.zeros((self.num_atoms, 3), float)
            frame["vel"] = vel
        if self.keytrj > 1:
            frc = numpy.zeros((self.num_atoms, 3), float)
            frame["frc"] = frc
        for i in xrange(self.num_atoms):
            # the atom header line
            words = self._f.next().split()
            if len(words) != 4:
                raise FileFormatError("The atom header line must contain 4 words. (%i'th frame, %i'th step, %i'th atom)" % (self._counter, step, i+1))
            symbols.append(words[0])
            try:
                masses[i] = float(words[2])*self.mass_unit
                charges[i] = float(words[3])
            except ValueError:
                raise FileFormatError("The numbers in the atom header line could not be interpreted.")
            # the pos line
            pos_msg = "The position lines must consist of three floating point values. (%i'th frame, %i'th step, %i'th atom)" % (self._counter, step, i+1)
            pos[i] = read_three(pos_msg)
            if self.keytrj > 0:
                vel_msg = "The velocity lines must consist of three floating point values. (%i'th frame, %i'th step, %i'th atom)" % (self._counter, step, i+1)
                vel[i] = read_three(vel_msg)
            if self.keytrj > 1:
                frc_msg = "The force lines must consist of three floating point values. (%i'th frame, %i'th step, %i'th atom)" % (self._counter, step, i+1)
                frc[i] = read_three(frc_msg)
        pos *= self.pos_unit # convert to au
        if self.keytrj > 0:
            vel *= self.vel_unit # convert to au
        if self.keytrj > 1:
            frc *= self.frc_unit # convert to au
        # done
        self._counter += 1
        return frame


class DLPolyOutputReader(object):
    """A Reader for DLPoly output files.

       Use this object as an iterator:
       >>> or = OutputReader("somefile.txt")
       >>> for row in or:
       ...     print row[5]

       The variable row in the example above is a concatenation of all the
       values that belong to one time frame. (line after line)
    """

    _marker = " " + "-"*130

    def __init__(self, filename, sub=slice(None), skip_equi_period=True,
        pos_unit=angstrom, time_unit=picosecond, angle_unit=deg,
        e_unit=amu/(angstrom/picosecond)**2
    ):
        """Initialize a DLPoly output reader

           Arguments:
             filename  --  the file with the history data
             sub  --  a slice indicating the frames to be skipped/selected
             skip_equi_period  -- When True, the equilibration period is not
                                  read (default=True)
             pos_unit, time_unit, angle_unit, e_unit
                  --  The conversion factors for the unit conversion from the
                      units in the data file to atomic units. The defaults
                      of these optional arguments correspond to the defaults of
                      dlpoly.
        """
        self._f = file(filename)
        self._sub = sub
        self.skip_equi_period = skip_equi_period
        self._counter = 1

        self._conv = [
            1,         e_unit,      1, e_unit, e_unit, e_unit,     e_unit,     e_unit,     e_unit, e_unit,
            time_unit, e_unit,      1, e_unit, e_unit, e_unit,     e_unit,     e_unit,     e_unit, e_unit,
            1,         pos_unit**3, 1, e_unit, e_unit, angle_unit, angle_unit, angle_unit, e_unit, 1000*atm,
        ]
        self.last_step = None

        # find the line that gives the number of equilibration steps:
        try:
            while True:
                line = self._f.next()
                if line.startswith(" equilibration period"):
                    self.equi_period = int(line[30:])
                    break
        except StopIteration:
            raise FileFormatError("DL_POLY OUTPUT file is too short. Could not find line with the number of equilibration steps.")
        except ValueError:
            raise FileFormatError("Could not read the number of equilibration steps. (expecting an integer)")

    def __del__(self):
        self._f.close()

    def __iter__(self):
        return self

    def next(self):
        """Read the next frame from the file

           This method is part of the iterator protocol.
        """
        def goto_next_frame():
            """Continue reading until the next frame is reached"""
            marked = False
            while True:
                line = self._f.next()[:-1]
                if marked and len(line) > 0 and not line.startswith(" --------"):
                    try:
                        step = int(line[:10])
                        return step, line
                    except ValueError:
                        pass
                marked = (len(line) == 131 and line == self._marker)

        while True:
            step, line = goto_next_frame()
            if (not self.skip_equi_period or step >= self.equi_period) and \
               step != self.last_step:
                break

        # skip frames as requested
        while not slice_match(self._sub, self._counter):
            step, line = goto_next_frame()
            self._counter += 1

        # now really read these three lines
        try:
            row = [step]
            for i in xrange(9):
                row.append(float(line[10+i*12:10+(i+1)*12]))
            line = self._f.next()[:-1]
            row.append(float(line[:10]))
            for i in xrange(9):
                row.append(float(line[10+i*12:10+(i+1)*12]))
            line = self._f.next()[:-1]
            row.append(float(line[:10]))
            for i in xrange(9):
                row.append(float(line[10+i*12:10+(i+1)*12]))
        except ValueError:
            raise FileFormatError("Some numbers in the output file could not be read. (expecting floating point numbers)")

        # convert all the numbers to atomic units
        for i in xrange(30):
            row[i] *= self._conv[i]

        # done
        self.last_step = step
        return row

