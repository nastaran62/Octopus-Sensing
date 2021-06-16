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

import os
import os.path
import queue
import random
import time
import tempfile
import pickle
import struct
import http.client
import multiprocessing
import multiprocessing.dummy
import multiprocessing.queues

import pytest
import pyOpenBCI
import serial


class MockSample:
    def __init__(self, channels):
        self.channels_data = [round(random.uniform(
            0.01, 0.9), 5) for _ in range(channels)]
        self.aux_data = [round(random.uniform(0.01, 0.9), 5)
                         for _ in range(channels)]
        self.id = random.randrange(1, 200)


class MockedOpenBCICyton:
    def __init__(self, daisy=True):
        self._channels = 16
        if daisy is False:
            self._channels = 8

    def stop_stream(self):
        pass

    def start_stream(self, callback):
        # Four seconds of data
        for _ in range(4 * 128):
            callback(MockSample(self._channels))
            # Sample rate: 128 per second
            time.sleep(1 / 128)


class MockedSerial:
    def __init__(self, port, speed):
        pass

    def flushInput(self):
        pass

    def write(self, data):
        pass

    def close(self):
        pass

    def read(self, size):
        if size == 1:
            # Asking for ack
            return struct.pack('B', 0xff)
        elif size == 9:
            # Enquiry configurations
            # Only byte 7 (number of channels) and byte 8 (buffer size) is used by the app.
            return b"\x00\x00\x00\x00\x00\x00\x00\x05\xff"
        elif size == 5:
            # Channels
            return b"\x65\x66\x67\x68\x69"
        elif size == 14:
            # One frame of data
            frame = []
            for _ in range(14):
                # 48 to 57 are numbers 0 to 9
                frame.append(random.randint(48, 57))
            # Sample rate: 128 per second
            time.sleep(1 / 128)
            return bytes(frame)


@pytest.fixture(scope="module")
def mocked():
    # Preventing processes from creating a new process
    original_process = multiprocessing.Process
    multiprocessing.Process = multiprocessing.dummy.Process
    original_queue = multiprocessing.queues.Queue
    multiprocessing.queues.Queue = queue.Queue
    original_queue_method = multiprocessing.Queue
    multiprocessing.Queue = queue.Queue

    original_openbcicyton = pyOpenBCI.OpenBCICyton
    pyOpenBCI.OpenBCICyton = MockedOpenBCICyton

    original_serial = serial.Serial
    serial.Serial = MockedSerial

    yield None

    multiprocessing.Process = original_process
    multiprocessing.queues.Queue = original_queue
    multiprocessing.Queue = original_queue_method
    pyOpenBCI.OpenBCICyton = original_openbcicyton
    serial.Serial = original_serial


def test_system_health(mocked):
    '''Runs the whole system to roughly check everything is working together.'''
    # To ensure mocks are applied, we import these modules here.
    import octopus_sensing.devices.openbci.openbci_streaming as openbci_streaming
    import octopus_sensing.devices.shimmer3.shimmer3_streaming as shimmer3_streaming
    from octopus_sensing.device_coordinator import DeviceCoordinator
    from octopus_sensing.common.message_creators import start_message, stop_message, terminate_message
    from octopus_sensing.monitoring_endpoint import MonitoringEndpoint

    output_dir = tempfile.mkdtemp(prefix="octopus-sensing-test")

    coordinator = DeviceCoordinator()

    openbci = openbci_streaming.OpenBCIStreaming(
        name="eeg", output_path=output_dir)
    coordinator.add_device(openbci)

    shimmer = shimmer3_streaming.Shimmer3Streaming(
        name="shimmer", output_path=output_dir)
    coordinator.add_device(shimmer)

    monitoring_endpoint = MonitoringEndpoint(coordinator)
    monitoring_endpoint.start()

    try:
        coordinator.dispatch(start_message("int_test", "stimulus_1"))
        # Allowing data collection for five seconds
        time.sleep(5)
        coordinator.dispatch(stop_message("int_test", "stimulus_1"))

        http_client = http.client.HTTPConnection("127.0.0.1:9330")
        http_client.request("GET", "/")
        response = http_client.getresponse()
        assert response.status == 200
        monitoring_data = pickle.loads(response.read())
        assert isinstance(monitoring_data, dict)

        assert isinstance(monitoring_data["eeg"], list)
        # three seconds * data rate
        assert len(monitoring_data["eeg"]) == 3 * 128
        assert len(monitoring_data["eeg"][0]) in (34, 35)
        assert len(monitoring_data["eeg"][-1]) in (34, 35)

        assert isinstance(monitoring_data["shimmer"], list)
        assert len(monitoring_data["shimmer"]) == 3 * 128
        assert len(monitoring_data["shimmer"][0]) in (8, 9)
        assert len(monitoring_data["shimmer"][-1]) in (8, 9)

    finally:
        coordinator.dispatch(terminate_message())
        monitoring_endpoint.stop()

    # To ensure termination is happened.
    time.sleep(0.5)

    eeg_output = os.path.join(output_dir, "eeg")
    assert os.path.exists(eeg_output)
    assert len(os.listdir(eeg_output)) == 1
    assert os.listdir(eeg_output)[0] == "eeg-int_test.csv"

    shimmer_output = os.path.join(output_dir, "shimmer")
    assert os.path.exists(shimmer_output)
    assert len(os.listdir(shimmer_output)) == 1
    assert os.listdir(shimmer_output)[0] == "shimmer-int_test.csv"
