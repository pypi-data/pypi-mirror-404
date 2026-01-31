Tracking module
===============

The Tracking module provides end-to-end pipelines for object detection, ID
stabilisation, flow extraction, and analysis. All commands are exposed under
the ``bee track`` CLI group.

Commands
--------

Run the full pipeline:

.. code-block:: bash

   bee track run-pipeline --input /path/to/video.mp4 --output /path/to/output_dir

Run YOLO detection/tracking and save CSV output:

.. code-block:: bash

   bee track run-yolo --model-path /path/to/model.pt --source-video /path/to/video.mp4 \
     --output-path /path/to/out.csv

Fix object IDs across frames:

.. code-block:: bash

   bee track fix-ids /path/to/tracking.csv --output /path/to/fixed.csv --num-objects 5

Extract flow information (dx/dy/speed):

.. code-block:: bash

   bee track extract-flow /path/to/fixed.csv --output /path/to/flow.csv

Run speed and direction analysis:

.. code-block:: bash

   bee track speed-analysis /path/to/flow.csv --output-dir /path/to/output_dir

Visualise tracks on video:

.. code-block:: bash

   bee track visualise-tracking --video /path/to/video.mp4 --csv /path/to/fixed.csv \
     --out /path/to/annotated.mp4

Batch processing
----------------

A batch-processing command is available. It runs the pipeline
over all videos in a directory tree and writes outputs to per-video subdirectories.

Usage:

.. code-block:: bash

   bee track batch-process --input-dir /path/to/videos
   bee track batch-process --input-dir /path/to/videos --filter hiveA
   bee track batch-process --input-dir /path/to/videos --output-dir-name tracking_outputs

Configuration
-------------

To create editable config files in your working directory:

.. code-block:: bash

   bee config init

This writes:

- ``tracking_config.yaml``
- ``tracking/custom_tracker.yaml``

The CLI will automatically use a ``tracking_config.yaml`` in your current
working directory if present.
