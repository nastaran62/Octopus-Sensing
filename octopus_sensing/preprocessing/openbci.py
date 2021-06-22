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
from typing import List, Optional
import pandas as pd
import numpy as np
import mne

from octopus_sensing.preprocessing.utils import load_all_trials, resample, load_all_samples
from octopus_sensing.devices.common import SavingModeEnum


def openbci_preprocess(input_path: str, file_name: str, output_path: str,
                       channels: List[str],
                       saving_mode: int = SavingModeEnum.CONTINIOUS_SAVING_MODE,
                       sampling_rate: int = 128,
                       signal_preprocess: bool = True):
    '''
    Split openbci recorded files based on markers and resample data to a
    constant sampling rate

    @param str input_path: openbci input file path
    @param str file_name: openbci input file name
    @param str output_path: preprocessed file path
    @param list channels: a list of recorded channels
    @type channels: list(str)
    @keyword int sampling_rate : The desired sampling_rate
    @note: Sometimes recorded data in one second with Openbci are less or more
           than the specified sampling rate. So, we resample data by replicating
           the last samples or removing some samples to achieve the desired sampling_rate
    '''
    if saving_mode == SavingModeEnum.SEPARATED_SAVING_MODE:
        if len(channels) == 8:
            data, times = \
                load_all_samples(os.path.join(input_path, file_name),
                                 (0, 8),  # channel columns
                                 12,
                                 '%H:%M:%S.%f')  # timestamp column

        elif len(channels) == 16:
            data, times = \
                load_all_samples(os.path.join(input_path, file_name),
                                 (0, 16),  # channel columns
                                 20,
                                 '%H:%M:%S.%f')  # timestamp column
        output_file_path = \
            "{0}/{1}".format(output_path, file_name)
        resampled_data = \
            resample(data, times, sampling_rate)
        if signal_preprocess is True:
            preprocessed_data = \
                clean_eeg(resampled_data,
                          channel_names=channels,
                          sampling_rate=sampling_rate)
        else:
            preprocessed_data = resampled_data
            # convert array into dataframe
        data_frame = pd.DataFrame(preprocessed_data, columns=channels)
        data_frame.to_csv(output_file_path, index=False)

    elif saving_mode == SavingModeEnum.CONTINIOUS_SAVING_MODE:
        if len(channels) == 8:
            trials_data, trials_times, triger_list = \
                load_all_trials(os.path.join(input_path, file_name),  # File path
                                (0, 8),  # channel columns
                                12,  # timestamp column
                                13,  # triger column
                                '%H:%M:%S.%f')  # timestamp format
        elif len(channels) == 16:
            trials_data, trials_times, triger_list = \
                load_all_trials(os.path.join(input_path, file_name),  # File path
                                (0, 16),  # channel columns
                                20,  # timestamp column
                                21,  # triger column
                                '%H:%M:%S.%f')  # timestamp format
        print("len trials ***************", len(trials_data))
        i = 0
        for trial in trials_data:
            output_file_path = \
                "{0}/{1}-{2}.csv".format(output_path,
                                         file_name[:-4],  # Removing .csv from file_name
                                         str(triger_list[i]).zfill(2))
            print("output_file_path", output_file_path)
            resampled_data = \
                resample(trial, trials_times[i], sampling_rate)

            if signal_preprocess is True:
                preprocessed_data = \
                    clean_eeg(resampled_data,
                              channel_names=channels,
                              sampling_rate=sampling_rate)
            else:
                preprocessed_data = resampled_data
                # convert array into dataframe
            data_frame = pd.DataFrame(preprocessed_data, columns=channels)

            # save the dataframe as a csv file
            data_frame.to_csv(output_file_path, index=False)
            i += 1
    else:
        raise Exception("Saving mode is incorrect")


class EegPreprocessing():
    def __init__(self, data, channel_names=None, sampling_rate=128):
        if channel_names is None:
            self._channel_names = \
                ["Fp1", "Fp2", "F7", "F3", "F4", "F8", "T3", "C3",
                 "C4", "T4", "T5", "P3", "P4", "T6", "O1", "O2"]
        else:
            self._channel_names = channel_names

        channel_data = np.transpose(data)/1e6
        channel_types = ["eeg"]*len(channel_names)

        self.__info = mne.create_info(channel_names,
                                      sampling_rate,
                                      channel_types)
        montage = mne.channels.make_standard_montage('standard_1020')
        self._mne_raw = mne.io.RawArray(channel_data, self.__info)
        self._mne_raw.set_montage(montage, match_case=False)
        self._mne_raw.load_data()

    def get_data(self):
        return self._mne_raw.get_data()

    def filter_data(self, low_frequency=1, high_frequency=45, notch_frequencies=[60]):
        '''
        Apply notch filter, low pass and high pass (bandpass) filter on mne data
        '''
        print("Apply filtering")
        # Band pass filter
        self._mne_raw.filter(l_freq=low_frequency, h_freq=high_frequency)
        # Notch filter
        if notch_frequencies not in (None, []):
            self._mne_raw.notch_filter(notch_frequencies)
        print("end filtering")


def clean_eeg(data, channel_names: List[str] = None,
              low_frequency: int = 1,
              high_frequency: int = 45,
              sampling_rate: Optional[int] = 128):
    if channel_names is None:
        channel_names = ["Fp1", "Fp2", "F7", "F3", "F4", "F8", "T3", "C3",
                         "C4", "T4", "T5", "P3", "P4", "T6", "O1", "O2"]

    # The length of data is 5 minutes
    preprocessing = \
        EegPreprocessing(data,
                         channel_names=channel_names,
                         sampling_rate=sampling_rate)
    preprocessing.filter_data(low_frequency=low_frequency, high_frequency=high_frequency)
    preprocessed_data = preprocessing.get_data()
    return np.transpose(preprocessed_data)
