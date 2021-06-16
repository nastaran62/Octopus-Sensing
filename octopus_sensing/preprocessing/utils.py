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

import datetime
import csv
import numpy as np


def load_all_samples(file_path, channels_cols, time_stamp_col, time_format):
    data = []
    times = []
    with open(file_path, 'r') as file:
        reader = csv.reader(file, delimiter=',')
        i = 0
        for row in reader:
            if i == 0:
                # Skip header line
                i += 1
                continue
            data.append(np.array(row[channels_cols[0]:channels_cols[1]], dtype=np.float32))
            times.append(row[time_stamp_col])
    converted_times = str_to_times(times, time_format)
    return data, converted_times


def load_all_trials(file_path, channels_cols, time_stamp_col, triger_col, time_format):
    '''
    '''
    all_trials_data = []
    all_trials_times = []
    trial_numbers = []

    action_flag = None
    data = []
    times = []
    with open(file_path, 'r') as file:
        reader = csv.reader(file, delimiter=',')

        for i, row in enumerate(reader):
            if i == 0:
                # Ignore header
                continue
            if len(row) > triger_col:
                if row[triger_col] not in (None, ''):
                    triger = row[triger_col]
                    action = triger[0:4]
                    trial_number = int(triger[-2:])
                    if action == "STAR":
                        action_flag = 1
                    elif action == "STOP":
                        action_flag = 0
                        all_trials_data.append(data)
                        converted_times = str_to_times(times, time_format)
                        all_trials_times.append(converted_times)
                        trial_numbers.append(trial_number)
                        data = []
                        times = []
            if action_flag == 1:
                data.append(np.array(row[channels_cols[0]:channels_cols[1]], dtype=np.float32))
                times.append(row[time_stamp_col])
    return all_trials_data, all_trials_times, trial_numbers


def str_to_times(times, time_format):
    '''
    Convert a list of str times to datetime
    '''
    converted_times = []
    for item in times:
        try:
            time = datetime.datetime.strptime(item, time_format)
        except:
            try:
                time = datetime.datetime.strptime(item, '%H:%M:%S')
            except:
                time = datetime.datetime.strptime(item, '%Y-%m-%d %H:%M:%S')
        converted_times.append(time)
    return converted_times


def resample(data, times, sampling_rate):
    i = 0
    time_delta = datetime.timedelta(0, 1, 0)
    start_time = times[0]
    sample_start_time = start_time
    block = []
    all_data = []
    j = 0
    block_number = 0
    for item in data:
        if times[i] - sample_start_time > time_delta:
            block_number += 1
            if len(block) < sampling_rate:
                while len(block) < sampling_rate:
                    # repeating last item
                    block.extend(block[-(sampling_rate-len(block)):])
            elif len(block) > sampling_rate:
                # Ignoring last items
                block = block[:sampling_rate]
            all_data.extend(block)
            block = []
            sample_start_time = start_time + (block_number * time_delta)
        block.append(item)
        i += 1
    if len(block) > 0:
        if len(block) > sampling_rate/2:
            while len(block) < sampling_rate:
                # repeating last item
                block.extend(block[-(sampling_rate-len(block)):])
            block_number += 1
            all_data.extend(block)
    return np.array(all_data)
