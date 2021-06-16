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

import socket
import time
from octopus_sensing.devices.device import Device

HOST = '127.0.0.1'
PORT = 15361

# transform a value into an array of byte values in little-endian order.
class OpenVibeStreaming(Device):
    def __init__(self):
        super().__init__()
        # connect
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.connect((HOST, PORT))

    def run(self):
        while True:
            message = self.message_queue.get()
            if message is not None:
                self.subject_id = message.subject_id
                self.stimulus_id = message.stimulus_id
            if message is None:
                continue
            elif message.type == "terminate":
                break
            else:
                print("Send trigger")
                self._send_trigger(message.payload["trigger"])
        self._socket.close()

    def _send_trigger(self, event_id):
        # create the three pieces of the tag, padding, event_id and timestamp
        padding=[0]*8

        # transform the value into an array of byte values in little-endian order
        event_id = list(event_id.to_bytes(8, byteorder='little'))

        # timestamp can be either the posix time in ms, or 0 to let the acquisition server timestamp the tag itself.
        t = int(time.time()*1000)
        timestamp = list(t.to_bytes(8, byteorder='little'))

        self._socket.sendall(bytearray(padding+event_id+timestamp))
