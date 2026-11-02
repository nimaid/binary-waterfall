"""PCM byte-order conversion."""


def convert_pcm_byte_order(data, sample_bytes, byte_order):
    if sample_bytes not in (1, 2, 3, 4):
        raise ValueError("Invalid sample width")

    if byte_order not in ("little", "big"):
        raise ValueError("Invalid byte order")

    complete = len(data) // sample_bytes * sample_bytes
    samples = data[:complete]
    remainder = data[complete:]

    if byte_order == "big" and sample_bytes > 1:
        samples = b"".join(
            samples[i:i + sample_bytes][::-1]
            for i in range(0, len(samples), sample_bytes)
        )

    return samples, remainder
