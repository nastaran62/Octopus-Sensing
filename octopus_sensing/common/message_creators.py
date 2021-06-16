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

from typing import Optional, Any

from octopus_sensing.common.message import Message


class MessageType():
    START = "START"
    STOP = "STOP"
    TERMINATE = "TERMINATE"


def start_message(experiment_id: str, stimulus_id: str, payload=None):
    '''
    Creates a message to inform device of starting the stimulus

    @param str experiment_id: experiment ID
    @param int stimulus_id: stimulus ID

    @kwargs payload: Some meta data related to starting the stimulus

    @rtype: Message
    @return: a start message
    '''
    return Message(MessageType.START,
                   payload,
                   experiment_id=experiment_id,
                   stimulus_id=stimulus_id)


def stop_message(experiment_id: str, stimulus_id: str):
    '''
    Creates a message to inform device of stopping the stimulus

    @param str experiment_id: experiment ID
    @param int stimulus_id: stimulus ID

    @rtype: Message
    @return: a stop message
    '''
    return Message(MessageType.STOP,
                   None,
                   experiment_id=experiment_id,
                   stimulus_id=stimulus_id)


def terminate_message():
    '''
    Creates a message to inform device of terminating the program

    @rtype: Message
    @return: a terminate message
    '''
    return Message(MessageType.TERMINATE,
                   None)
