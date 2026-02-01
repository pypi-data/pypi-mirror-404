import asyncio
import time
from collections import deque
from typing import Optional

import click
import numpy as np
import sounddevice as sd

from xiaozhi_sdk import XiaoZhiWebsocket
from xiaozhi_sdk.cli.logger import logger
from xiaozhi_sdk.cli.mcp_tools import mcp_tool_func, volume
from xiaozhi_sdk.config import INPUT_AUDIO_FRAME_DURATION
from xiaozhi_sdk.utils import get_mac_address
from xiaozhi_sdk.utils.audio_device import get_audio_device_info, print_audio_devices

# 全局状态
input_audio_buffer: deque[bytes] = deque()
device_stauts = "listen"  # "speak" or "listen"

is_end = False
human_asr_end_time = None
audio_device_info = get_audio_device_info()


async def handle_message(message):
    global device_stauts
    global human_asr_end_time

    """处理接收到的消息"""
    global is_end

    if message["type"] == "tts" and message["state"] == "start":  # start
        device_stauts = "speak"  # 防止打断

    elif message["type"] == "stt":  # 人类语音
        human_asr_end_time = time.time()
        logger.info1("human: %s", message["text"])

    elif message["type"] == "tts" and message["state"] == "sentence_start":  # AI语音
        logger.info2("AI: %s", message["text"])

    elif message["type"] == "tts" and message["state"] == "stop":
        # logger.info2("播放结束")
        await asyncio.sleep(0.5)
        device_stauts = "listen"
        logger.info("聆听中...")
    elif message["type"] == "llm":  # 表情
        logger.info3("emotion: %s", message["text"])
    else:  # 其他消息
        pass
        # logger.info("other: %s", message)

    if message["type"] == "websocket" and message["state"] == "close":
        is_end = True


async def play_assistant_audio(
    audio_queue: deque[bytes], enable_audio, input_device_info: dict, output_device_info: dict
):
    """播放音频流"""
    global human_asr_end_time

    stream = None
    if enable_audio:
        stream = sd.OutputStream(
            device=output_device_info["index"],
            # samplerate=sound_device["output"]["samplerate"],
            samplerate=input_device_info["samplerate"],  # 这里使用输入的采样率
            channels=1,
            dtype=np.int16,
        )
        stream.start()

    while True:
        if is_end:
            return

        if not audio_queue:
            await asyncio.sleep(0.01)
            continue

        if human_asr_end_time:
            logger.debug("首个音频包响应时间：%s 秒", time.time() - human_asr_end_time)
            human_asr_end_time = None

        pcm_data = audio_queue.popleft()
        if stream:
            # 将字节数据转换为 numpy int16 数组
            audio_array = np.frombuffer(pcm_data, dtype=np.int16)
            # 应用音量控制
            if volume != 1.0:
                # 应用音量系数，并裁剪到 int16 的有效范围 [-32768, 32767] 以避免失真
                audio_array = np.clip(audio_array * volume, -32768, 32767).astype(np.int16)
            # stream.write() 需要 numpy 数组，而不是字节数据
            stream.write(audio_array)


class XiaoZhiClient:
    """小智客户端类"""

    def __init__(
        self,
        url: Optional[str] = None,
        ota_url: Optional[str] = None,
    ):
        self.xiaozhi: Optional[XiaoZhiWebsocket] = None
        self.url = url
        self.ota_url = ota_url
        self.mac_address = ""

    async def start(
        self,
        mac_address: str,
        serial_number: str,
        license_key: str,
        enable_audio,
        input_device_info: dict,
        output_device_info: dict,
    ) -> bool:
        """启动客户端连接"""
        self.mac_address = mac_address
        self.xiaozhi = XiaoZhiWebsocket(
            handle_message,
            url=self.url,
            ota_url=self.ota_url,
            audio_sample_rate=input_device_info["samplerate"],
        )

        await self.xiaozhi.set_mcp_tool(mcp_tool_func(self.xiaozhi))

        asyncio.create_task(
            play_assistant_audio(self.xiaozhi.output_audio_queue, enable_audio, input_device_info, output_device_info)
        )

        if not await self.xiaozhi.init_connection(
            self.mac_address, serial_number=serial_number, license_key=license_key
        ):
            return False

        return True

    def audio_callback(self, indata, frames, time, status):
        """音频输入回调函数"""
        pcm_data = (indata.flatten() * 32767).astype(np.int16).tobytes()
        input_audio_buffer.append(pcm_data)

    async def process_audio_input(self):
        """处理音频输入"""
        while True:

            if is_end:
                return

            if not input_audio_buffer:
                await asyncio.sleep(0.01)
                continue

            pcm_data = input_audio_buffer.popleft()
            if device_stauts == "listen":
                await self.xiaozhi.send_audio(pcm_data)
            else:
                input_audio_buffer.clear()


async def run_client(
    mac_address: str,
    url: str,
    ota_url: str,
    serial_number: str,
    license_key: str,
    enable_audio: bool,
    wake_word: str,
    input_device_info: dict,
    output_device_info: dict,
):
    """运行客户端的异步函数"""
    logger.debug("Recording... Press Ctrl+C to stop.")
    client = XiaoZhiClient(url, ota_url)
    if not await client.start(
        mac_address, serial_number, license_key, enable_audio, input_device_info, output_device_info
    ):
        return

    # 发送唤醒词
    if wake_word and client.xiaozhi:
        await client.xiaozhi.send_text(wake_word)

    blocksize = input_device_info["samplerate"] * INPUT_AUDIO_FRAME_DURATION // 1000

    with sd.InputStream(
        device=input_device_info["index"],
        callback=client.audio_callback,
        channels=1,
        samplerate=input_device_info["samplerate"],
        blocksize=blocksize,
    ):
        logger.info("聆听中...")
        await client.process_audio_input()


@click.command()
@click.argument("mac_address", required=False)
@click.option("--url", help="服务端websocket地址")
@click.option("--ota_url", help="OTA地址")
@click.option("--serial_number", default="", help="设备的序列号")
@click.option("--license_key", default="", help="设备的授权密钥")
@click.option("--enable_audio", default=True, help="是否开启音频播放")
@click.option("--wake_word", default="", help="唤醒词")
@click.option("--input_device", default=None, type=int, help="输入设备")
@click.option("--output_device", default=None, type=int, help="输出设备")
@click.option("--list_devices", is_flag=True, help="列出所有音频设备")
def main(
    mac_address: str,
    url: str,
    ota_url: str,
    serial_number: str,
    license_key: str,
    enable_audio: bool,
    wake_word: str,
    input_device: int,
    output_device: int,
    list_devices: bool,
):
    """小智SDK客户端

    MAC_ADDRESS: 设备的MAC地址 (格式: XX:XX:XX:XX:XX:XX)
    """
    if list_devices:
        print_audio_devices()
        return

    input_device_id = sd.default.device[0] if input_device is None else input_device
    output_device_id = sd.default.device[1] if output_device is None else output_device
    input_device_info = audio_device_info.get(input_device_id)
    output_device_info = audio_device_info.get(output_device_id)

    if not input_device_info or not input_device_info["is_input"]:
        logger.error("输入设备不存在")
        return

    if not output_device_info or not output_device_info["is_output"]:
        logger.error("输出设备不存在")
        return

    logger.info(f"输入设备: {input_device_info['name']}, 采样率: {input_device_info['samplerate']}")
    logger.info(f"输出设备: {output_device_info['name']}, 采样率: {output_device_info['samplerate']}\n")

    mac_address = mac_address or get_mac_address()
    asyncio.run(
        run_client(
            mac_address,
            url,
            ota_url,
            serial_number,
            license_key,
            enable_audio,
            wake_word,
            input_device_info,
            output_device_info,
        )
    )
