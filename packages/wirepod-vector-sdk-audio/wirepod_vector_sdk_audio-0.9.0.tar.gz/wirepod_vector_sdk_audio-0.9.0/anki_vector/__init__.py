# Copyright (c) 2018 Anki, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License in the file LICENSE.txt or at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
SDK for programming with the Anki Vector robot.

This fork includes audio streaming support via wirepod's websocket API.
"""

import sys
import logging

from . import messaging
from .robot import Robot, AsyncRobot
from .version import __version__
from .audio_stream import AudioStreamClient, AudioStreamError, check_wirepod_audio_support

logger = logging.getLogger('vector')  # pylint: disable=invalid-name

if sys.version_info < (3, 6, 1):
    sys.exit('anki_vector requires Python 3.6.1 or later')

__all__ = [
    'Robot',
    'AsyncRobot',
    'AudioStreamClient',
    'AudioStreamError',
    'check_wirepod_audio_support',
    'logger',
    'messaging',
    '__version__'
]
