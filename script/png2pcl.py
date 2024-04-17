import cv2
import numpy as np
import open3d as o3d
import argparse

def generate_pointcloud(input_file, output_file, x_meter, y_meter, z_meter, interval):
    # 画像を読み込む
    image = cv2.imread(input_file, cv2.IMREAD_UNCHANGED)
    height, width, channels = image.shape

    # ポイントクラウドのデータを格納する配列
    points = []
    colors = []

    # 画像データを走査してポイントクラウドを生成する
    y = 0
    while y < height:
        x = 0
        while x < width:
            # 色情報を取得（アルファチャンネルを無視する）
            bgr_color = image[int(y), int(x)][:3]  # BGR形式で色を取得
            # BGRからRGBへ変換
            rgb_color = bgr_color[::-1]  # 配列を反転させてRGBに変換
            # y座標を反転させる
            y_inverted = height - y
            # ポイントクラウドに点を追加
            points.append([x / width * x_meter, y_inverted / height * y_meter, z_meter])
            colors.append(rgb_color)
            x += interval * width / x_meter
        y += interval * height / y_meter

    # numpy配列に変換
    points = np.array(points)
    colors = np.array(colors) / 255.0  # open3dでは色情報が0から1の範囲である必要がある

    # open3dのPointCloudオブジェクトを作成
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(points)
    pcd.colors = o3d.utility.Vector3dVector(colors)

    # PCD形式で保存
    o3d.io.write_point_cloud(output_file, pcd)

# コマンドライン引数を解析する
parser = argparse.ArgumentParser(description="Generate a point cloud from a PNG image.")
parser.add_argument("input_file", type=str, help="Input PNG image file.")
parser.add_argument("output_file", type=str, help="Output PCD file.")
parser.add_argument("--x_meter", type=float, default=100, help="Width of the area in meters. Default is 100.")
parser.add_argument("--y_meter", type=float, default=100, help="Height of the area in meters. Default is 100.")
parser.add_argument("--z_meter", type=float, default=0, help="Base height of the point cloud in meters. Default is 0.")
parser.add_argument("--interval", type=float, default=1, help="Interval between points in meters. Default is 1.")

# 引数を解析する
args = parser.parse_args()

# スクリプトを実行
generate_pointcloud(args.input_file, args.output_file, args.x_meter, args.y_meter, args.z_meter, args.interval)
