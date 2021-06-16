# This file is part of Octopus Sensing <https://octopus-sensing.nastaran-saffar.me/>
# Copyright © Nastaran Saffaryazdi 2020
#
# Octopus Sensing is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software Foundation,
#  either version 3 of the License, or (at your option) any later version.
#
# Octopus Sensing is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with Octopus Sensing.
# If not, see <https://www.gnu.org/licenses/>.

from typing import Optional
import multiprocessing
from multiprocessing.queues import Queue


class Device(multiprocessing.Process):
    '''All devices should inherit from Device class.'''

    def __init__(self, name: Optional[str] = None, output_path: str = "output"):
        super().__init__(name=name)
        self.message_queue: Optional[Queue] = None
        self.subject_id: Optional[str] = None
        self.stimulus_id: Optional[str] = None
        self.output_path: str = output_path

    def run(self) -> None:
        self._run()

    def _run(self) -> None:
        '''The subclass shouldn't implement 'run', but '_run' instead.'''
        raise NotImplementedError()

    def set_queue(self, queue: Queue) -> None:
        '''
        Sets message queue for the device

        @param queue: a queue that will be used for message passing
        '''
        self.message_queue = queue

    def get_name(self) -> str:
        '''
        Returns device name
        '''
        return self.name
