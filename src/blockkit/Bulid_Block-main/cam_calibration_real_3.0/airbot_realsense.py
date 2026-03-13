'''
Copyright: qiuzhi.tech
Author: 草木
Date: 2025-06-16 11:56:45
LastEditTime: 2025-06-16 11:56:45
'''
import pyrealsense2 as rs
import numpy as np
import yaml
import cv2
from typing import Union, List


class RealsenseCamera:
    __unaligned_warning_printed = False

    def __init__(self) -> None:
        with open("configs/rs_camera.yaml", "r") as file:
            config = yaml.safe_load(file)
            # config_path = yaml.safe_load(file)["Path"]
        # config = yaml.safe_load(open(config_path, "r"))
        
        self.inited: bool = False
        self.resolution = config["Realsense"]["resolution"]
        self.depth_factor = config["Realsense"]["depth_factor"]
        self.profile = config["Realsense"][self.resolution]["profile"]
        print(f"Realsense camera profile: {self.profile}")
        self.intrinsic = config["Realsense"][self.resolution]["intrinsic"]
        self.distortion = config["Realsense"][self.resolution]["distortion"]
        
        self.init()
    
    def init(self):
        # Configure streams
        self.pipeline = rs.pipeline()
        rs_config = rs.config()
        rs_config.enable_stream(
            rs.stream.depth,
            self.profile[0],
            self.profile[1],
            rs.format.z16,
            self.profile[2],
        )
        rs_config.enable_stream(
            rs.stream.color,
            self.profile[0],
            self.profile[1],
            rs.format.bgr8,
            self.profile[2],
        )
        # Start streaming
        cfg = self.pipeline.start(rs_config)
        color_profile = cfg.get_stream(rs.stream.color)
        depth_profile = cfg.get_stream(rs.stream.depth)
        print(
            f"color profile:{color_profile.as_video_stream_profile()}\ndepth profile:{depth_profile.as_video_stream_profile()}"
        )
        
        # Set processers
        self.aligner = rs.align(rs.stream.color)
        self.depth_hole_filling = rs.hole_filling_filter()
        self.colorizer = rs.colorizer()

        self.inited = True

    @property
    def WIDTH(self) -> int:
        return self.profile[0]

    @property
    def HEIGHT(self) -> int:
        return self.profile[1]

    @property
    def FPS(self) -> int:
        return self.profile[2]

    @property
    def INTRINSIC(self) -> np.ndarray:
        return self.intrinsic
    
    @property
    def DISTORTION(self) -> np.ndarray:
        return self.distortion

    def deinit(self) -> bool:
        self.inited = False
        self.pipeline.stop()
        return True

    def get_rgb(self) -> np.ndarray:
        return self.get_frame("rgb")

    def get_bgr(self) -> np.ndarray:
        return self.get_frame("bgr")

    def get_depth(self) -> np.ndarray:
        return self.get_frame("depth")

    def get_depth_map(self) -> np.ndarray:
        return self.get_frame("depth_map")

    def get_frame(self, frame_type: Union[str, List[str]] = ["bgr","depth"], align: bool = True):
        frames = self.pipeline.wait_for_frames()
        if align:
            frames = self.aligner.process(frames)
        elif not self.__unaligned_warning_printed:
            print("\033[93mWarning: get unaligned frame\033[0m")  # 黄色警告
            self.__unaligned_warning_printed = True

        depth_frame = frames.get_depth_frame()
        depth_frame = self.depth_hole_filling.process(depth_frame)
        color_frame = frames.get_color_frame()

        depth_image = np.array(depth_frame.get_data()).astype(np.float32)
        bgr_image = np.array(color_frame.get_data())
        rgb_image = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)
        depth_map = np.array(self.colorizer.colorize(depth_frame).get_data())

        frames = {
            "rgb": rgb_image,
            "bgr": bgr_image,
            "depth": depth_image,
            "depth_map": depth_map
        }
        
        if isinstance(frame_type, list):
            result = [] 
            for i in frame_type:
                if i not in frames.keys():
                    raise TypeError(
                        "Invalid frame_type, candidate type: ['rgb', 'bgr', 'depth', 'depth_map']"
                    )
                else:
                    result.append(frames[i])
            return result
        elif isinstance(frame_type, str):
            if frame_type not in frames.keys():
                raise TypeError(
                    "Invalid frame_type, candidate type: ['rgb', 'bgr', 'depth', 'depth_map']"
                )
            return frames[frame_type]
        else:
            raise TypeError(
                "Param frame_type should be 'str | list[str]'"
            )

    def create_point_cloud(self, depth: np.ndarray, organized: bool = True):
        """Generate point cloud using depth image only.

        Input:
            depth: [numpy.ndarray, (H,W), numpy.float32]
                depth image
            organized: bool
                whether to keep the cloud in image shape (H,W,3)

        Output:
            cloud: [numpy.ndarray, (H,W,3)/(H*W,3), numpy.float32]
                generated cloud, (H,W,3) for organized=True, (H*W,3) for organized=False
        """        
        xmap = np.arange(depth.shape[1])
        ymap = np.arange(depth.shape[0])
        xmap, ymap = np.meshgrid(xmap, ymap)
        points_z = depth / self.depth_factor
        points_x = (
            (xmap - self.intrinsic[0][2]) * points_z / self.intrinsic[0][0]
        )
        points_y = (
            (ymap - self.intrinsic[1][2]) * points_z / self.intrinsic[1][1]
        )
        cloud = np.stack([points_x, points_y, points_z], axis=-1)
        if not organized:
            cloud = cloud.reshape([-1, 3])
        return cloud
        

if __name__ == "__main__":
    import datetime
    import os

    camera = RealsenseCamera()
    frame_cnt = 0
    dir_name = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    save_path = os.path.join("yolo_dataset", dir_name)
    os.makedirs(save_path, exist_ok=True)
    
    while True:
        color_image = camera.get_frame(frame_type="bgr")
        cv2.imshow(f"Color Image {frame_cnt}", color_image)
        key = cv2.waitKey(1)
        if key == 27:   
            cv2.destroyAllWindows()
            break
        elif key == ord(" "):
            name = datetime.datetime.now().strftime("%Y%m%d%H%M%S") + ".png"
            img_path = os.path.join(save_path, name)
            cv2.imwrite(img_path, color_image)
            frame_cnt += 1
            frame_cnt = frame_cnt % 20
            cv2.destroyAllWindows()
    camera.deinit()
