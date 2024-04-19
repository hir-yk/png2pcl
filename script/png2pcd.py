import cv2
import numpy as np
import open3d as o3d
import argparse

def read_image(input_file):
    return cv2.imread(input_file, cv2.IMREAD_UNCHANGED)

def convert_bgr_to_rgb(bgr_color):
    return bgr_color[::-1]

def generate_pointcloud(image, x_meter, y_meter, z_meter, interval, offset_x, offset_y):
    height, width, _ = image.shape
    points = []
    colors = []

    for y in np.arange(0, height, interval * height / y_meter):
        for x in np.arange(0, width, interval * width / x_meter):
            bgr_color = image[int(y), int(x), :3]
            rgb_color = convert_bgr_to_rgb(bgr_color)
            y_inverted = height - y
            points.append([
                (x / width * x_meter) + offset_x,  # オフセット値を足す
                (y_inverted / height * y_meter) + offset_y,  # オフセット値を足す
                z_meter
            ])
            colors.append(rgb_color / 255.0)

    return np.array(points), np.array(colors)

def create_point_cloud(points, colors):
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(points)
    pcd.colors = o3d.utility.Vector3dVector(colors)
    return pcd

def save_point_cloud(pcd, output_file):
    o3d.io.write_point_cloud(output_file, pcd)

def parse_arguments():
    parser = argparse.ArgumentParser(description="Generate a point cloud from a PNG image.")
    parser.add_argument("input_file", type=str, help="Input PNG image file.")
    parser.add_argument("output_file", type=str, help="Output PCD file.")
    parser.add_argument("--x_meter", type=float, default=100, help="Width of the area in meters. Default is 100.")
    parser.add_argument("--y_meter", type=float, default=100, help="Height of the area in meters. Default is 100.")
    parser.add_argument("--z_meter", type=float, default=0, help="Base height of the point cloud in meters. Default is 0.")
    parser.add_argument("--interval", type=float, default=1, help="Interval between points in meters. Default is 1.")
    parser.add_argument("--offset_x", type=float, default=0, help="Offset for the x coordinate in meters. Default is 0.")
    parser.add_argument("--offset_y", type=float, default=0, help="Offset for the y coordinate in meters. Default is 0.")
    return parser.parse_args()

def main():
    args = parse_arguments()
    image = read_image(args.input_file)
    points, colors = generate_pointcloud(image, args.x_meter, args.y_meter, args.z_meter, args.interval, args.offset_x, args.offset_y)
    pcd = create_point_cloud(points, colors)
    save_point_cloud(pcd, args.output_file)

if __name__ == "__main__":
    main()
