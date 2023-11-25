import argparse
from ctypes import c_uint8
from multiprocessing import Queue, Array, Lock, set_start_method

import cv2  # type: ignore
import mediapipe  # type: ignore
import numpy as np  # type: ignore

from rosny import ProcessNode, ComposeNode

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--input", default=0,
                    help="Source of video. Defaults to webcam.")
parser.add_argument("-m", "--method", default="default", type=str,
                    help="A method to start child processes, "
                         "value can be 'fork', 'spawn' or 'forkserver'.")
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
        self.ctype = ctype
        self.lock = Lock()
        self.array = Array(ctype, int(np.prod(self.shape)))

    def _numpy_array(self) -> np.ndarray:
        return np.ndarray(self.shape,
                          dtype=self.ctype,
                          buffer=self.array.get_obj())

    @property
    def value(self) -> np.ndarray:
        with self.lock:
            return self._numpy_array().copy()

    @value.setter
    def value(self, array: np.ndarray):
        with self.lock:
            self._numpy_array()[:] = array


class VideoNode(ProcessNode):
    def __init__(self, loop_rate, shared_image: NumpyArray, source=0):
        super().__init__(loop_rate=loop_rate, profile_interval=5)
        self.shared_image = shared_image
        self.source = source
        self.video = None

    def on_loop_begin(self):
        self.video = cv2.VideoCapture(self.source)

    def work(self):
        success, image = self.video.read()
        if success:
            self.shared_image.value = image
        else:
            self.common_state.set_exit()

    def on_loop_end(self):
        self.video.release()


class PoseEstimationNode(ProcessNode):
    def __init__(self, loop_rate, shared_image: NumpyArray, result_queue: Queue):
        super().__init__(loop_rate=loop_rate, profile_interval=5)
        self.shared_image = shared_image
        self.result_queue = result_queue
        self.pose_estimation = None

    def on_loop_begin(self):
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


class VisualizeNode(ProcessNode):
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
        if cv2.waitKey(1) & 0xFF == 27:
            self.common_state.set_exit()


class MainNode(ComposeNode):
    def __init__(self, source):
        super().__init__()
        image_size, fps = get_video_params(source)
        shared_image = NumpyArray(image_size)
        result_queue = Queue(maxsize=2)
        self.video_node = VideoNode(fps, shared_image, source)
        self.pose_node = PoseEstimationNode(fps, shared_image, result_queue)
        self.visualize_node = VisualizeNode(shared_image, result_queue)


if __name__ == "__main__":
    if args.method != "default":
        set_start_method(args.method)

    node = MainNode(args.input)
    node.start()
    node.wait()
    node.stop()
    node.join()
