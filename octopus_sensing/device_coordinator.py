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
import time
import traceback
import multiprocessing
import queue
import pickle
from typing import List, Any, Tuple, Dict

from octopus_sensing.devices.device import Device
from octopus_sensing.devices.monitored_device import MonitoredDevice
from octopus_sensing.common.message import Message
from octopus_sensing.common.message_creators import terminate_message

QueueType = multiprocessing.queues.Queue


class MonitoringCache:
    def __init__(self):
        self._time = time.time_ns()
        self._cached_data = []

    def get_cache(self):
        '''Returns None if cache is not available or expired'''
        # 100 ms
        if time.time_ns() - self._time > 100000000:
            return None
        return self._cached_data

    def cache(self, data: List[Any]):
        self._cached_data = data
        self._time = time.time_ns()


class DeviceCoordinator:
    '''
    Coordinating devices
    '''

    def __init__(self):
        self.__devices = {}
        self.__queues: List[QueueType] = []
        self.__device_counter: int = 0
        self.__monitoring_queues: List[Tuple[QueueType, QueueType, Device]] = [
        ]
        self.__monitoring_cache = MonitoringCache()

    def __get_device_id(self) -> str:
        '''
        Generate an ID for devices that do not have name

        @rtype: str
        @return device_id
        '''
        self.__device_counter += 1
        device_id = "device_{0}".format(self.__device_counter)
        return device_id

    def get_devices(self) -> List[Device]:
        '''
        Return a list of added devices

        @rtype: list(device)
        @return a list of added devices
        '''
        return list(self.__devices.values())

    def add_device(self, device: Device) -> None:
        '''
        Adds new device to the coordinator and starts it

        @param Device device: a device object

        @keyword str name: The name of device
        '''
        assert isinstance(device, Device)

        if device.name is None:
            device.name = self.__get_device_id()
        if device.name in self.__devices.keys():
            raise RuntimeError("This device already has been added")

        self.__devices[device.name] = device
        msg_queue: QueueType = multiprocessing.Queue()
        device.set_queue(msg_queue)
        self.__queues.append(msg_queue)

        self.__set_monitoring_queues(device)

        device.start()

    def add_devices(self, devices: List[Device]) -> None:
        '''
        Adds new devices to the coordinator

        @param list devices: a list of device object
        @type devices: list(Device)
        '''
        for device in devices:
            self.add_device(device)

    def dispatch(self, message: Message) -> None:
        '''
        dispatch new message to all devices

        @param Message message: a message object object
        '''
        for message_queue in self.__queues:
            message_queue.put(message)

    def terminate(self):
        self.dispatch(terminate_message())
        for item in self.__devices.values():
            item.join()

    def get_monitoring_data(self) -> Dict[str, List[Any]]:
        '''
        Returns latest collected data from all devices.
        Device's data can be anything, depending on the device itself.

        @return: Dict of device name to the collected data.
        @rtype: Dict[device_name, List[Any]]
        '''
        cached = self.__monitoring_cache.get_cache()
        if cached:
            return cached

        # Putting request for all devices, then collecting them all, for performance reasons.
        for in_q, _, device in self.__monitoring_queues:
            try:
                # The sub-process won't use the data we put in the queue. It's just a signal.
                in_q.put(b'0', timeout=0.1)
            except queue.Full:
                print("Could not put monitoring request for {0} device.".format(
                    device.name), file=sys.stderr)
                traceback.print_exc()

        result = {}
        for _, out_q, device in self.__monitoring_queues:
            try:
                records = pickle.loads(out_q.get(timeout=0.1))
                # We ensured device has a name in the add_device, ignoring it here.
                result[device.name] = records  # type: ignore
            except (queue.Empty, pickle.PickleError):
                print("Could not read monitoring data from {0} device".format(
                    device.name), file=sys.stderr)
                traceback.print_exc()

        self.__monitoring_cache.cache(result)
        return result

    def __set_monitoring_queues(self, device: Device) -> None:
        if isinstance(device, MonitoredDevice):
            in_q: QueueType = multiprocessing.Queue()
            out_q: QueueType = multiprocessing.Queue()
            device.set_monitoring_queues(in_q, out_q)
            self.__monitoring_queues.append((in_q, out_q, device))
