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
Anki/DDL Vector - Python SDK with Audio Streaming:
    Fork with real-time microphone audio streaming via wirepod

## With support for Production, wire-pod and OSKR robots! ##
This fork extends the wirepod Vector Python SDK with real-time audio
streaming capabilities via wirepod's websocket API.

NEW FEATURES:
    * Real-time microphone audio streaming from Vector
    * AudioStreamClient for websocket-based audio capture
    * Trigger Vector to listen without "Hey Vector" wake word
    * Save audio recordings as WAV files

REQUIREMENTS:
    * A modified wirepod server with audio streaming support
    * websockets library (automatically installed)

The Vector SDK gives you direct access to Vector's unprecedented set of
advanced sensors, AI capabilities, and robotics technologies including
computer vision, intelligent mapping and navigation, and a groundbreaking
collection of expressive animations.

Requirements:
    * Python 3.7+
    * wirepod server with audio streaming enabled
"""

import os.path
import sys
from setuptools import setup

if sys.version_info < (3, 6, 1):
    sys.exit('The Vector SDK requires Python 3.6.1 or later')

HERE = os.path.abspath(os.path.dirname(__file__))

def fetch_version():
    """Get the version from the package"""
    with open(os.path.join(HERE, 'anki_vector', 'version.py')) as version_file:
        versions = {}
        exec(version_file.read(), versions)
        return versions

VERSION_DATA = fetch_version()
VERSION = VERSION_DATA['__version__']

def get_requirements():
    """Load the requirements from requirements.txt into a list"""
    reqs = []
    with open(os.path.join(HERE, 'requirements.txt')) as requirements_file:
        for line in requirements_file:
            reqs.append(line.strip())
    return reqs

setup(
    name='wirepod_vector_sdk_audio',
    version=VERSION,
    description="Vector SDK with real-time audio streaming support via wirepod websocket API.",
    long_description=__doc__,
    url='https://github.com/kercre123/wirepod-vector-python-sdk',
    author='Anki, Inc',
    author_email='developer@anki.com',
    license='Apache License, Version 2.0',
    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
    ],
    zip_safe=True,
    keywords='anki wire pod wire-pod vector robot robotics sdk ai vision audio streaming microphone'.split(),
    packages=['anki_vector', 'anki_vector.camera_viewer', 'anki_vector.configure', 'anki_vector.messaging', 'anki_vector.opengl', 'anki_vector.reserve_control'],
    package_data={
        'anki_vector': ['LICENSE.txt', 'opengl/assets/*.obj', 'opengl/assets/*.mtl', 'opengl/assets/*.jpg',
                  'opengl/assets/LICENSE.txt']
    },
    install_requires=get_requirements(),
    extras_require={
        '3dviewer': ['PyOpenGL>=3.1'],
        'docs': ['sphinx', 'sphinx_rtd_theme', 'sphinx_autodoc_typehints'],
        'experimental': ['keras', 'scikit-learn', 'scipy', 'tensorflow'],
        'test': ['pytest', 'requests', 'requests_toolbelt'],
    }
)
