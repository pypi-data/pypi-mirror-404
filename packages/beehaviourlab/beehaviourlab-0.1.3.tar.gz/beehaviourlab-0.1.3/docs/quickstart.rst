Quickstart Guide
================

This guide shows the simplest end-to-end usage of the Tracking pipeline.

Create local config files (optional but recommended if you want to tweak defaults):

.. code-block:: bash

   bee config init

1) Run the tracking pipeline on a video:

.. code-block:: bash

   bee track run-pipeline --input /path/to/video.mp4 --output /path/to/output_dir

2) Inspect the outputs (CSV files) in the output directory:

- ``*_yolo_tracking_raw.csv``: raw detections
- ``*_yolo_tracking_fixed_ids.csv``: detections with stable IDs
- ``*_yolo_tracking_fixed_ids_velocity.csv``: flow and speed metrics

3) Visualise tracks on the source video:

.. code-block:: bash

   bee track visualise-tracking --video /path/to/video.mp4 --csv /path/to/fixed.csv \
     --out /path/to/annotated.mp4

Batch processing
----------------

Batch processing allows you to run the pipeline across all videos in a directory tree.

.. code-block:: bash

   bee track batch-process --input-dir /path/to/videos
   bee track batch-process --input-dir /path/to/videos --output-dir-name tracking_outputs
   bee track batch-process --input-dir /path/to/videos --filter hiveA
