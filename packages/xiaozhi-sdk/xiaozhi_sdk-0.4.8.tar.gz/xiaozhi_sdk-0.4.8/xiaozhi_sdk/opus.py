import av
import numpy as np
import opuslib

from xiaozhi_sdk.config import XIAOZHI_SAMPLE_RATE


class AudioOpus:

    def __init__(self, sample_rate, channels, frame_duration, output_sample_rate=None):
        self.input_frame_duration = frame_duration
        self.input_sample_rate = sample_rate
        self.input_channels = channels
        self.input_frame_size = self.input_sample_rate * self.input_frame_duration // 1000
        self.output_sample_rate = output_sample_rate or sample_rate
        self.outut_frame_size = self.output_sample_rate * self.input_frame_duration // 1000

        # 创建 Opus 编码器
        self.opus_encoder_16k = opuslib.Encoder(
            fs=XIAOZHI_SAMPLE_RATE, channels=1, application=opuslib.APPLICATION_VOIP
        )

        self.output_resampler = av.AudioResampler(format="s16", layout="mono", rate=self.output_sample_rate)
        self.resampler_16k = av.AudioResampler(format="s16", layout="mono", rate=16000)

    def set_out_audio_frame(self, audio_params):
        # 小智服务端 的 音频信息
        self.xiaozhi_out_sample_rate = audio_params["sample_rate"]
        self.xiaozhi_out_frame_size = self.xiaozhi_out_sample_rate * audio_params["frame_duration"] // 1000

        # 创建 Opus 解码器
        self.opus_decoder = opuslib.Decoder(
            fs=self.xiaozhi_out_sample_rate,  # 采样率
            channels=audio_params["channels"],  # 单声道
        )

    def to_16k_samplerate_pcm(self, pcm_array):
        layout = "mono" if self.input_channels == 1 else "stereo"
        frame = av.AudioFrame.from_ndarray(pcm_array.reshape(1, -1), format="s16", layout=layout)
        frame.sample_rate = self.input_sample_rate
        resampled_frames = self.resampler_16k.resample(frame)
        samples = resampled_frames[0].to_ndarray().flatten()
        return samples

    def to_16k_pcm(self, pcm):
        pcm_array = np.frombuffer(pcm, dtype=np.int16)
        pcm_array = self.to_16k_samplerate_pcm(pcm_array)
        pcm_bytes = pcm_array.tobytes()
        return pcm_bytes

    async def pcm_to_opus(self, pcm):
        pcm_array = np.frombuffer(pcm, dtype=np.int16)
        pcm_bytes = pcm_array.tobytes()
        if self.input_sample_rate != XIAOZHI_SAMPLE_RATE:
            # 小智服务端仅支持 16000 采样率， 将 pcm_array 转 16k 采样率
            pcm_array = self.to_16k_samplerate_pcm(pcm_array)
            pcm_bytes = pcm_array.tobytes()

        frame_size = XIAOZHI_SAMPLE_RATE * self.input_frame_duration // 1000
        return self.opus_encoder_16k.encode(pcm_bytes, frame_size)

    async def change_sample_rate(self, pcm_array) -> np.ndarray:
        # 采样率 变更
        frame = av.AudioFrame.from_ndarray(np.array(pcm_array).reshape(1, -1), format="s16", layout="mono")
        frame.sample_rate = self.xiaozhi_out_sample_rate
        resampled_frames = self.output_resampler.resample(frame)
        samples = resampled_frames[0].to_ndarray().flatten()
        return samples

    def padding(self, samples):
        # 不足 self.frame_size 补 0
        samples_padded = np.pad(samples, (0, self.outut_frame_size - samples.size), mode="constant", constant_values=0)
        return samples_padded.reshape(1, self.outut_frame_size)

    async def opus_to_pcm(self, opus) -> np.ndarray:
        pcm_data = self.opus_decoder.decode(opus, frame_size=self.xiaozhi_out_frame_size)
        pcm_array = np.frombuffer(pcm_data, dtype=np.int16)
        if self.input_sample_rate != self.xiaozhi_out_sample_rate:
            pcm_array = await self.change_sample_rate(pcm_array)

        pcm_array = self.padding(pcm_array)
        return pcm_array
