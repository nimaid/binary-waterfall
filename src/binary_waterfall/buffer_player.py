import numpy as np
import sounddevice as sd

UINT8_MIDPOINT = 1 << 7
INT16_SIGN_BIT = 1 << 15
INT24_SIGN_BIT = 1 << 23
INT24_MODULUS = 1 << 24
INT32_SIGN_BIT = 1 << 31

def pcm_bytes_to_float32(raw, sample_bytes, num_channels):
    raw = bytes(raw)
    bytes_per_frame = sample_bytes * num_channels
    if bytes_per_frame <= 0 or len(raw) < bytes_per_frame:
        return np.zeros((0, max(num_channels, 1)), dtype=np.float32)

    # throw tail away if not a multiple of the frame size
    usable = len(raw) - (len(raw) % bytes_per_frame)
    raw = raw[:usable]
    frames = usable // bytes_per_frame

    # convert int to float in range of -1.0 to 1.0
    if sample_bytes == 1:
        samples = np.frombuffer(raw, dtype=np.uint8).astype(np.float32)
        samples = (samples - UINT8_MIDPOINT) / float(UINT8_MIDPOINT)
    elif sample_bytes == 2:
        samples = np.frombuffer(raw, dtype="<i2").astype(np.float32) / float(INT16_SIGN_BIT)
    elif sample_bytes == 3:
        # due to lack of int24 / <i3 we build samples by hand
        packed = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 3)
        values = (
            packed[:, 0].astype(np.int32)
            | (packed[:, 1].astype(np.int32) << 8)
            | (packed[:, 2].astype(np.int32) << 16)
        )
        values = np.where(values >= INT24_SIGN_BIT, values - INT24_MODULUS, values)
        samples = values.astype(np.float32) / float(INT24_SIGN_BIT)
    elif sample_bytes == 4:
        samples = np.frombuffer(raw, dtype="<i4").astype(np.float32) / float(INT32_SIGN_BIT)
    else:
        raise ValueError(f"Unsupported sample width: {sample_bytes} bytes")

    np.clip(samples, -1.0, 1.0, out=samples)
    return samples.reshape(frames, num_channels)

class BufferPlayer:
    def __init__(self, obtain_data_cb, samplerate=32000, channels=1, blocksize=1024):
        self.obtain_data = obtain_data_cb
        self.is_playing = False
        self._gain = 1.0
        self.stream = sd.OutputStream(
            samplerate=samplerate,
            channels=channels,
            dtype="float32",
            callback=self._callback,
            blocksize=blocksize,
        )

    def _callback(self, outdata, frames, time, status):
        outdata.fill(0)
        data = self.obtain_data(frames)

        if data is None:
            return

        if data.ndim == 1:
            data = data.reshape(-1, 1)

        if data.shape != outdata.shape:
            raise ValueError(
                f"Audio chunk shape {data.shape} does not match stream {outdata.shape}"
            )

        if self._gain != 1.0:
            data = data * np.float32(self._gain)

        np.clip(data, -1.0, 1.0, out=data)
        outdata[:] = data

    def setVolume(self, volume):
        self._gain = volume / 100

    def update_stream_safe(self, sample_rate, num_channels, block_size=None):
        if block_size is None:
            block_size = self.stream.blocksize

        was_playing = self.is_playing
        self.stop()
        self.stream.close()
        self.stream = sd.OutputStream(
            samplerate=sample_rate,
            channels=num_channels,
            dtype="float32",
            callback=self._callback,
            blocksize=block_size,
        )

        if was_playing:
            self.start()

    def start(self):
        if self.is_playing or self.stream is None:
            return
        self.stream.start()
        self.is_playing = True

    def stop(self):
        if self.stream is None or not self.is_playing:
            return
        self.stream.stop()
        self.is_playing = False

    def close(self):
        self.stop()
        if self.stream is not None:
            self.stream.close()
            self.stream = None
