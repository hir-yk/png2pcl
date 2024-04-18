import requests
from PIL import Image
import math
from io import BytesIO
import argparse
import os
import yaml


# Haversine公式を使用して2点間の距離を計算する関数
def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0  # 地球の半径 (km)
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = math.sin(dLat/2) * math.sin(dLat/2) + \
        math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
        math.sin(dLon/2) * math.sin(dLon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance = R * c
    return distance

# 画像の縦横の距離を計算し、YAMLファイルに出力する関数
def output_map_dimensions_to_yaml(lat_start, lon_start, lat_end, lon_end, zoom, yaml_filename):
    # 縦と横の距離を計算
    width_km = haversine(lat_start, lon_start, lat_start, lon_end)
    height_km = haversine(lat_start, lon_start, lat_end, lon_start)
    
    # 距離情報とコマンドライン引数の情報を辞書に格納
    dimensions = {
        'latitude_start': lat_start,
        'longitude_start': lon_start,
        'latitude_end': lat_end,
        'longitude_end': lon_end,
        'zoom': zoom,
        'width_km': width_km,
        'height_km': height_km
    }
    
    # YAMLファイルに書き出し
    with open(yaml_filename, 'w') as yaml_file:
        yaml.dump(dimensions, yaml_file, default_flow_style=False)

# 地理院地図のタイルを取得する関数
def get_tile(zoom, xtile, ytile, save_directory):
    url = f"https://cyberjapandata.gsi.go.jp/xyz/std/{zoom}/{xtile}/{ytile}.png"
    response = requests.get(url)
    if response.status_code == 200:
        tile_image = Image.open(BytesIO(response.content))
        # img_tiles ディレクトリが存在しない場合は作成
        os.makedirs(save_directory, exist_ok=True)
        # 画像をファイルとして保存
        tile_image.save(os.path.join(save_directory, f"{zoom}_{xtile}_{ytile}.png"))
        return tile_image
    else:
        return None

# 緯度経度からタイル座標を計算する関数
def deg_to_tile(lat_deg, lon_deg, zoom):
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return (xtile, ytile)

# タイル座標から緯度経度を計算する関数
def tile_to_deg(xtile, ytile, zoom):
    n = 2.0 ** zoom
    lon_deg = xtile / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
    lat_deg = math.degrees(lat_rad)
    return (lat_deg, lon_deg)
    
# タイル座標からピクセル座標を計算する関数
def tile_to_pixel(tile):
    return (tile[0]*256, tile[1]*256)

# 指定した緯度経度の範囲の地図をPNG画像として取得する関数
# 指定した緯度経度の範囲の地図をPNG画像として取得する関数
def get_map_image(lat_start, lon_start, lat_end, lon_end, zoom, map_image_filename, save_directory, yaml_filename):
    # タイル座標を計算
    start_tile = deg_to_tile(lat_start, lon_start, zoom)
    end_tile = deg_to_tile(lat_end, lon_end, zoom)
    
    # 四隅の緯度経度を計算（右下の緯度経度を取得するために+1を追加）
    top_left_deg = tile_to_deg(start_tile[0], start_tile[1], zoom)
    top_right_deg = tile_to_deg(end_tile[0] + 1, start_tile[1], zoom)
    bottom_left_deg = tile_to_deg(start_tile[0], end_tile[1] + 1, zoom)
    bottom_right_deg = tile_to_deg(end_tile[0] + 1, end_tile[1] + 1, zoom)
    
    # 画像の縦横の距離を計算
    width_km = haversine(top_left_deg[0], top_left_deg[1], top_right_deg[0], top_right_deg[1])
    height_km = haversine(top_left_deg[0], top_left_deg[1], bottom_left_deg[0], bottom_left_deg[1])
    
    # 四隅の緯度経度と画像の縦横の距離をYAMLファイルに出力
    map_info = {
        'corners': {
            'top_left': top_left_deg,
            'top_right': top_right_deg,
            'bottom_left': bottom_left_deg,
            'bottom_right': bottom_right_deg
        },
        'dimensions': {
            'width_km': width_km,
            'height_km': height_km
        }
    }
    with open(yaml_filename, 'a') as yaml_file:  # Write to the YAML file
        yaml.dump(map_info, yaml_file, default_flow_style=False)
    
    # 全体の画像サイズを計算
    total_width = (end_tile[0] - start_tile[0] + 1) * 256
    total_height = (end_tile[1] - start_tile[1] + 1) * 256
    
    # 全体の画像を作成
    map_image = Image.new('RGB', (total_width, total_height))
    

    # タイルをダウンロードして画像に貼り付け
    for x in range(start_tile[0], end_tile[0] + 1):
        for y in range(start_tile[1], end_tile[1] + 1):
            tile_image = get_tile(zoom, x, y, save_directory)  # Use save_directory here
            if tile_image:
                map_image.paste(tile_image, ((x - start_tile[0]) * 256, (y - start_tile[1]) * 256))
    
    # 指定範囲のピクセル座標を計算
    start_pixel = tile_to_pixel(start_tile)
    end_pixel = tile_to_pixel(end_tile)
    
    # 指定範囲を切り取り
    cropped_image = map_image.crop((0, 0, end_pixel[0] - start_pixel[0] + 256, end_pixel[1] - start_pixel[1] + 256))
    
    # PNG画像として保存
#    output_map_dimensions_to_yaml(lat_start, lon_start, lat_end, lon_end, 'map_dimensions.yaml')
    cropped_image.save(map_image_filename)
    
# コマンドライン引数を解析する関数
def parse_arguments():
    parser = argparse.ArgumentParser(description='Download a map image from GSI map tiles.')
    parser.add_argument('lat_start', type=float, help='Starting latitude')
    parser.add_argument('lon_start', type=float, help='Starting longitude')
    parser.add_argument('lat_end', type=float, help='Ending latitude')
    parser.add_argument('lon_end', type=float, help='Ending longitude')
    parser.add_argument('--zoom', type=int, default=15, help='Zoom level (default: 15)')
    return parser.parse_args()

# メイン関数
def main():
    args = parse_arguments()
    # result ディレクトリを指定
    result_directory = "result"
    # img_tiles ディレクトリを指定
    save_directory = os.path.join(result_directory, "img_tiles")
    # result ディレクトリが存在しない場合は作成
    os.makedirs(result_directory, exist_ok=True)
    os.makedirs(save_directory, exist_ok=True)  # Ensure img_tiles directory exists
    # 合成した地図画像のファイル名
    map_image_filename = os.path.join(result_directory, 'map_image.png')
    # YAMLファイルの名前
    yaml_filename = os.path.join(result_directory, 'map_dimensions.yaml')
    

    # 地図画像の寸法情報をYAMLファイルに出力（zoom引数を追加）    output_map_dimensions_to_yaml(args.lat_start, args.lon_start, args.lat_end, args.lon_end, args.zoom, yaml_filename)
    # 地図画像を取得して保存し、四隅の緯度経度をYAMLファイルに出力
    get_map_image(args.lat_start, args.lon_start, args.lat_end, args.lon_end, args.zoom, map_image_filename, save_directory, yaml_filename)



if __name__ == '__main__':
    main()

