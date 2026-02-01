import io
import platform
import subprocess
import time

import numpy as np
from PIL import Image, ImageGrab

from xiaozhi_sdk.cli.logger import logger
from xiaozhi_sdk.utils.mcp_tool import get_device_status, screenshot, set_volume, take_photo

# 音量大小 (0.0-1.0)
volume = 0.5


def clear_clipboard():
    """清除剪贴板内容（跨平台）"""
    try:
        system = platform.system()
        if system == "Darwin":  # macOS
            subprocess.run(["pbcopy"], input=b"", check=False)
        elif system == "Windows":  # Windows
            subprocess.run(
                ["powershell", "-Command", "Set-Clipboard -Value ''"],
                check=False,
                capture_output=True,
            )
        else:  # Linux
            # 尝试使用 xclip
            try:
                subprocess.run(["xclip", "-selection", "clipboard", "-i", "/dev/null"], check=False)
            except FileNotFoundError:
                # 如果 xclip 不存在，尝试使用 xsel
                try:
                    subprocess.run(["xsel", "-c", "-b"], check=False)
                except FileNotFoundError:
                    logger.warning("无法清除剪贴板：未找到 xclip 或 xsel 命令")
    except Exception as e:
        logger.warning("清除剪贴板失败: %s", e)


def mcp_tool_func(xiaozhi):

    async def mcp_turn_camera(data: dict) -> tuple[dict, bool]:
        import cv2

        """打开摄像头并拍照"""
        cap = None
        try:
            logger.info("正在打开摄像头...")
            # 打开默认摄像头（索引 0）
            cap = cv2.VideoCapture(0)

            if not cap.isOpened():
                logger.error("无法打开摄像头")
                return {"message": "无法打开摄像头，请确保摄像头已连接并授予权限"}, True

            # 设置摄像头分辨率（可选）
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

            # 丢弃前几帧，让摄像头稳定（前几帧通常是黑的）
            for _ in range(5):
                cap.read()

            # 等待摄像头稳定
            time.sleep(0.1)

            # 读取一帧
            ret, frame = cap.read()

            if not ret or frame is None:
                logger.error("无法从摄像头获取画面")
                return {"message": "无法从摄像头获取画面"}, True

            # OpenCV 使用 BGR 格式，需要转换为 RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # 转换为 PIL Image
            im = Image.fromarray(frame_rgb)

            # 转换为 JPEG 字节
            byte_io = io.BytesIO()
            im.save(byte_io, format="JPEG", quality=30)
            im.save("./test.jpg", format="JPEG", quality=30)

            img_bytes = byte_io.getvalue()
            logger.info("摄像头拍照成功")

        except Exception as e:
            logger.error("摄像头拍照失败: %s", e)
            return {"message": f"摄像头拍照失败: {str(e)}"}, True
        finally:
            # 确保释放摄像头资源
            if cap is not None:
                cap.release()

        return await xiaozhi.async_analyze_image(img_bytes, data.get("question", "请描述这张图片"))

    async def mcp_local_screenshot(data) -> (dict, bool):
        logger.info("请截图需要识别的内容:")
        time.sleep(1)
        for _ in range(20):
            im = ImageGrab.grabclipboard()
            if not im:
                time.sleep(0.3)
                continue
            if im.mode == "RGBA":
                im = im.convert("RGB")

            byte_io = io.BytesIO()
            im.save(byte_io, format="JPEG", quality=30)
            # im.save("./test.jpg", format='JPEG', quality=30)

            img_bytes = byte_io.getvalue()

            # 读取完截图后清除剪贴板
            clear_clipboard()

            logger.info("截图成功")
            return await xiaozhi.async_analyze_image(img_bytes, data["question"])

        logger.error("截图失败, 请让在10秒内完成截图操作")
        return {"message": "请提醒用户在10秒内完成截图操作"}, True

    async def mcp_global_screenshot(data: dict) -> (dict, bool):
        # 获取屏幕截图
        try:
            logger.info("正在截取屏幕...")
            im = ImageGrab.grab()
            if im.mode == "RGBA":
                im = im.convert("RGB")

            byte_io = io.BytesIO()
            im.save(byte_io, format="JPEG", quality=30)
            img_bytes = byte_io.getvalue()
            logger.info("屏幕截图成功")

            return await xiaozhi.async_analyze_image(img_bytes, data["question"])
        except Exception as e:
            logger.error("屏幕截图失败: %s", e)
            return "屏幕截图失败", True

    def mcp_set_volume(data: dict) -> (dict, bool):
        global volume
        volume = float(data["volume"] / 100)
        logger.info("音量设置为: %s%%", data["volume"])
        return {}, False

    def mcp_get_device_status(data: dict) -> (dict, bool):
        return {"audio_speaker": {"volume": int(volume * 100)}, "platform": platform.uname()}, False

    # take_photo["tool_func"] = mcp_turn_camera
    take_photo["tool_func"] = mcp_local_screenshot
    take_photo["is_async"] = True

    set_volume["tool_func"] = mcp_set_volume
    get_device_status["tool_func"] = mcp_get_device_status
    screenshot["tool_func"] = mcp_global_screenshot
    screenshot["is_async"] = True

    return [take_photo, set_volume, get_device_status]
