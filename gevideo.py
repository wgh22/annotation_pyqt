import cv2
import os
import re

def images_to_video_with_frame_numbers(image_folder, output_video_file, fps):
    """
    将文件夹中的图片序列合成为带帧号的视频。

    :param image_folder: 存放图片的文件夹路径。
    :param output_video_file: 输出的视频文件路径和名称 (例如 'output.mp4')。
    :param fps: 视频的帧率 (Frames Per Second)。
    """
    images = [img for img in os.listdir(image_folder) if img.endswith(".png") or img.endswith(".jpg")]
    
    # 确保图片按数字顺序排序，能正确处理 'frame1.png', 'frame10.png'
    try:
        images.sort(key=lambda f: int(re.sub(r'\D', '', f)))
    except ValueError:
        print("警告：文件名不包含数字，将按字母顺序排序。")
        images.sort()

    if not images:
        print(f"在文件夹 {image_folder} 中没有找到图片文件！")
        return

    first_image_path = os.path.join(image_folder, images[0])
    frame = cv2.imread(first_image_path)
    if frame is None:
        print(f"无法读取第一张图片: {first_image_path}")
        return
    height, width, layers = frame.shape
    size = (width, height)

    fourcc = cv2.VideoWriter_fourcc(*'mp4v') 
    out = cv2.VideoWriter(output_video_file, fourcc, fps, size)

    print("开始合成视频并添加帧号...")
    # 使用 enumerate 来同时获取索引 (i) 和文件名 (image_name)
    for i, image_name in enumerate(images):
        image_path = os.path.join(image_folder, image_name)
        frame = cv2.imread(image_path)

        # ------------------- 新增核心代码：添加帧号 -------------------
        
        # 1. 定义要显示的文本（帧号从 1 开始，所以用 i + 1）
        frame_number_text = f"Frame: {i + 1}"

        # 2. 定义文本参数
        font = cv2.FONT_HERSHEY_SIMPLEX  # 字体
        font_scale = 1.5                  # 字体大小
        font_color = (255, 255, 255)      # 字体颜色 (B, G, R) -> 这里是白色
        thickness = 2                     # 字体粗细
        
        # 3. 定义文本位置 (org): (x, y) 坐标，代表文本框的左下角
        #    我们将它放在左下角，留出一些边距
        position = (30, height - 30) # 离左边30像素，离底部30像素

        # 4. 使用 cv2.putText() 将文本绘制到帧上
        cv2.putText(
            frame,                   # 要绘制的图像
            frame_number_text,       # 要绘制的文本
            position,                # 文本的起始坐标 (左下角)
            font,                    # 字体
            font_scale,              # 字体大小
            font_color,              # 字体颜色
            thickness,               # 字体粗细
            cv2.LINE_AA              # 线条类型 (LINE_AA 使线条更平滑)
        )
        
        # -----------------------------------------------------------

        # 将处理过的帧写入视频
        out.write(frame)
        
        # 打印进度
        print(f"正在处理第 {i+1}/{len(images)} 帧: {image_name}")

    out.release()
    cv2.destroyAllWindows()
    print(f"\n带帧号的视频已成功保存到: {output_video_file}")


# --- 主程序 ---
if __name__ == '__main__':
    # --- 请根据您的实际情况修改以下参数 ---
    
    # 1. 图片所在的文件夹路径
    image_folder = 'img' 
    
    # 2. 输出视频的文件名和路径
    output_video_file = 'output_with_frame_numbers.mp4'
    
    # 3. 视频的帧率
    fps = 30

    images_to_video_with_frame_numbers(image_folder, output_video_file, fps)