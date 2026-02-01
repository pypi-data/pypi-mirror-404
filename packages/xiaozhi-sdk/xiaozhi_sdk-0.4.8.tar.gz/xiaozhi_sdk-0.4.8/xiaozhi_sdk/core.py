import asyncio
import json
import logging
import re
import uuid
from collections import deque
from typing import Any, Callable, Deque, Dict, Optional

import websockets

from xiaozhi_sdk.config import (
    INPUT_AUDIO_CHANNELS,
    INPUT_AUDIO_FRAME_DURATION,
    INPUT_AUDIO_SAMPLE_RATE,
    XIAOZHI_SAMPLE_RATE,
)
from xiaozhi_sdk.iot import OtaDevice
from xiaozhi_sdk.mcp import McpTool
from xiaozhi_sdk.utils import setup_opus

setup_opus()
from xiaozhi_sdk.opus import AudioOpus

logger = logging.getLogger("xiaozhi_sdk")


class XiaoZhiWebsocket(McpTool):

    def __init__(
        self,
        message_handler_callback: Optional[Callable] = None,
        url: Optional[str] = None,
        ota_url: Optional[str] = None,
        audio_sample_rate: int = INPUT_AUDIO_SAMPLE_RATE,
        audio_channels: int = INPUT_AUDIO_CHANNELS,
        audio_frame_duration=INPUT_AUDIO_FRAME_DURATION,
        audio_format="opus",
        audio_output_sample_rate: int | None = None,
    ):
        super().__init__()
        self.url = url
        self.ota_url = ota_url
        self.audio_channels = audio_channels
        self.audio_frame_duration = audio_frame_duration
        self.audio_opus = AudioOpus(audio_sample_rate, audio_channels, audio_frame_duration, audio_output_sample_rate)
        self.audio_format = audio_format
        # 客户端标识
        self.client_id = str(uuid.uuid4())
        self.mac_addr: Optional[str] = None
        self.websocket_token = ""

        # 回调函数
        self.message_handler_callback = message_handler_callback

        # 连接状态
        self.hello_received = asyncio.Event()
        self.session_id = ""
        self.websocket = None
        self.message_handler_task: Optional[asyncio.Task] = None

        # 输出音频
        self.output_audio_queue: Deque[bytes] = deque()
        self.is_playing: bool = False

        # OTA设备
        self.ota: Optional[OtaDevice] = None
        self.iot_task: Optional[asyncio.Task] = None
        self.wait_device_activated: bool = False

        # mcp工具
        self.mcp_tool_dict = {}

    async def _send_hello(self) -> None:
        """发送hello消息"""
        hello_message = {
            "type": "hello",
            "version": 1,
            "features": {"mcp": True, "consistent_sample_rate": False},
            "transport": "websocket",
            "audio_params": {
                "format": self.audio_format,
                "sample_rate": XIAOZHI_SAMPLE_RATE,
                "channels": 1,
                "frame_duration": self.audio_opus.input_frame_duration,
            },
        }
        await self.websocket.send(json.dumps(hello_message))
        await asyncio.wait_for(self.hello_received.wait(), timeout=10.0)

    async def _start_listen(self) -> None:
        """开始监听"""
        listen_message = {"session_id": self.session_id, "type": "listen", "state": "start", "mode": "realtime"}
        await self.websocket.send(json.dumps(listen_message))

    async def is_activate(self, ota_info):
        """是否激活"""
        if ota_info.get("activation"):
            return False

        return True

    async def _activate_iot_device(self, license_key: str, ota_info: Dict[str, Any]) -> None:
        """激活IoT设备"""
        if not self.ota:
            return

        challenge = ota_info["activation"]["challenge"]
        await asyncio.sleep(3)
        self.wait_device_activated = True
        for _ in range(10):
            if self.websocket:
                await self.send_text("hi")

            if await self.ota.check_activate(challenge, license_key):
                await self.websocket.close()
                await self.connect_websocket(self.websocket_token)
                await self.send_text("hi")
                self.wait_device_activated = False
                break

            await asyncio.sleep(3)

    # async def _send_demo_audio(self) -> None:
    #     """发送演示音频"""
    #     current_dir = os.path.dirname(os.path.abspath(__file__))
    #     wav_path = os.path.join(current_dir, "../file/audio/16k_greet.wav")
    #     framerate, channels = get_wav_info(wav_path)
    #     audio_opus = AudioOpus(framerate, channels, self.audio_frame_duration)
    #
    #     for pcm_data in read_audio_file(wav_path, 16000, self.audio_frame_duration):
    #         opus_data = await audio_opus.pcm_to_opus(pcm_data)
    #         await self.websocket.send(opus_data)
    #     await self.send_silence_audio()

    async def send_abort(self):
        await self.websocket.send(json.dumps({"session_id": self.session_id, "type": "abort", "reason": ""}))

    async def send_wake_word(self, wake_word: str) -> bool:
        """发送唤醒词"""
        return await self.send_text(wake_word)

    async def send_text(self, content: str) -> bool:
        """发送文本"""
        try:
            await self.websocket.send(
                json.dumps({"session_id": self.session_id, "type": "listen", "state": "detect", "text": content})
            )
            return True
        except websockets.ConnectionClosed:
            if self.message_handler_callback and not self.wait_device_activated:
                await self.message_handler_callback(
                    {"type": "websocket", "state": "close", "source": "sdk.send_wake_word"}
                )
            logger.debug("[websocket] close")
            return False

    async def send_silence_audio(self, duration_seconds: float = 1.2) -> None:
        """发送静音音频"""
        frames_count = int(duration_seconds * 1000 / self.audio_opus.input_frame_duration)
        pcm_frame = b"\x00\x00" * int(self.audio_opus.input_sample_rate / 1000 * self.audio_opus.input_frame_duration)

        for _ in range(frames_count):
            await self.send_audio(pcm_frame)

    async def _handle_websocket_message(self, message: Any) -> None:
        """处理接受到的WebSocket消息"""

        # audio data
        if isinstance(message, bytes):
            try:
                pcm_array = await self.audio_opus.opus_to_pcm(message)
                self.output_audio_queue.extend(pcm_array)
            except Exception as e:
                logger.error("opus_to_pcm error: %s", e)
            return

        # json message
        data = json.loads(message)
        message_type = data["type"]
        if message_type == "hello":
            self.audio_opus.set_out_audio_frame(data["audio_params"])
            self.hello_received.set()
            self.session_id = data["session_id"]
            return
        elif message_type == "mcp":
            await self.mcp(data)
            return

        # 转发其他 message_type
        if self.message_handler_callback:
            try:
                await self.message_handler_callback(data)
            except Exception as e:
                logger.error("message_handler_callback error: %s", e)

            if message_type == "tts":
                if data["state"] == "sentence_start":
                    self.is_playing = True
                else:
                    self.is_playing = False
        else:
            logger.warning("未定义回调函数 %s", data)

    async def _message_handler(self) -> None:
        """消息处理器"""
        try:
            async for message in self.websocket:
                try:
                    await self._handle_websocket_message(message)
                except Exception as e:
                    logger.error("message_handler error: %s", e)
        finally:
            if self.message_handler_callback and not self.wait_device_activated:
                if self.websocket:
                    await self.message_handler_callback(
                        {"type": "websocket", "state": "close", "source": "sdk.message_handler"}
                    )
            logger.debug("[websocket] close")

    async def set_mcp_tool(self, mcp_tool_list) -> None:
        """设置MCP工具"""
        for mcp_tool in mcp_tool_list:
            self.mcp_tool_dict[mcp_tool["name"]] = mcp_tool

    async def connect_websocket(self, websocket_token) -> bool:
        """连接websocket"""
        headers = {
            "Authorization": "Bearer {}".format(websocket_token),
            "Protocol-Version": "1",
            "Device-Id": self.mac_addr,
            "Client-Id": self.client_id,
        }
        try:
            self.websocket = await websockets.connect(uri=self.url, additional_headers=headers, open_timeout=5)
        except websockets.exceptions.InvalidMessage as e:
            logger.error("[websocket] 连接失败，请检查网络连接或设备状态。当前链接地址: %s, 错误信息：%s", self.url, e)
            return False
        except Exception as e:
            logger.error("[websocket] 连接失败，请检查网络连接或设备状态。当前链接地址: %s, 错误信息：%s", self.url, e)
            return False

        self.message_handler_task = asyncio.create_task(self._message_handler())
        await self._send_hello()
        await self._start_listen()
        logger.debug("[websocket] Connection successful. mac_addr: %s", self.mac_addr)
        await asyncio.sleep(0.5)
        return True

    async def init_connection(self, mac_addr: str, serial_number: str = "", license_key: str = "") -> bool:
        """初始化连接"""
        mac_pattern = r"^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$"
        if not re.match(mac_pattern, mac_addr):
            raise ValueError(f"无效的MAC地址格式: {mac_addr}。正确格式应为 XX:XX:XX:XX:XX:XX")

        self.mac_addr = mac_addr.lower()

        if not self.url or self.ota_url:
            self.ota = OtaDevice(self.mac_addr, self.client_id, self.ota_url, serial_number)
            ota_info = await self.ota.activate_device()
            self.websocket_token = ota_info["websocket"]["token"]
            ws_url = ota_info.get("websocket", {}).get("url")
            self.url = self.url or ws_url

            if not await self.is_activate(ota_info):
                self.iot_task = asyncio.create_task(self._activate_iot_device(license_key, ota_info))
                logger.debug("[IOT] 设备未激活")

        if not self.url:
            logger.warning("[websocket] 未找到websocket链接地址")
            return False

        if "tenclass.net" not in self.url and "xiaozhi.me" not in self.url:
            logger.warning("[websocket] 检测到非官方服务器，当前链接地址: %s", self.url)

        if not await self.connect_websocket(self.websocket_token):
            return False

        return True

    async def send_audio(self, pcm: bytes) -> bool:
        """发送音频数据"""
        if not self.websocket:
            return False

        state = self.websocket.state
        if state == websockets.protocol.State.OPEN:
            if self.audio_format == "opus":
                opus_data = await self.audio_opus.pcm_to_opus(pcm)
                await self.websocket.send(opus_data)
            else:
                pcm16k = self.audio_opus.to_16k_pcm(pcm)
                await self.websocket.send(pcm16k)

            return True
        elif state in [websockets.protocol.State.CLOSED, websockets.protocol.State.CLOSING]:
            if self.wait_device_activated:
                logger.debug("[websocket] Server actively disconnected, reconnecting...")
            elif self.message_handler_callback:
                pass
                # if self.websocket:
                #     await self.message_handler_callback({"type": "websocket", "state": "close", "source": "sdk.send_audio"})
                #     self.websocket = None
                #     logger.debug("[websocket] Server actively disconnected")

            await asyncio.sleep(0.5)
            return False
        else:
            await asyncio.sleep(0.1)
            return False

    async def close(self) -> None:
        """关闭连接"""
        if self.message_handler_task and not self.message_handler_task.done():
            self.message_handler_task.cancel()
            try:
                await self.message_handler_task
            except asyncio.CancelledError:
                pass

        if self.iot_task:
            self.iot_task.cancel()

        if self.websocket:
            await self.websocket.close()
