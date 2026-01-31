# BEEhaviourLab

[![tests](https://github.com/BEEhaviourLab/BEEhaviourLab/actions/workflows/tests.yml/badge.svg)](https://github.com/BEEhaviourLab/BEEhaviourLab/actions/workflows/tests.yml)

BEEhaviourLab provides tools for detecting, tracking, and analysing bee behaviour from video data.

Documentation
-------------
Full documentation is published on GitHub Pages:
https://beehaviourlab.github.io/BEEhaviourLab/

Installation
------------
Install from PyPI:

```
pip install beehaviourlab
```

Install with docs or test extras:

```
pip install "beehaviourlab[docs]"
pip install "beehaviourlab[test]"
```

Install with dev extras (docs + tests):

```
pip install "beehaviourlab[dev]"
```

Install from source (recommended for development):

```
pip install -e .
```

For docs tooling:

```
pip install -e ".[docs]"
```

Tracking module
---------------
All tracking commands are available under the `bee track` group.

Common commands:

```
bee track run-pipeline --input /path/to/video.mp4 --output /path/to/output_dir
bee track run-yolo --model-path /path/to/model.pt --source-video /path/to/video.mp4 --output-path /path/to/out.csv
bee track fix-ids /path/to/tracking.csv --output /path/to/fixed.csv --num-objects 5
bee track extract-flow /path/to/fixed.csv --output /path/to/flow.csv
bee track speed-analysis /path/to/flow.csv --output-dir /path/to/output_dir
bee track visualise-tracking --video /path/to/video.mp4 --csv /path/to/fixed.csv --out /path/to/annotated.mp4
```

Batch processing
----------------
There is also a batch-processing command for running the tracking pipeline over all videos in a
directory tree and writing outputs into a per-video subdirectory.

Usage:

```
bee track batch-process --input-dir /path/to/videos
bee track batch-process --input-dir /path/to/videos --filter hiveA
bee track batch-process --input-dir /path/to/videos --output-dir-name tracking_outputs
```

Configuration
-------------
To create editable config files in your working directory:

```
bee config init
```

This writes:
- `tracking_config.yaml`
- `tracking/custom_tracker.yaml`

The CLI will automatically use a `tracking_config.yaml` in your current working
directory if present.
