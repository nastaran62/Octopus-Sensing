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

from typing import Tuple, Any, Optional
import os
import threading
import cv2
from octopus_sensing.devices.device import Device
from octopus_sensing.common.message_creators import MessageType
import time
import csv
import datetime


class CameraStreaming(Device):
    def __init__(self, camera_no: Optional[int] = None, camera_path: Optional[str] = None, image_width: int = 1280, image_height: int = 720, **kwargs):
        assert (camera_no is not None) ^ (camera_path is not None), \
            "Only one of camera_no or camera_path should have value"
        super().__init__(**kwargs)
        self.output_path = os.path.join(self.output_path, "video")
        os.makedirs(self.output_path, exist_ok=True)
        if camera_no is not None:
            self._camera_number = camera_no
        elif camera_path is not None:
            self._camera_number = int(os.path.realpath(camera_path))

        self._image_width = image_width
        self._image_height = image_height
        self._video_size: Tuple[int, int] = (self._image_width, self._image_height)
        self._video_capture: Any = None
        self._fps: int = 30
        self._capture_times: list = []
        self._counter = 0

    def _run(self):
        print("self._camera_number", self._camera_number)
        self._video_capture = cv2.VideoCapture(self._camera_number)
        try:
            self._video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, self._image_width)
            self._video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self._image_height)
        except Exception as error:
            # Ignoring all errors
            print("Could not set the camera resolution.")
            print(error)

        # There's no guarantee that we can set the camera resolution. So, we
        # re-read the settings again from the camera.
        self._fps = self._video_capture.get(cv2.CAP_PROP_FPS)
        self._video_size = (int(self._video_capture.get(cv2.CAP_PROP_FRAME_WIDTH)),
                            int(self._video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT)))
        self._video_capture.read()

        recording_thread = None
        recording_event = None

        print(f"Initialized video device [{self.name}]: {self._video_size} fps: {self._fps}")

        while True:
            message = self.message_queue.get()
            if message is None:
                continue
            if message.type == MessageType.START:
                self._capture_times = []
                if recording_thread is not None:
                    raise RuntimeError(
                        ("[{0} device] Received two start messages. "
                         "A STOP message should be send before trying "
                         "to start a new video recording.".format(self.name)))

                file_name = "{0}/{1}-{2}-{3}.avi".format(self.output_path,
                                                         self.name,
                                                         message.experiment_id,
                                                         str(message.stimulus_id).zfill(2))
                recording_event = threading.Event()
                recording_event.set()
                recording_thread = threading.Thread(
                    target=self._stream_loop, args=(file_name, recording_event), daemon=True)
                print("after thread", time.time())
                recording_thread.start()

            elif message.type == MessageType.STOP:
                self._save_frame_times(file_name)
                if recording_event is not None:
                    recording_event.clear()
                recording_thread = None
                recording_event = None

            elif message.type == MessageType.TERMINATE:
                if recording_event is not None:
                    recording_event.clear()
                recording_thread = None
                recording_event = None
                break

        print("video terminated")
        self._video_capture.release()

    def _stream_loop(self, file_name: str, event: threading.Event):
        coded = cv2.VideoWriter_fourcc(*'XVID')
        print(file_name, "frame_per_second", self._fps, "**********************")
        writer = cv2.VideoWriter(file_name,
                                 coded,
                                 self._fps,
                                 self._video_size)

        try:
            while self._video_capture.isOpened:
                if event.is_set():
                    ret, frame = self._video_capture.read()
                    if ret:
                        self._counter += 1
                        self._capture_times.append(datetime.datetime.now())
                        writer.write(frame)
                else:
                    writer.release()
                    break

        except Exception as error:
            print("Error while recording video. Device: {0}".format(self.name))
            print(error)

    def _stream_loop_image(self, file_name: str, event: threading.Event):
        try:
            while self._video_capture.isOpened:
                if event.is_set():
                    ret, frame = self._video_capture.read()
                    if ret:
                        a = time.time()
                        os.makedirs(file_name[:-4], exist_ok=True)
                        image_file_name = file_name[:-4] + "/" + str(a) + ".jpg"
                        print(image_file_name)
                        cv2.imwrite(image_file_name, frame)
                else:
                    break

        except Exception as error:
            print("Error while recording video. Device: {0}".format(self.name))
            print(error)

    def _save_frame_times(self, file_name):
        print(len(self._capture_times))
        csv_file_name = file_name[:-3] + "csv"
        with open(csv_file_name, 'a') as csv_file:
            for item in self._capture_times:
                writer = csv.writer(csv_file)
                writer.writerow([item])
                csv_file.flush()
