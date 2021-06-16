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
import pathlib
from octopus_sensing.device_coordinator import DeviceCoordinator
from octopus_sensing.devices.openbci.openbci_streaming import OpenBCIStreaming
from octopus_sensing.devices.shimmer3.shimmer3_streaming import Shimmer3Streaming
from octopus_sensing.preprocessing.openbci import openbci_preprocess
from octopus_sensing.preprocessing.shimmer3 import shimmer3_preprocess


def preprocess_devices(device_coordinator: DeviceCoordinator, output_path: str,
                       openbci_sampling_rate: int = 128,
                       shimmer3_sampling_rate: int = 128,
                       signal_preprocess: bool = True):
    '''
    Preprocees recorded files for all devices that are added to device_coordinator,
    Some devices do not have any preprocessing, so this function will ignore them

    @param DeviceCoordinator device_coordinator: an instance of DeviceCoordinator
    @param str output_path: Path for preprocessed Files
    @param int openbci_sampling_rate: New sampling rate for openbci resampling
    @param int shimmer3_sampling_rate: New sampling rate for shimmer3 resampling
    '''
    print("Start preprocessing ....")
    devices = device_coordinator.get_devices()
    for device in devices:
        if isinstance(device, OpenBCIStreaming):
            device_output_path = os.path.join(output_path, device.get_name())
            print("device_output_path", device_output_path)
            if not os.path.exists(device_output_path):
                pathlib.Path(device_output_path).mkdir(parents=True, exist_ok=True)

            # This is the path that device saves recording data
            input_path = device.get_output_path()
            print("input_path", input_path)
            file_names = os.listdir(input_path)
            file_names.sort()
            if not os.path.exists(device_output_path):
                os.mkdir(device_output_path)
            for file_name in file_names:
                openbci_preprocess(input_path, file_name, device_output_path,
                                   device.get_channels(),
                                   saving_mode=device.get_saving_mode(),
                                   sampling_rate=openbci_sampling_rate,
                                   signal_preprocess=signal_preprocess)
        elif isinstance(device, Shimmer3Streaming):
            device_output_path = os.path.join(output_path, device.get_name())
            if not os.path.exists(device_output_path):
                pathlib.Path(device_output_path).mkdir(parents=True, exist_ok=True)

            # This is the path that device saves recording data

            input_path = device.get_output_path()
            file_names = os.listdir(input_path)
            file_names.sort()
            print("preprocess shimmer input_path", input_path)
            print("preprocess shimmer device_output_path", device_output_path)
            for file_name in file_names:
                shimmer3_preprocess(input_path, file_name, device_output_path,
                                    saving_mode=device.get_saving_mode(),
                                    sampling_rate=shimmer3_sampling_rate,
                                    signal_preprocess=signal_preprocess)
    print("Preprocessing done")
