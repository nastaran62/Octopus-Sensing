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
import threading
import datetime
import csv
import math
import struct
import serial
from octopus_sensing.devices.monitored_device import MonitoredDevice
from octopus_sensing.common.message_creators import MessageType
from octopus_sensing.devices.common import SavingModeEnum


class Shimmer3Streaming(MonitoredDevice):
    '''
    Manages Shimmer3 streaming
    '''

    def __init__(self, saving_mode=SavingModeEnum.CONTINIOUS_SAVING_MODE, **kwargs):
        super().__init__(**kwargs)

        self._saving_mode = saving_mode
        self._stream_data = []
        self._inintialize_connection()
        self._trigger = None
        self._break_loop = False
        self.output_path = self._make_output_path()

    def _make_output_path(self):
        output_path = os.path.join(self.output_path, "shimmer")
        os.makedirs(output_path, exist_ok=True)
        return output_path

    def _inintialize_connection(self):
        '''
        Initializing connection with Simmer3 device
        '''
        self._serial = serial.Serial("/dev/rfcomm0", 115200)
        self._serial.flushInput()
        print("port opening, done.")
        # send the set sensors command
        # 4 bytes command:
        #     0x08 is SET_SENSORS_COMMAND
        #     Each bit in the three following bytes are one sensor.
        self._serial.write(struct.pack(
            'BBBB', 0x08, 0x84, 0x01, 0x00))  # GSR and PPG
        self._wait_for_ack()
        print("sensor setting, done.")

        # Enable the internal expansion board power
        self._serial.write(struct.pack('BB', 0x5E, 0x01))
        self._wait_for_ack()
        print("enable internal expansion board power, done.")

        # send the set sampling rate command

        '''
        sampling_freq = 32768 / clock_wait = X Hz
        2 << 14 = 32768
        '''
        sampling_freq = 128
        clock_wait = math.ceil((2 << 14) / sampling_freq)

        self._serial.write(struct.pack('<BH', 0x05, clock_wait))
        self._wait_for_ack()

        # Inquiry configurations (For finding channels order)
        # Page 16 of This PDF:
        # http://www.shimmersensing.com/images/uploads/docs/LogAndStream_for_Shimmer3_Firmware_User_Manual_rev0.11a.pdf

        self._serial.write(struct.pack('B', 0x01))
        self._wait_for_ack()
        inquiery_response = bytes("", 'utf-8')
        # response_size is 1 packet_type + 2 Sampling rate + 4 Config Bytes +
        # 1 Num Channels + 1 Buffer size
        response_size = 9
        numbytes = 0
        while numbytes < response_size:
            inquiery_response += self._serial.read(response_size)
            numbytes = len(inquiery_response)

        num_channels = inquiery_response[7]
        print("Number of Channels:", num_channels)
        print("Buffer size:", inquiery_response[8])

        # There's one byte for each channel
        # For the meaning of each byte, refer to the above PDF
        channels = bytes("", "utf-8")
        numbytes = 0
        while numbytes < num_channels:
            channels += self._serial.read(num_channels)
            numbytes = len(channels)

        print("Channel 1:", channels[0])
        print("Channel 2:", channels[1])
        print("Channel 3:", channels[2])
        print("Channel 4:", channels[3])
        print("Channel 5:", channels[4])

        # send start streaming command
        self._serial.write(struct.pack('B', 0x07))
        self._wait_for_ack()
        print("start command sending, done.")

    def _wait_for_ack(self):
        ddata = ""
        ack = struct.pack('B', 0xff)
        while ddata != ack:
            ddata = self._serial.read(1)

    def _run(self):
        '''
        Listening to the message queue and manage messages
        '''
        loop_thread = threading.Thread(target=self._stream_loop)
        loop_thread.start()

        while True:
            message = self.message_queue.get()
            if message is None:
                continue
            if message.type == MessageType.START:
                print("Shimmer start")
                self._experiment_id = message.experiment_id
                self.__set_trigger(message)
            elif message.type == MessageType.STOP:
                if self._saving_mode == SavingModeEnum.SEPARATED_SAVING_MODE:
                    self._experiment_id = message.experiment_id
                    file_name = \
                        "{0}/{1}-{2}-{3}.csv".format(self.output_path,
                                                     self.name,
                                                     self._experiment_id,
                                                     message.stimulus_id)
                    self._save_to_file(file_name)
                else:
                    print("Shimmer stop")
                    self._experiment_id = message.experiment_id
                    self.__set_trigger(message)
            elif message.type == MessageType.TERMINATE:
                if self._saving_mode == SavingModeEnum.CONTINIOUS_SAVING_MODE:
                    file_name = \
                        "{0}/{1}-{2}.csv".format(self.output_path,
                                                 self.name,
                                                 self._experiment_id)
                    self._save_to_file(file_name)
                break

        self._break_loop = True
        loop_thread.join()

    def __set_trigger(self, message):
        '''
        Takes a message and set the trigger using its data

        @param Message message: a message object
        '''
        self._trigger = \
            "{0}-{1}-{2}".format(message.type,
                                 message.experiment_id,
                                 str(message.stimulus_id).zfill(2))

    def _stream_loop(self):
        '''
        Reads incoming data
        '''
        ddata = bytes("", 'utf-8')
        numbytes = 0
        # 1byte packet type + 3byte timestamp + 2 byte X + 2 byte Y +
        # 2 byte Z + 2 byte PPG + 2 byte GSR
        framesize = 14

        try:
            while True:
                while numbytes < framesize:
                    ddata += self._serial.read(framesize)
                    numbytes = len(ddata)
                    if self._break_loop:
                        break

                if self._break_loop:
                    self._stop_shimmer()
                    break

                data = ddata[0:framesize]
                ddata = ddata[framesize:]
                numbytes = len(ddata)

                # read basic packet information
                (packettype) = struct.unpack('B', data[0:1])
                (timestamp0, timestamp1, timestamp2) = \
                    struct.unpack('BBB', data[1:4])

                # read packet payload
                (x, y, z, PPG_raw, GSR_raw) = \
                    struct.unpack('HHHHH', data[4:framesize])
                record_time = datetime.datetime.now()

                # get current GSR range resistor value
                data_range = ((GSR_raw >> 14) & 0xff)  # upper two bits
                if data_range == 0:
                    rf = 40.2   # kohm
                elif data_range == 1:
                    rf = 287.0  # kohm
                elif data_range == 2:
                    rf = 1000.0  # kohm
                elif data_range == 3:
                    rf = 3300.0  # kohm

                # convert GSR to kohm value
                gsr_to_volts = (GSR_raw & 0x3fff) * (3.0/4095.0)
                GSR_ohm = rf/((gsr_to_volts / 0.5) - 1.0)

                # convert PPG to milliVolt value
                PPG_mv = PPG_raw * (3000.0/4095.0)

                timestamp = timestamp0 + timestamp1*256 + timestamp2*65536

                #print([packettype[0], timestamp, GSR_ohm, PPG_mv] + self._trigger)

                if self._trigger is not None:
                    print("Shimmer trigger")
                    row = [packettype[0],
                           timestamp,
                           x, y, z,
                           GSR_ohm,
                           PPG_mv,
                           record_time,
                           self._trigger]
                    self._trigger = None
                else:
                    row = [packettype[0],
                           timestamp,
                           x, y, z,
                           GSR_ohm,
                           PPG_mv,
                           record_time]
                self._stream_data.append(row)

        except KeyboardInterrupt:
            self._stop_shimmer()

    def _stop_shimmer(self):
        # send stop streaming command
        self._serial.write(struct.pack('B', 0x20))

        print("stop command sent, waiting for ACK_COMMAND")
        self._wait_for_ack()
        print("ACK_COMMAND received.")
        self._serial.close()
        print("All done")

    def _save_to_file(self, file_name):
        if not os.path.exists(file_name):
            csv_file = open(file_name, 'a')
            header = ["type", "time stamp", "Acc_x", "Acc_y", "Acc_z",
                      "GSR_ohm",
                      "PPG_mv",
                      "time",
                      "trigger"]
            writer = csv.writer(csv_file)
            writer.writerow(header)
            csv_file.flush()
            csv_file.close()

        with open(file_name, 'a') as csv_file:
            writer = csv.writer(csv_file)
            for row in self._stream_data:
                writer.writerow(row)
                csv_file.flush()

    def _get_monitoring_data(self):
        '''Returns latest collected data for monitoring/visualizing purposes.'''
        # Last three seconds
        # FIXME: hard-coded data collection rate
        return self._stream_data[-1 * 3 * 128:]

    def get_saving_mode(self):
        return self._saving_mode

    def get_output_path(self):
        return self.output_path
