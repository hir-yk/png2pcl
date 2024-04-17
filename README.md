# png2pcl

This Python script converts a PNG image of an aerial photograph into a 3D point cloud in PCD format. The script allows users to specify the real-world dimensions of the image in meters and the desired interval between points.

## Features

- Converts PNG images to colored 3D point clouds.
- Allows specification of image width and height in meters.
- Allows specification of the base height of the point cloud in meters.
- Allows specification of the interval between points in meters.
- Outputs the point cloud in PCD format.

## Prerequisites

Before running this script, you must have the following packages installed:

- OpenCV
- NumPy
- Open3D

You can install these packages using `pip`:

```
bash pip install opencv-python numpy open3d
```

## Usage

To use the script, run it from the command line with the required arguments. Here is an example command:

```
python3 png_to_3d_pointcloud.py input.png output.pcd --x_meter 200 --y_meter 150 --interval 0.5
```

### Command-Line Arguments

- `input_file`: The input PNG image file.
- `output_file`: The output PCD file.
- `--x_meter` (optional): The width of the area in meters. Default is 100.
- `--y_meter` (optional): The height of the area in meters. Default is 100.
- `--z_meter` (optional): The base height of the point cloud in meters. Default is 0.
- `--interval` (optional): The interval between points in meters. Default is 1.

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.
