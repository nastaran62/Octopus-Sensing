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

from typing import Optional, Any


class Message():
    '''
    Message class
    '''

    def __init__(self, message_type: str, payload: Any,
                 experiment_id: Optional[str] = None,
                 stimulus_id: Optional[str] = None):
        '''
        Initializes the message object

        @param str type: The type of message
        @param payload: the message data that can have differnt values

        @keyword str experiment_id: experiment's ID
        @keyword str stimulus_id: stimulus's ID
        '''
        self.type = message_type
        self.payload = payload
        self.experiment_id = experiment_id
        self.stimulus_id = stimulus_id
