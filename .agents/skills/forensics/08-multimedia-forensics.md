## Multimedia Forensics

- Primary Probe
  - * -> [Condition: Audio file is present] -> Action: inspect metadata, convert to spectrogram, listen for channel imbalance/reversal, and test for appended archives or SSTV/DTMF/Morse-like encodings.
  - * -> [Condition: Video file is present] -> Action: extract frames, thumbnails, subtitles, audio tracks, and container metadata; check for single-frame inserts, QR flashes, or timing-encoded content.
  - * -> [Condition: Photo set is present] -> Action: review EXIF, geotags, orientation inconsistencies, camera serials, and sensor-pattern continuity across the set.

- Dead End Pivots
  - * -> [Condition: Nothing obvious appears in playback] -> Action: analyze individual channels, reverse playback, slow down timing, and inspect frame deltas or hidden subtitle/data tracks.
  - * -> [Condition: EXIF is stripped] -> Action: compare file naming, thumbnails, JPEG quant tables, maker-note remnants, and edit history indicators.
  - * -> [Condition: Multiple files look near-duplicate] -> Action: run image/video differencing and audio subtraction; CTF flags often live in differences, not absolute content.

- Data Chaining
  - * -> [Condition: Spectrogram or frame yields text/QR/key] -> Action: send it to cryptographic recovery or file-format analysis immediately.
  - * -> [Condition: Geolocation or clock data appears] -> Action: align it with logins, transfers, and filesystem events in the global timeline.
  - * -> [Condition: Camera fingerprint or editing signature emerges] -> Action: use it to cluster authentic vs tampered files and isolate the carrier that matters.

- Simple one-liners
  - `ffmpeg -i raw/audio.wav -lavfi showspectrumpic=s=1920x1080 stego/spectrogram.png`
  - `ffmpeg -i raw/video.mp4 -vf fps=1 stego/frames/frame_%05d.png`
  - `exiftool -a -u -g1 raw/mediafile > stego/exif_full.txt`

