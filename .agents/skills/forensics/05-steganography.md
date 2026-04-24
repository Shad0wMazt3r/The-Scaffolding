## Steganography

- Primary Probe
  - * -> [Condition: Carrier is an image or audio file] -> Action: start with `file`, `exiftool`, `binwalk`, `strings`, and `steghide info`; then inspect dimensions, channels, palette, compression, and metadata for contradictions. Steghide exposes `info` and `extract` for candidate stego files. [manpages.ubuntu](https://manpages.ubuntu.com/manpages/trusty/man1/steghide.1.html)
  - * -> [Condition: Carrier is PNG or BMP] -> Action: run `zsteg -a` first, then inspect per-channel bit planes, alpha channel, palette ordering, and trailing bytes. `zsteg` is designed to detect hidden data in PNG and BMP, and installs via RubyGems.
  - * -> [Condition: Carrier is JPEG or audio] -> Action: favor metadata, binwalk, appended payload checks, quantization/DCT anomalies, and spectrogram analysis over naive LSB assumptions.

- Dead End Pivots
  - * -> [Condition: Steghide/binwalk returns nothing] -> Action: check for appended archives, trailing ZIP/RAR headers, split payloads across multiple carriers, and entropy spikes in footer or comment segments.
  - * -> [Condition: Visible image looks normal and LSB tools fail] -> Action: inspect individual RGB/A bit planes, palette index ordering, Unicode whitespace in companion text, and filename/EXIF comments as covert channels.
  - * -> [Condition: JPEG challenge implies frequency-domain hiding] -> Action: compare DCT coefficient distributions, quantization tables, restart markers, and recompression artifacts; treat social-media recompression clues as part of the puzzle.

- Data Chaining
  - * -> [Condition: Extracted payload is an archive, script, or key] -> Action: pass it to file-format analysis, password testing, and memory/disk correlation.
  - * -> [Condition: EXIF/comment fields contain coordinates, timestamps, or tool names] -> Action: pivot into logs, browser history, or challenge infrastructure naming patterns.
  - * -> [Condition: Multi-image set shares near-identical visuals] -> Action: diff pixels, palettes, or audio phase against the entire set; CTF authors often shard flags across “almost identical” files.

- Simple one-liners
  - `steghide info raw/carrier.jpg`
  - `zsteg -a raw/carrier.png > stego/zsteg_all.txt`
  - `python3 -c "from PIL import Image;import numpy as np;im=np.array(Image.open('raw/carrier.png'));Image.fromarray(((im[:,:,0]&1)*255).astype('uint8')).save('stego/r_lsb.png')"`

- Script Definition Block: JPEG DCT anomaly scanner
  - Input Data: JPEG carrier set, optional known-clean comparison set.
  - Core Processing Logic:
    - Parse quantization tables and coefficient histograms by block and channel.
    - Detect biased low-frequency/AC distributions inconsistent with natural recompression.
    - Compare coefficient populations across sibling images for sharded embedding.
    - Export suspicious block coordinates and channel-level heatmaps.
  - Dependencies: JPEG parser, numpy/scipy, visualization helper.
  - Expected Output Format: CSV `file,channel,block_x,block_y,score` plus PNG heatmaps.

