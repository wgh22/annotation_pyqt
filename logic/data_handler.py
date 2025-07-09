import json
import os
from typing import List, Dict, Any

class DataHandler:
    """
    处理从JSON文件加载数据和保存数据。
    此类抽象了标注的文件I/O操作。
    """
    def __init__(self, markout_dir: str, video_base_dir: str):
        """
        初始化DataHandler。

        Args:
            markout_dir (str): 存储JSON标注文件的目录。
            video_base_dir (str): 视频文件夹所在的基础目录。
        """
        if not os.path.exists(markout_dir):
            os.makedirs(markout_dir)
        self.markout_dir = markout_dir
        self.video_base_dir = video_base_dir

    def get_json_path(self, video_name: str) -> str:
        """
        构建视频对应JSON文件的完整路径。

        Args:
            video_name (str): 视频目录的名称。

        Returns:
            str: JSON文件的绝对路径。
        """
        return os.path.join(self.markout_dir, f"{video_name}.json")

    def load_data(self, video_name: str) -> Dict[str, Any]:
        """
        从JSON文件中加载特定视频的标注数据。

        如果文件不存在，则返回默认的数据结构。

        Args:
            video_name (str): 视频目录的名称。

        Returns:
            Dict[str, Any]: 包含视频标注数据的字典。
        """
        json_path = self.get_json_path(video_name)
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading {json_path}: {e}")
                # 出错时返回默认结构
                return self._get_default_structure(video_name)
        else:
            return self._get_default_structure(video_name)

    def save_data(self, video_name: str, data: Dict[str, Any]):
        """
        将视频的标注数据保存到其JSON文件中。

        Args:
            video_name (str): 视频目录的名称。
            data (Dict[str, Any]): 要保存的标注数据字典。
        """
        json_path = self.get_json_path(video_name)
        try:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            print(f"Successfully saved annotations to {json_path}")
        except IOError as e:
            print(f"Error saving to {json_path}: {e}")

    def _get_default_structure(self, video_name: str) -> Dict[str, Any]:
        """
        为新视频创建默认数据结构。

        Args:
            video_name (str): 视频目录的名称。

        Returns:
            Dict[str, Any]: 具有默认结构的字典。
        """
        # 相对路径应从项目根目录开始。
        relative_path = os.path.join(os.path.basename(self.video_base_dir), video_name).replace("\\", "/")
        
        return {
            "video_name": video_name,
            "relative_path": relative_path, # FIX: Add relative_path to the top level
            "description": "Video annotation file.",
            "frame_num_total":0,
            "pre_instructions": [],
            "problem": {
                "abolished": False,
                "issue": False
            },
            "annotations": []
        }
        
    def format_annotation(self, instruction: str, start: int, end: int) -> Dict[str, Any]:
        """
        格式化单个标注记录。

        Args:
            instruction (str): 动作描述。
            start (int): 开始帧号。
            end (int): 结束帧号。

        Returns:
            Dict[str, Any]: 代表单个标注的字典。
        """
        # Note: We are keeping relative_path inside each annotation for consistency with the initial request,
        # even though it's also at the top level now.
        return {
            "instruction": instruction,
            "start": start,
            "end": end
        }
