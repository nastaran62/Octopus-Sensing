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

from octopus_sensing.devices.shimmer3_streaming import Shimmer3Streaming
from octopus_sensing.devices.openbci_streaming import OpenBCIStreaming
from octopus_sensing.devices.common import SavingModeEnum
from octopus_sensing.preprocessing.preprocess_devices import preprocess_devices
from octopus_sensing.device_coordinator import DeviceCoordinator

RECORDED_FILES_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                   "data/recorded")
print("RECORDED_FILES_PATH", RECORDED_FILES_PATH)


class MockedShimmer3Streaming(Shimmer3Streaming):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _run(self):
        pass

    def _inintialize_connection(self):
        pass

    def _make_output_path(self):
        return self.output_path


class MockedOpenBCIStreaming(OpenBCIStreaming):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _run(self):
        pass

    def _inintialize_board(self, daisy):
        return None

    def _make_output_path(self):
        return self.output_path


def test_preprocess_continuous_saving_mode():
    ch_names = ["Fp1", "Fp2", "F7", "F3", "F4", "F8", "T3", "C3",
                "C4", "T4", "T5", "P3", "P4", "T6", "O1", "O2"]
    openbci16 = \
        MockedOpenBCIStreaming(name="OpenBCI_16_continuous",
                               saving_mode=SavingModeEnum.CONTINIOUS_SAVING_MODE,
                               output_path=os.path.join(
                                   RECORDED_FILES_PATH, "OpenBCI_16_continuous"),
                               channels_order=ch_names)
    ch_names = ["Fp1", "Fp2", "F7", "F3", "F4", "F8", "T3", "C3"]
    openbci8 = \
        MockedOpenBCIStreaming(name="OpenBCI_8_continuous",
                               saving_mode=SavingModeEnum.CONTINIOUS_SAVING_MODE,
                               output_path=os.path.join(
                                   RECORDED_FILES_PATH, "OpenBCI_8_continuous"),
                               channels_order=ch_names,
                               daisy=False)

    shimmer = \
        MockedShimmer3Streaming(name="Shimmer_continuous",
                                saving_mode=SavingModeEnum.CONTINIOUS_SAVING_MODE,
                                output_path=os.path.join(RECORDED_FILES_PATH, "Shimmer_continuous"))

    device_coordinator = DeviceCoordinator()
    device_coordinator.add_devices([openbci16, openbci8, shimmer])

    preprocess_file_path = "/tmp/preprocess"

    preprocess_devices(device_coordinator, preprocess_file_path,
                       openbci_sampling_rate=6,
                       shimmer3_sampling_rate=6,
                       signal_preprocess=False)

    expected_openbci16_path = \
        os.path.join(os.path.dirname(os.path.realpath(__file__)),
                     "data/preprocess_expected/OpenBCI_16_continuous")
    preprocess_openbci16_path = "/tmp/preprocess/OpenBCI_16_continuous"
    check_files(preprocess_openbci16_path, expected_openbci16_path)

    expected_openbci8_path = \
        os.path.join(os.path.dirname(os.path.realpath(__file__)),
                     "data/preprocess_expected/OpenBCI_8_continuous")
    preprocess_openbci8_path = "/tmp/preprocess/OpenBCI_8_continuous"
    check_files(preprocess_openbci8_path, expected_openbci8_path)

    expected_shimmer_path = \
        os.path.join(os.path.dirname(os.path.realpath(__file__)),
                     "data/preprocess_expected/Shimmer_continuous")
    preprocess_shimmer_path = "/tmp/preprocess/Shimmer_continuous"
    check_files(preprocess_shimmer_path, expected_shimmer_path)


def test_preprocess_seperated_saving_mode():
    ch_names = ["Fp1", "Fp2", "F7", "F3", "F4", "F8", "T3", "C3",
                "C4", "T4", "T5", "P3", "P4", "T6", "O1", "O2"]
    openbci16 = \
        MockedOpenBCIStreaming(name="OpenBCI_16_sep",
                               saving_mode=SavingModeEnum.SEPARATED_SAVING_MODE,
                               output_path=os.path.join(
                                   RECORDED_FILES_PATH, "OpenBCI_16_sep"),
                               channels_order=ch_names)
    ch_names = ["Fp1", "Fp2", "F7", "F3", "F4", "F8", "T3", "C3"]
    openbci8 = \
        MockedOpenBCIStreaming(name="OpenBCI_8_sep",
                               saving_mode=SavingModeEnum.SEPARATED_SAVING_MODE,
                               output_path=os.path.join(
                                   RECORDED_FILES_PATH, "OpenBCI_8_sep"),
                               channels_order=ch_names,
                               daisy=False)
    shimmer = \
        MockedShimmer3Streaming(name="Shimmer_sep",
                                saving_mode=SavingModeEnum.SEPARATED_SAVING_MODE,
                                output_path=os.path.join(RECORDED_FILES_PATH, "Shimmer_sep"))

    device_coordinator = DeviceCoordinator()
    device_coordinator.add_devices([openbci16, openbci8, shimmer])

    preprocess_file_path = "/tmp/preprocess"
    preprocess_devices(device_coordinator, preprocess_file_path,
                       openbci_sampling_rate=6,
                       shimmer3_sampling_rate=6,
                       signal_preprocess=False)

    expected_openbci16_path = \
        os.path.join(os.path.dirname(os.path.realpath(__file__)),
                     "data/preprocess_expected/OpenBCI_16_sep")
    preprocess_openbci16_path = "/tmp/preprocess/OpenBCI_16_sep"
    check_files(preprocess_openbci16_path, expected_openbci16_path)

    expected_openbci8_path = \
        os.path.join(os.path.dirname(os.path.realpath(__file__)),
                     "data/preprocess_expected/OpenBCI_8_sep")
    preprocess_openbci8_path = "/tmp/preprocess/OpenBCI_8_sep"
    check_files(preprocess_openbci8_path, expected_openbci8_path)

    expected_shimmer_path = \
        os.path.join(os.path.dirname(os.path.realpath(__file__)),
                     "data/preprocess_expected/Shimmer_sep")
    preprocess_shimmer_path = "/tmp/preprocess/Shimmer_sep"
    check_files(preprocess_shimmer_path, expected_shimmer_path)


def check_files(preprocess_path, expected_path):
    expected_files = os.listdir(expected_path)
    preprocess_files = os.listdir(preprocess_path)
    assert len(preprocess_files) == len(expected_files)

    expected_files.sort()
    preprocess_files.sort()
    i = 0
    for file in preprocess_files:
        # Compare file name
        assert file == expected_files[i]

        # Compare file content
        preprocess_file = open(os.path.join(preprocess_path, file), 'r')
        expected_file = open(os.path.join(expected_path, file), 'r')
        file_one = preprocess_file.readlines()
        file_two = expected_file.readlines()
        preprocess_file.close()
        expected_file.close()
        j = 0
        for line in file_one:
            assert line == file_two[j]
            j += 1

        i += 1
