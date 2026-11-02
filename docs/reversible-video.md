# Reversible Video Export

Binary Waterfall can export a Matroska (MKV) video containing
the visible waterfall animation, audio, and a lossless FFV1
stream holding the original input bytes.

## Export

1. Open an input file.
2. Select **Export → Video**.
3. Enable **Include original file for recovery**.
4. Choose the **MKV Reversible** file format.
5. Export the video.

The application verifies that the exported MKV can reproduce
the input exactly before publishing the completed file.

## Recovery

Use **File → Recover Original File** and select a compatible
reversible MKV. Select a safe destination for the recovered file.

The decoder validates the embedded recovery header and SHA-256
checksum. If validation fails, the operation must not publish
an incomplete recovered file.

## Privacy and security

**A reversible MKV contains the entire original file.**

Anyone with access to the video may recover that file, including
private or confidential information it contains.

Only share reversible videos when you are comfortable sharing
the complete input file.

Renaming the video, hiding the recovery stream, or using a
regular media player does not protect the embedded information.

## Compatibility

Reversible recovery is supported for MKV files created with
Binary Waterfall's compatible FFV1 recovery format.

Regular MP4, AVI, and ordinary MKV exports do not necessarily
contain recoverable input data.

Do not expect recovery from transcoded, resized, edited, or
otherwise modified videos. Exact recovery requires the original
lossless recovery stream to remain intact.
