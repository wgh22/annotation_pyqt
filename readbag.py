try:
    import rosbag
except ImportError:
    print("rosbag import error")
import numpy as np
import cv2
import matplotlib.pyplot as plt
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
    # 使用 OpenCV 将解压后的图像保存为 PNG 文件
    cv2.imwrite(f'/work/output_image_.png', img)

def read_status(msg):
    np_arr = np.frombuffer(msg.data,np.float64)
    print(np_arr)

def save_compressed_depth_image(msg):
    # # msg.data 是压缩深度图像的数据，可以通过 cv2 来解压

    with open('depth_image.bin', 'wb') as f:
        f.write(msg.data)  # 将 msg.data 直接写入二进制文件 

def read_bag_movie(bag_file):
    # 打开 .bag 文件
    img_list = []
    with rosbag.Bag(bag_file, 'r') as bag:
        # 打印文件中所有的消息类型和主题
        print("主题和消息类型:")
        last_time = 0
        max_error = -999
        import math
        for idx, (topic, msg, _) in enumerate(bag.read_messages()):
            if idx == 467:
                break
            t = msg.header.stamp
            print(t)
            # print(msg.data)
            # continue

            img_list.append(save_compressed_image(msg.data))

        image_list = [convert_cv2_to_moviepy_format(img) for img in img_list]

        # 创建视频：15fps
        video_clip = ImageSequenceClip(image_list, fps=15)

        # 输出视频
        video_clip.write_videofile("/work/output_video.mp4", codec="libx264")

def read_bag_file(bag_file):
    # 打开 .bag 文件
    img_list = []
    with rosbag.Bag(bag_file, 'r') as bag:
        # 打印文件中所有的消息类型和主题
        print("主题和消息类型:")
        for idx, (topic, msg, _) in enumerate(bag.read_messages()):
            print(_)
            print(msg.sensor_states[0].finger_sensor_states[0].location)
            print(msg.sensor_states[0].finger_sensor_states[0].calc_force)
            print(msg.sensor_states[0].finger_sensor_states[1].location)
            print(msg.sensor_states[0].finger_sensor_states[1].calc_force)
            print(msg.sensor_states[0].finger_sensor_states[2].location)
            print(msg.sensor_states[0].finger_sensor_states[2].calc_force)
            print(msg.sensor_states[0].finger_sensor_states[3].location)
            print(msg.sensor_states[0].finger_sensor_states[3].calc_force)
            print(msg.sensor_states[0].finger_sensor_states[4].location)
            print(msg.sensor_states[0].finger_sensor_states[4].calc_force)

            break


def find_closest_timestamps(group1, group2):
    result = []
    i, j = 0, 0  # i 指向 group1，j 指向 group2
    
    while i < len(group1):
        # 移动 j 指针，找到 group2 中大于等于 group1[i] 的位置
        while j < len(group2) - 1 and group2[j + 1][0] < group1[i][0]:
            j += 1
        
        # 选择 group2[j] 和 group2[j+1] 中最接近 group1[i] 的时间戳
        if j + 1 < len(group2) and abs(group2[j + 1][0] - group1[i][0]) < abs(group2[j][0] - group1[i][0]):
            result.append(group2[j + 1])
        else:
            result.append(group2[j])
        
        i += 1
    
    return result


def get_image_arm_handstate(source_path):
    rgb_path = f'{source_path}/realsence_color_img.bag'
    right_hand_path = f'{source_path}/xhand/right_hand_status.bag'
    right_arm_path = f'{source_path}/right_arm_status.bag'
    rgb_list, right_hand_list, right_arm_list = [], [], []
    with rosbag.Bag(rgb_path, 'r') as bag:
        for idx, (topic, msg, _) in enumerate(bag.read_messages()):
            rgb_list.append((msg.header.stamp, msg.data))
    with rosbag.Bag(right_hand_path, 'r') as bag:
        for idx, (topic, msg, _) in enumerate(bag.read_messages()):
            cur_force = []
            cur_force.append(msg.sensor_states[0].finger_sensor_states[0].calc_force)
            cur_force.append(msg.sensor_states[0].finger_sensor_states[1].calc_force)
            cur_force.append(msg.sensor_states[0].finger_sensor_states[2].calc_force)
            cur_force.append(msg.sensor_states[0].finger_sensor_states[3].calc_force)
            cur_force.append(msg.sensor_states[0].finger_sensor_states[4].calc_force)
            right_hand_list.append((msg.header.stamp, msg.hand_states[0].position, cur_force))
    with rosbag.Bag(right_arm_path, 'r') as bag:
        for idx, (topic, msg, _) in enumerate(bag.read_messages()):
            right_arm_list.append((msg.header.stamp, msg.joint_status))
    
    aligned_arm_list = find_closest_timestamps(rgb_list, right_arm_list)
    aligned_hand_list = find_closest_timestamps(rgb_list, right_hand_list)

    ret_list = []
    print_stamp = []
    for i in range(len(rgb_list)):
        ret_list.append((rgb_list[i], aligned_arm_list[i], aligned_hand_list[i]))
        print_stamp.append((rgb_list[i][0].to_sec(), aligned_arm_list[i][0].to_sec(), aligned_hand_list[i][0].to_sec()))

    for item in print_stamp:
        print(item)
    return ret_list



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
    timepoints = [img[0].to_sec() for (img, _, _) in timepoints]
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

def read_and_save():
    
    import os
    bag_path_list = ["428_data.txt"]
    save_list = ["mount/xhand/202504/raw_data/c3/0428"]
    for number in range(len(bag_path_list)):
        count_idx = 0
        bag_list_path = bag_path_list[number]
        save_parent_path = save_list[number]
        with open(bag_list_path, "r") as f:
            for bag_pth in f.readlines():
                file_name = bag_pth.split(",")[0]
                bag_path = file_name
                datalist = get_image_arm_handstate(bag_path)
                #option1
                keyboard_path = f"{bag_path}/keyboard.bag"
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
                    os.makedirs(f'{save_parent_path}/{count_idx}', exist_ok=True)
                    os.makedirs(f'{save_parent_path}/{count_idx}/img', exist_ok=True)
                    img_list = []
                    for i in range(clip[0], clip[1] + 1):
                        img_i = i - clip[0]
                        # write datalist[i][0][1] in raw_data/grasp/{idx}/img/{i}.png
                        img_cnt = save_compressed_image(datalist[i][0][1])
                        cv2.imwrite(f'{save_parent_path}/{count_idx}/img/{img_i}.png',img_cnt)
                        img_list.append(img_cnt)

                        # write datalist[i][1][1] in raw_data/grasp/{idx}/arm.txt(ecah line is a joint status)
                        with open(f'{save_parent_path}/{count_idx}/arm.txt', 'a') as f:
                            f.write(str(datalist[i][1][1])+ '\n')
                        # write datalist[i][2][1] in raw_data/grasp/{idx}/hand.txt(ecah line is a hand status)
                        with open(f'{save_parent_path}/{count_idx}/hand.txt', 'a') as f:
                            f.write(str(datalist[i][2][1]) + '\n')
                        with open(f'{save_parent_path}/{count_idx}/hand_force.txt', 'a') as f:
                            f.write(str(datalist[i][2][2]) + '\n')
                    # image_list = [convert_cv2_to_moviepy_format(img) for img in img_list]

                    # video_clip = ImageSequenceClip(image_list, fps=30)

                    # # 输出视频
                    # video_clip.write_videofile(f'raw_data/grasp/{count_idx}/output_video.mp4', codec="libx264")
                    count_idx += 1


# if __name__ == '__main__':
#     # source_path = '/work/data/bags/2025_02_27_12_59_47'
#     # source_path = '/work/data/bags/2025_02_27_12_03_25'
#     source_path = '/home/ruicheng/MSRA_SRobot_core/data/bags/2025_04_09_08_52_50'

    
#     bag_file = f'{source_path}/xhand/right_hand_status.bag'
#     # read_bag_movie(bag_file)
#     read_bag_file(bag_file)
#     # get_image_6dpos_handstate(source_path=source_path)
#     # get_image_6dpos_handstate(source_path)
#     # visualize_depth('depth_image.bin')




if __name__ == "__main__":
    read_and_save()