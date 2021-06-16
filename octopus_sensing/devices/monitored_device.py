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

import sys
import pickle
import multiprocessing.queues
import threading
import traceback
from typing import List, Any

from octopus_sensing.devices.device import Device

QueueType = multiprocessing.queues.Queue


class MonitoredDevice(Device):
    '''Provides functionalities for monitoring a device's data. For example,
    using a visualizer.
    '''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._monitor_in_q = None
        self._monitor_out_q = None

    def set_monitoring_queues(self, monitor_in_q: QueueType, monitor_out_q: QueueType) -> None:
        '''Set the queues for communicating with the parent process.
        It should be called before the start of the process.
        '''
        assert isinstance(monitor_in_q, QueueType)
        assert isinstance(monitor_out_q, QueueType)

        self._monitor_in_q = monitor_in_q
        self._monitor_out_q = monitor_out_q

    def run(self) -> None:
        # Ensuring queues are set.
        assert isinstance(self._monitor_in_q, QueueType)
        assert isinstance(self._monitor_out_q, QueueType)

        threading.Thread(target=self._monitor_loop,
                         name=self.__class__.__name__ + " monitor thread", daemon=True) \
            .start()

        self._run()

    def _monitor_loop(self) -> None:
        while True:
            # We don't use the data from the queue. It's just a signal.
            self._monitor_in_q.get()

            try:
                # Only 10ms timeout, because we don't want to take cpu time from the
                # main thread (data collector)
                self._monitor_out_q.put(
                    pickle.dumps(
                        self._get_monitoring_data(),
                        protocol=pickle.HIGHEST_PROTOCOL),
                    timeout=0.01)

            except pickle.PickleError:
                print("Error pickling monitoring data", file=sys.stderr)
                traceback.print_exc()
                # We don't want to keep the parent process waiting
                self._monitor_out_q(pickle.dumps(
                    [], protocol=pickle.HIGHEST_PROTOCOL))

    def _get_monitoring_data(self) -> List[Any]:
        '''Subclasses must implmenet this method. It should return
        a list of latest collected records.
        This method will be called in a separate thread, and should
        be thread-safe.
        Also, implmentation must return as quick as possible, to prevent
        blocking of the main thread that doing the collecting.

        @param requested_records: Number of records that should be returned.
        @type requested_records: int

        @return: List of records, or empty list if there's nothing.
        @rtype: List[Any]
        '''
        raise NotImplementedError()
