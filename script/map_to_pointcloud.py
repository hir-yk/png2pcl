import requests
import yaml
import argparse
from PIL import Image
from io import BytesIO
import subprocess
import os
import math

# Haversine公式を使用して2点間の距離を計算する関数
def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  # 地球の半径（メートル）
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    return distance

# 緯度経度から画像の縦横比を計算し、sizeパラメータを設定する関数
def calculate_image_size(top_left_lat, top_left_lng, bottom_right_lat, bottom_right_lng, max_size=640):
    # 縦と横の距離を計算
    width = haversine(top_left_lat, top_left_lng, top_left_lat, bottom_right_lng)
    height = haversine(top_left_lat, top_left_lng, bottom_right_lat, top_left_lng)
    
    # 縦横比を計算
    aspect_ratio = width / height
    
    # Google Maps APIの最大サイズに合わせて画像サイズを計算
    if aspect_ratio >= 1:
        # 横長の場合
        image_width = max_size
        image_height = int(max_size / aspect_ratio)
    else:
        # 縦長の場合
        image_height = max_size
        image_width = int(max_size * aspect_ratio)
    
    # 画像サイズを返す
    return f"{image_width}x{image_height}"
    
# コマンドライン引数を解析する
parser = argparse.ArgumentParser(description="Generate a point cloud from a specified area using Google Maps API.")
parser.add_argument("top_left_lat", type=float, help="Latitude of the top left corner of the area.")
parser.add_argument("top_left_lng", type=float, help="Longitude of the top left corner of the area.")
parser.add_argument("bottom_right_lat", type=float, help="Latitude of the bottom right corner of the area.")
parser.add_argument("bottom_right_lng", type=float, help="Longitude of the bottom right corner of the area.")
parser.add_argument("--output_file", type=str, default="output.pcd", help="Output PCD file name. Default is 'output.pcd'.")
parser.add_argument("--interval", type=float, default=1.0, help="Interval between points in meters. Default is 1.0.")
args = parser.parse_args()

# Google Maps Static APIのエンドポイントとAPIキー
MAPS_API_ENDPOINT = "https://maps.googleapis.com/maps/api/staticmap"
API_KEY = "YOUR_API_KEY"

# 緯度経度から画像を取得する関数
def get_map_image(top_left_lat, top_left_lng, bottom_right_lat, bottom_right_lng, zoom, api_key, size):
    # パラメータの設定
    params = {
        "size": size,  # 計算された画像のサイズ
        "maptype": "roadmap",  # 地図のタイプ
        "key": api_key,
        "center": f"{(top_left_lat + bottom_right_lat) / 2},{(top_left_lng + bottom_right_lng) / 2}",
        "zoom": zoom
    }
    
    # Google Maps Static APIにリクエストを送信
    response = requests.get(MAPS_API_ENDPOINT, params=params)
    if response.status_code == 200:
        # 画像を取得してPIL Imageオブジェクトに変換
        image = Image.open(BytesIO(response.content))
        return image
    else:
        raise Exception(f"Failed to retrieve map image: {response.content}")

# 画像と情報をYAMLファイルに保存する関数
def save_image_and_info(image, width_meter, height_meter, top_left_lat, top_left_lng, bottom_right_lat, bottom_right_lng, yaml_file):
    # 画像をPNG形式で保存
    image_file = "map_image.png"
    image.save(image_file)
    
    # 情報をYAMLファイルに保存
    info = {
        "image_file": image_file,
        "width_meter": width_meter,
        "height_meter": height_meter,
        "top_left": {
            "latitude": top_left_lat,
            "longitude": top_left_lng
        },
        "bottom_right": {
            "latitude": bottom_right_lat,
            "longitude": bottom_right_lng
        }
    }
    with open(yaml_file, "w") as f:
        yaml.dump(info, f)

    return image_file

# PNG画像からPCLを生成する関数
def generate_pcl_from_png(png_file, output_pcd, x_meter, y_meter, interval):
    # png2pcl.pyスクリプトを呼び出してPCLを生成
    subprocess.run(["python3", "png2pcl.py", png_file, output_pcd, "--x_meter", str(x_meter), "--y_meter", str(y_meter), "--interval", str(interval)])

def calculate_zoom_level(top_left_lat, top_left_lng, bottom_right_lat, bottom_right_lng, map_width, map_height):
    # 地球の半径（メートル）
    R = 6378137
    
    # 緯度の差の絶対値
    lat_diff = abs(top_left_lat - bottom_right_lat)
    
    # 経度の差の絶対値
    lng_diff = abs(top_left_lng - bottom_right_lng)
    
    # 緯度の差に基づいて縦の距離を計算
    lat_dist = (math.pi / 180) * R * lat_diff
    
    # 経度の差に基づいて横の距離を計算（赤道に近いほど距離は大きくなる）
    lng_dist = (math.pi / 180) * R * lng_diff * math.cos(math.radians((top_left_lat + bottom_right_lat) / 2))
    
    # 画像の縦横比に合わせてズームレベルを計算
    scale = max(lat_dist / map_height, lng_dist / map_width)
    zoom_level = math.floor(math.log2(2 * math.pi * R / scale))
    
    return zoom_level
    
# 画像を取得してPCLを生成し、YAMLファイルに保存するメイン処理
if __name__ == "__main__":
    # 緯度経度から幅と高さを計算
    width_meter = haversine(args.top_left_lat, args.top_left_lng, args.top_left_lat, args.bottom_right_lng)
    height_meter = haversine(args.top_left_lat, args.top_left_lng, args.bottom_right_lat, args.top_left_lng)
    
    # 画像の縦横比に合わせたsizeパラメータを計算
    size = calculate_image_size(args.top_left_lat, args.top_left_lng, args.bottom_right_lat, args.bottom_right_lng)
    
    # ズームレベルを決定
#    zoom = calculate_zoom_level(args.top_left_lat, args.top_left_lng, args.bottom_right_lat, args.bottom_right_lng, width_meter, height_meter)
    zoom = 16   
    # 画像を取得
    image = get_map_image(args.top_left_lat, args.top_left_lng, args.bottom_right_lat, args.bottom_right_lng, zoom, API_KEY, size)
    
    # 画像を保存し、情報をYAMLファイルに保存
    image_file = save_image_and_info(image, width_meter, height_meter, args.top_left_lat, args.top_left_lng, args.bottom_right_lat, args.bottom_right_lng, "map_info.yaml")
    
    # PCLを生成
    generate_pcl_from_png(image_file, args.output_file, width_meter, height_meter, args.interval)

