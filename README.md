# png2pcl
Convert PNG format image files to PCL


```
usage: png_to_3d_pointcloud.py [-h] [--x_meter X_METER] [--y_meter Y_METER] [--z_meter Z_METER] [--interval INTERVAL]
                               input_file output_file

Generate a point cloud from a PNG image.

positional arguments:
  input_file           Input PNG image file.
  output_file          Output PCD file.

options:
  -h, --help           show this help message and exit
  --x_meter X_METER    Width of the area in meters. Default is 100.
  --y_meter Y_METER    Height of the area in meters. Default is 100.
  --z_meter Z_METER    Base height of the point cloud in meters. Default is 0.
  --interval INTERVAL  Interval between points in meters. Default is 1.
```
