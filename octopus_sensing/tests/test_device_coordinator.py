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
# You should have received a copy of the GNU General Public License along with Foobar.
# If not, see <https://www.gnu.org/licenses/>.

import time
import pytest

from octopus_sensing.device_coordinator import MonitoringCache, DeviceCoordinator
from octopus_sensing.devices.device import Device


def test_monitoring_cache():
    cache = MonitoringCache()

    data = [1, 2, 3]

    cache.cache(data)

    time.sleep(0.06)
    assert cache.get_cache() == data

    time.sleep(0.05)
    assert cache.get_cache() is None


def test_should_auto_assign_device_id():
    test_device = Device()
    test_device._run = lambda: None
    coordinator = DeviceCoordinator()
    coordinator.add_device(test_device)
    assert isinstance(test_device.name, str)
    assert len(test_device.name) > 0


def test_should_not_add_duplicated_deivces():
    test_device = Device(name="device1")
    test_device._run = lambda: None
    coordinator = DeviceCoordinator()
    coordinator.add_device(test_device)
    with pytest.raises(RuntimeError):
        coordinator.add_device(test_device)
