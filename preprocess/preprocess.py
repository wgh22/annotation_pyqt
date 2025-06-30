import os
try:
    import rosbag
except ImportError:
    print("rosbag import error")
import numpy as np
import cv2
try:
    from moviepy import ImageSequenceClip
except:
    print("moviepy import error")

def convert_cv2_to_moviepy_format(cv2_image):
    # 需要将 BGR 格式的 OpenCV 图像转换为 RGB 格式
    return cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB)

def save_compressed_image(msg):
    # msg.data 是压缩图像的数据，可以通过 cv2 来解压
    np_arr = np.frombuffer(msg, np.uint8)  # 将 byte 数据转换为 numpy 数组
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)  # 解压图像
    return img



def save_compressed_depth_image(msg):
    # # msg.data 是压缩深度图像的数据，可以通过 cv2 来解压

    with open('depth_image.bin', 'wb') as f:
        f.write(msg.data)  # 将 msg.data 直接写入二进制文件 


def get_image(rgb_path):
    rgb_list = []
    with rosbag.Bag(rgb_path, 'r') as bag:
        for idx, (topic, msg, _) in enumerate(bag.read_messages()):
            rgb_list.append((msg.header.stamp, msg.data))

    return rgb_list



def process_events(events):
    """
    输入 events：列表，元素形如 (t, data)，其中 t 为数字（时间），data 为 'start'、'stop' 或 'stopanddelete'，
                    并且 events 已按照 t 从小到大排列。
    输出：列表，元素形如 (t1, t2)，t1 来自 'start' 消息，t2 来自与当前 start 最近的 stop 消息。
    
    逻辑：
      - 扫描列表，当遇到一个 'start' 消息时，收集从该消息之后到下一个 'start' 之间的所有消息。
      - 如果该区间内没有消息，或包含 'stopanddelete' 消息，则跳过该 start。
      - 如果该区间内只有 'stop' 消息，则选择第一个 stop 消息（即离 start 最近的）并生成 (t_start, t_stop)。
    """
    results = []
    n = len(events)
    i = 0

    while i < n:
        t, data = events[i]
        if data == "start":
            start_time = t
            # 收集从当前 start 后到下一个 start 之间的消息
            j = i + 1
            group = []
            while j < n and events[j][1] != 'start':
                group.append(events[j])
                j += 1

            # 如果没有消息或有 'stopanddelete' 消息，则跳过
            if not group or any(item[1] == "stop_and_delete" for item in group):
                i = j
                continue

            # 仅当所有消息都是 stop 时，则选择离当前 start 最近的 stop 消息(即第一个 stop)
            stops = [item for item in group if item[1] == 'stop']
            if stops:
                results.append((start_time, stops[0][0]))
            # 跳至下一个 start
            i = j
        else:
            i += 1

    return results

def extract_indices_from_intervals(timepoints, intervals):
    """
    输入：
      - timepoints: 排好序的时间点列表，例如 [1, 3, 5, 7, 9, 11, 13]
      - intervals: 排好序的不重叠区间列表，例如 [(2, 8), (10, 14)]
    输出：
      - 列表：对于每个区间，返回一个二元组 (start_index, end_index)，表示该区间内在 timepoints 的下标范围；
              如果区间内没有时间点，则返回 None。
    """
    results = []
    timepoints = [img[0].to_sec() for img in timepoints]
    n = len(timepoints)
    j = 0  # timepoints 的位置指针

    for s, t in intervals:
        # 跳过所有在区间起点 s 之前的时间点
        while j < n and timepoints[j] < s:
            j += 1
        # 如果当前位置在区间内，则记录下标
        if j < n and timepoints[j] <= t:
            start_index = j
            # 将指针移动到超出 t 的位置
            while j < n and timepoints[j] <= t:
                j += 1
            end_index = j - 1
            results.append((start_index, end_index))
        else:
            # 当前区间内没有时间点
            raise ValueError(f"区间 {s} - {t} 内没有时间点")

    return results

def clip_by_time(data_list, threshold=4/30):
    """
    将排好序的1维时间列表按照相邻元素时间差分割成若干段，
    当两个相邻时间点的差值大于 threshold（默认1/30秒）时，
    则认为存在断裂，当前点为新段起始时间。
    
    返回：一个列表，包含各段起始时间
    """
    time_list = [img[0].to_sec() for (img, _, _) in data_list]
    if not time_list:
        return []
    
    segments = []
    start_index = 0

    for i in range(1, len(time_list)):
        # 如果当前时间点与前一个时间点差值超过阈值，则切分一段
        if time_list[i] - time_list[i - 1] > threshold:
            segments.append((start_index, i - 1))
            start_index = i

    # 添加最后一段
    segments.append((start_index, len(time_list) - 1))
    return segments

def process_all_bag_files(bag_data_dir, video_dir):
    """
    Main preprocessing function.
    (This function remains unchanged but is included for completeness)
    """
    if not os.path.exists(bag_data_dir):
        print(f"Error: Bag data directory not found at {bag_data_dir}")
        return
    
    # bag_path_list = ["428_data.txt"]
    # save_list = ["mount/xhand/202504/raw_data/c3/0428"]
    for dir_name in sorted(os.listdir(bag_data_dir)):
        count_idx = 0
        bag_list_path = os.path.join(bag_data_dir, dir_name)
        if not os.path.isdir(bag_list_path): continue
        
        # save_parent_path = save_list[number]
        color_bag_path = os.path.join(bag_list_path, 'realsence_color_img.bag')
        
        # output_video_dir = os.path.join(video_dir, dir_name)
        # output_img_dir = os.path.join(output_video_dir, 'img')
        # output_video_path = os.path.join(output_video_dir, 'video.mp4')

        # if os.path.exists(output_video_path):
        #     print(f"Video already exists, skipping: {output_video_path}")
        #     continue

        if not os.path.exists(color_bag_path):
            print(f"Warning: 'realsence_color_img.bag' not found in {bag_list_path}. Skipping.")
            continue
        
        
        datalist = get_image(color_bag_path)
        #option1
        keyboard_path = os.path.join(bag_list_path, 'keyboard.bag')
        if not os.path.exists(keyboard_path):
            indices = [(0, len(datalist) - 1)]
        else:
            asd = []
            with rosbag.Bag(keyboard_path, 'r') as bag:
                for id, (topic, msg, t) in enumerate(bag.read_messages()):
                    asd.append((t.to_sec(), msg.data))
            clips = process_events(asd)
            
            indices = extract_indices_from_intervals(datalist, clips)

        # option2
        # indices = clip_by_time(datalist)

        for clip in indices:
            # mkdir raw_data/grasp/{idx}
            output_video_dir = f'{os.path.join(video_dir, dir_name)}_{count_idx}'
            output_img_dir = os.path.join(output_video_dir, 'img')
            output_video_path = os.path.join(output_video_dir, 'video.mp4')
            
            if os.path.exists(output_video_path):
                print(f"Video already exists, skipping: {output_video_path}")
                continue
            
            os.makedirs(output_video_dir, exist_ok=True)
            os.makedirs(output_img_dir, exist_ok=True)
            img_list = []
            for i in range(clip[0], clip[1] + 1):
                img_i = i - clip[0]
                # write datalist[i][0][1] in raw_data/grasp/{idx}/img/{i}.png
                img_cnt = save_compressed_image(datalist[i][1])
                cv2.imwrite(f'{output_img_dir}/{img_i}.png',img_cnt)
                img_list.append(img_cnt)

            image_list = [convert_cv2_to_moviepy_format(img) for img in img_list]

            video_clip = ImageSequenceClip(image_list, fps=25)

            # # 输出视频
            video_clip.write_videofile(output_video_path, codec="libx264")
            count_idx += 1
