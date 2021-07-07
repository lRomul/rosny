import argparse
from ctypes import c_uint8
from multiprocessing import Queue, Array, Lock

import cv2  # type: ignore
import mediapipe  # type: ignore
import numpy as np  # type: ignore

from rosny import ProcessStream, ComposeStream

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--input", default=0,
                    help="Source of video. Defaults to webcam.")
args = parser.parse_args()


def get_video_params(source):
    video = cv2.VideoCapture(source)
    width = video.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = video.get(cv2.CAP_PROP_FRAME_HEIGHT)
    fps = video.get(cv2.CAP_PROP_FPS)
    video.release()
    frame_size = int(height), int(width), 3
    return frame_size, fps


class NumpyArray:
    """NumPy array on shared memory"""
    def __init__(self, shape: tuple, ctype=c_uint8):
        self.shape = tuple(shape)
        self.lock = Lock()
        self.array = Array(ctype, int(np.prod(self.shape)))
        self.np_array = np.frombuffer(self.array.get_obj(), dtype=ctype)
        self.np_array = self.np_array.reshape(self.shape)

    @property
    def value(self) -> np.ndarray:
        with self.lock:
            return self.np_array.copy()

    @value.setter
    def value(self, array: np.ndarray):
        with self.lock:
            self.np_array[:] = array


class VideoStream(ProcessStream):
    def __init__(self, loop_rate, shared_image: NumpyArray, source=0):
        super().__init__(loop_rate=loop_rate, profile_interval=5)
        self.shared_image = shared_image
        self.source = source
        self.video = None

    def on_work_loop_begin(self):
        self.video = cv2.VideoCapture(self.source)

    def work(self):
        success, image = self.video.read()
        if success:
            self.shared_image.value = image
        else:
            self.common_state.set_exit()

    def on_work_loop_end(self):
        self.video.release()


class PoseEstimationStream(ProcessStream):
    def __init__(self, loop_rate, shared_image: NumpyArray, result_queue: Queue):
        super().__init__(loop_rate=loop_rate, profile_interval=5)
        self.shared_image = shared_image
        self.result_queue = result_queue
        self.pose_estimation = None

    def on_work_loop_begin(self):
        self.pose_estimation = mediapipe.solutions.pose.Pose(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
            model_complexity=0
        )

    def work(self):
        image = cv2.cvtColor(self.shared_image.value, cv2.COLOR_BGR2RGB)
        image.flags.writeable = False
        output = self.pose_estimation.process(image)
        self.result_queue.put(output.pose_landmarks, timeout=1)


class VisualizeStream(ProcessStream):
    def __init__(self, shared_image: NumpyArray, result_queue: Queue):
        super().__init__(profile_interval=5)
        self.shared_image = shared_image
        self.result_queue = result_queue

    def work(self):
        pose_landmarks = self.result_queue.get(timeout=1)
        image = self.shared_image.value
        mediapipe.solutions.drawing_utils.draw_landmarks(
            image, pose_landmarks,
            mediapipe.solutions.pose.POSE_CONNECTIONS
        )
        cv2.imshow('MediaPipe Pose', image)
        if cv2.waitKey(5) & 0xFF == 27:
            self.common_state.set_exit()


class MainStream(ComposeStream):
    def __init__(self, source):
        super().__init__()
        image_size, fps = get_video_params(source)
        shared_image = NumpyArray(image_size)
        result_queue = Queue()
        self.video_stream = VideoStream(fps, shared_image, source)
        self.pose_stream = PoseEstimationStream(fps, shared_image, result_queue)
        self.visualize_stream = VisualizeStream(shared_image, result_queue)


if __name__ == "__main__":
    stream = MainStream(args.input)
    stream.start()
    stream.wait()
    stream.stop()
    stream.join()
