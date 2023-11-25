import argparse

import cv2  # type: ignore
import mediapipe  # type: ignore
import numpy as np  # type: ignore

from rosny import CommonState, ThreadNode, ComposeNode

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--input", default=0,
                    help="Source of video. Defaults to webcam.")
args = parser.parse_args()


class State(CommonState):
    def __init__(self):
        super(State, self).__init__()
        self.image = None
        self.selfie_output = None


class VideoNode(ThreadNode):
    def __init__(self, source=0):
        self.video = cv2.VideoCapture(source)
        self.fps = self.video.get(cv2.CAP_PROP_FPS)
        super().__init__(loop_rate=self.fps, profile_interval=5)

    def work(self):
        success, image = self.video.read()
        if success:
            image = cv2.flip(image, 1)
            self.common_state.image = image
        else:
            self.common_state.set_exit()

    def on_join_end(self):
        self.video.release()


class SelfieSegmentationNode(ThreadNode):
    def __init__(self, loop_rate):
        super().__init__(loop_rate=loop_rate, profile_interval=5)
        self.selfie_segmentation = mediapipe.solutions\
            .selfie_segmentation.SelfieSegmentation(model_selection=1)

    def work(self):
        image = self.common_state.image
        if image is not None:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            image.flags.writeable = False
            output = self.selfie_segmentation.process(image)
            self.common_state.selfie_output = output


class VisualizeNode(ThreadNode):
    def __init__(self, loop_rate):
        super().__init__(loop_rate=loop_rate, profile_interval=5)

    def work(self):
        image = self.common_state.image
        output = self.common_state.selfie_output
        if image is not None and output is not None:
            condition = np.stack((output.segmentation_mask,) * 3, axis=-1) > 0.1
            bg_image = np.zeros(image.shape, dtype=np.uint8)
            bg_image[:] = (192, 192, 192)
            output_image = np.where(condition, image, bg_image)
            cv2.imshow('MediaPipe Selfie Segmentation', output_image)
            if cv2.waitKey(1) & 0xFF == 27:
                self.common_state.set_exit()


class MainNode(ComposeNode):
    def __init__(self, source):
        super().__init__()
        self.video_node = VideoNode(source)
        self.selfie_node = SelfieSegmentationNode(self.video_node.fps)
        self.visualize_node = VisualizeNode(self.video_node.fps)
        self.compile(common_state=State())  # Share custom common_state between nodes


if __name__ == "__main__":
    node = MainNode(args.input)
    node.start()
    node.wait()
    node.stop()
    node.join()
