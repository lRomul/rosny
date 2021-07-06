import argparse
from multiprocessing import Queue

import cv2  # type: ignore
import mediapipe  # type: ignore

from rosny import ProcessStream, ComposeStream

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--input", default=0,
                    help="Source of video. Defaults to webcam.")
args = parser.parse_args()


class VideoStream(ProcessStream):
    def __init__(self, image_queue: Queue, source=0):
        super().__init__(profile_interval=5)
        self.image_queue = image_queue
        self.source = source
        self.video = None

    def on_work_loop_begin(self):
        self.video = cv2.VideoCapture(self.source)

    def work(self):
        success, image = self.video.read()
        if success:
            self.image_queue.put(image, timeout=1)
        else:
            self.common_state.set_exit()

    def on_work_loop_end(self):
        self.video.release()


class PoseEstimationStream(ProcessStream):
    def __init__(self, image_queue: Queue, result_queue: Queue):
        super().__init__(profile_interval=5)
        self.image_queue = image_queue
        self.result_queue = result_queue
        self.pose_estimation = None

    def on_work_loop_begin(self):
        self.pose_estimation = mediapipe.solutions.pose.Pose(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
            model_complexity=0
        )

    def work(self):
        bgr_image = self.image_queue.get(timeout=1)
        image = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)
        image.flags.writeable = False
        output = self.pose_estimation.process(image)
        self.result_queue.put((bgr_image, output.pose_landmarks), timeout=1)


class VisualizeStream(ProcessStream):
    def __init__(self, result_queue: Queue):
        super().__init__(profile_interval=5)
        self.result_queue = result_queue

    def work(self):
        image, pose_landmarks = self.result_queue.get(timeout=1)
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
        image_queue = Queue()
        result_queue = Queue()
        self.video_stream = VideoStream(image_queue, source)
        self.pose_stream = PoseEstimationStream(image_queue, result_queue)
        self.visualize_stream = VisualizeStream(result_queue)


if __name__ == "__main__":
    stream = MainStream(args.input)
    stream.start()
    stream.wait()
    stream.stop()
    stream.join()
