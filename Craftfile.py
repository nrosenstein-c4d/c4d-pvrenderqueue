# PV Render Queue Cinema 4D Plugin
# Copyright (C) 2015  Niklas Rosenstein
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
#
# craftr_module(nr.pvrenderqueue)

from craftr import *
from craftr.ext.maxon.py4d import create_distro_task, extract_symbols_task, Egg

symbols = extract_symbols_task(format = 'class')
distro = create_distro_task(
  source_dir = path.local('devel'),
  eggs = [Egg(
    name = 'nr.pvrq2.egg',
    files = ['nr.pvrq2/nr'],
    zipped = False
  )],
)
