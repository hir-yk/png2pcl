import requests
from PIL import Image
import math
from io import BytesIO
import argparse
import os
import subprocess
import yaml
import mgrs
from geographiclib.geodesic import Geodesic
import utm

# Constants
TILE_SIZE = 256
EARTH_RADIUS_KM = 6371.0
WGS84 = Geodesic.WGS84

# Helper functions
def geodesic_distance(lat1, lon1, lat2, lon2):
    result = WGS84.Inverse(lat1, lon1, lat2, lon2)
    return result['s12'] / 1000  # Return distance in kilometers

def haversine(lat1, lon1, lat2, lon2):
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = (math.sin(dLat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dLon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return EARTH_RADIUS_KM * c * 1000  # Return distance in meters

def deg_to_tile(lat_deg, lon_deg, zoom):
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return (xtile, ytile)

def tile_to_deg(xtile, ytile, zoom):
    n = 2.0 ** zoom
    lon_deg = xtile / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
    lat_deg = math.degrees(lat_rad)
    return (lat_deg, lon_deg)

def tile_to_pixel(tile):
    return (tile[0] * TILE_SIZE, tile[1] * TILE_SIZE)

def get_tile(zoom, xtile, ytile, save_directory):
    tile_filename = os.path.join(save_directory, f"{zoom}_{xtile}_{ytile}.png")
    if os.path.isfile(tile_filename):
        print(f"タイル {zoom}/{xtile}/{ytile} は既に存在します。スキップします。")
        return Image.open(tile_filename)

    # タイルのダウンロードを開始
    print(f"タイル {zoom}/{xtile}/{ytile} をダウンロードしています...")
    url = f"https://cyberjapandata.gsi.go.jp/xyz/std/{zoom}/{xtile}/{ytile}.png"
    response = requests.get(url)
    if response.status_code == 200:
        tile_image = Image.open(BytesIO(response.content))
        os.makedirs(save_directory, exist_ok=True)
        tile_image.save(tile_filename)
        print(f"タイル {zoom}/{xtile}/{ytile} をダウンロードしました。")
        return tile_image
    else:
        print(f"タイル {zoom}/{xtile}/{ytile} のダウンロードに失敗しました。ステータスコード: {response.status_code}")
        return None

def get_map_image(lat_start, lon_start, lat_end, lon_end, zoom, map_image_filename, save_directory):
    # タイル座標を計算
    start_tile = deg_to_tile(lat_start, lon_start, zoom)
    end_tile = deg_to_tile(lat_end, lon_end, zoom)
    
    # 四隅の緯度経度を計算
    top_left_deg = tile_to_deg(start_tile[0], start_tile[1], zoom)
    top_right_deg = tile_to_deg(end_tile[0] + 1, start_tile[1], zoom)
    bottom_left_deg = tile_to_deg(start_tile[0], end_tile[1] + 1, zoom)
    bottom_right_deg = tile_to_deg(end_tile[0] + 1, end_tile[1] + 1, zoom)
    
    # 画像の縦横の距離を計算
    width_km = geodesic_distance(top_left_deg[0], top_left_deg[1], top_right_deg[0], top_right_deg[1])
    height_km = geodesic_distance(top_left_deg[0], top_left_deg[1], bottom_left_deg[0], bottom_left_deg[1])
    
    # 全体の画像サイズを計算
    total_width = (end_tile[0] - start_tile[0] + 1) * TILE_SIZE
    total_height = (end_tile[1] - start_tile[1] + 1) * TILE_SIZE
    
    # 全体の画像を作成
    map_image = Image.new('RGB', (total_width, total_height))
    print("地図画像を作成中...")
    
    # タイルをダウンロードして画像に貼り付け
    for x in range(start_tile[0], end_tile[0] + 1):
        for y in range(start_tile[1], end_tile[1] + 1):
            tile_image = get_tile(zoom, x, y, save_directory)
            if tile_image:
                map_image.paste(tile_image, ((x - start_tile[0]) * TILE_SIZE, (y - start_tile[1]) * TILE_SIZE))
    
    # 画像をファイルに保存
    map_image.save(map_image_filename)
    print(f"地図画像を '{map_image_filename}' に保存しました。")
        
    # 四隅の緯度経度と画像の縦横の距離を返す
    return (top_left_deg, top_right_deg, bottom_left_deg, bottom_right_deg, width_km, height_km)
    


def parse_arguments():
    parser = argparse.ArgumentParser(description='Download a map image from GSI map tiles.')
    parser.add_argument('lat_start', type=float, help='Starting latitude')
    parser.add_argument('lon_start', type=float, help='Starting longitude')
    parser.add_argument('lat_end', type=float, help='Ending latitude')
    parser.add_argument('lon_end', type=float, help='Ending longitude')
    parser.add_argument('--zoom', type=int, default=15, help='Zoom level (default: 15)')
    parser.add_argument('--interval', type=float, default=1.0, help='Interval between points in meters. Default is 1.0')
    return parser.parse_args()

def calculate_local_position(lat, lon):
    # 緯度経度をUTM座標に変換
    utm_result = utm.from_latlon(lat, lon)
    easting, northing, zone_number, zone_letter = utm_result
    
    # MGRS座標系の原点（100kmグリッドの南西角）のUTM座標を計算
    origin_easting = int(easting // 100000) * 100000
    origin_northing = int(northing // 100000) * 100000
    
    # 原点からの相対的な位置を計算（メートル単位）
    local_x = easting - origin_easting
    local_y = northing - origin_northing
    
    return local_x, local_y
    
    
def main():
    # コマンドライン引数を解析
    args = parse_arguments()
    print("コマンドライン引数を解析しました。")

    # 結果を保存するディレクトリを設定
    result_directory = "result"
    save_directory = os.path.join(result_directory, "img_tiles")
    os.makedirs(result_directory, exist_ok=True)
    os.makedirs(save_directory, exist_ok=True)
    print(f"ディレクトリ '{result_directory}' と '{save_directory}' を作成または確認しました。")

    # 地図画像とYAMLファイルのファイル名を設定
    map_image_filename = os.path.join(result_directory, 'map_image.png')
    yaml_filename = os.path.join(result_directory, 'map_dimensions.yaml')


    # 地図画像を取得して保存し、四隅の緯度経度と画像の縦横の距離を取得
    top_left_deg, top_right_deg, bottom_left_deg, bottom_right_deg, width_km, height_km = get_map_image(
        args.lat_start, args.lon_start, args.lat_end, args.lon_end, args.zoom, map_image_filename, save_directory
    )
    
    # 地図情報を辞書に格納
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
    # MGRSとローカルUTM座標を計算して辞書に追加
    m = mgrs.MGRS()
    bottom_left_lat, bottom_left_lon = map_info['corners']['bottom_right']
    xtile, ytile = deg_to_tile(args.lat_end, args.lon_start, args.zoom)
    bottom_left_deg = tile_to_deg(xtile, ytile+1, args.zoom)  # ytile + 1 でタイルの下の辺を取得
    bottom_left_lat, bottom_left_lon = bottom_left_deg
    mgrs_code = m.toMGRS(bottom_left_lat, bottom_left_lon, MGRSPrecision=5)
    
    # MGRS座標系の原点からの相対的な位置を計算
    local_x, local_y = calculate_local_position(bottom_left_lat, bottom_left_lon)
    local_x = float(local_x)
    local_y = float(local_y)
    
    # 結果を辞書に追加
    map_info['mgrs'] = {
        'code': mgrs_code,
        'local_x': round(local_x, 3),  # 小数点以下3桁で丸める
        'local_y': round(local_y, 3)   # 小数点以下3桁で丸める
    }
    
    print(f"MGRSコード: {mgrs_code}, ローカルX: {local_x:.3f} m, ローカルY: {local_y:.3f} m")

    # MGRSとローカルUTM座標をmap_infoに追加
    map_info['mgrs'] = {
        'code': mgrs_code,
        'local_x': local_x,
        'local_y': local_y
    }

    # map_infoをYAMLファイルに書き出し
    with open(yaml_filename, 'w') as yaml_file:
        yaml.dump(map_info, yaml_file, default_flow_style=False)
    print(f"地図情報を '{yaml_filename}' に書き出しました。")

    # png2pcl.pyコマンドを構築して実行
    png2pcl_command = [
        'python3', 'png2pcd.py',
        map_image_filename,
        os.path.splitext(map_image_filename)[0] + '.pcd',
        '--x_meter', str(map_info['dimensions']['width_km'] * 1000),
        '--y_meter', str(map_info['dimensions']['height_km'] * 1000),
        '--z_meter', '0',
        '--interval', str(args.interval),
        '--offset_x', str(map_info['mgrs']['local_x']),
        '--offset_y', str(map_info['mgrs']['local_y'])
    ]
    print(f"png2pcl.pyコマンドを実行します: {' '.join(png2pcl_command)}")
    subprocess.run(png2pcl_command)

if __name__ == '__main__':
    main()
