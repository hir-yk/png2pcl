import requests
import yaml
from PIL import Image
from io import BytesIO

# Google Maps Static APIのエンドポイント
MAPS_API_ENDPOINT = "https://maps.googleapis.com/maps/api/staticmap"

# APIキー（Google Cloud Platformで取得したキーを使用）
API_KEY = "YOUR_API_KEY"

# 緯度経度から画像を取得する関数
def get_map_image(top_left_lat, top_left_lng, bottom_right_lat, bottom_right_lng, zoom, api_key):
    # パラメータの設定
    params = {
        "size": "640x640",  # 画像のサイズ（Google Maps APIの最大サイズ）
        "maptype": "satellite",  # 地図のタイプ
        "key": api_key,
        "path": f"color:0x0000ff|weight:5|{top_left_lat},{top_left_lng}|{bottom_right_lat},{bottom_right_lng}"
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
    image.save("map_image.png")
    
    # 情報をYAMLファイルに保存
    info = {
        "image_file": "map_image.png",
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

# 画像を取得してYAMLファイルに保存する例
if __name__ == "__main__":
    # 画像を取得する緯度経度の範囲を指定
    top_left_lat = 35.6895
    top_left_lng = 139.6917
    bottom_right_lat = 35.6814
    bottom_right_lng = 139.7068
    zoom = 16  # ズームレベル
    
    # 画像を取得
    image = get_map_image(top_left_lat, top_left_lng, bottom_right_lat, bottom_right_lng, zoom, API_KEY)
    
    # 幅と高さを計算（ここでは仮の値を使用）
    width_meter = 1000  # 実際には緯度経度から計算する必要がある
    height_meter = 1000  # 実際には緯度経度から計算する必要がある
    
    # 画像と情報をYAMLファイルに保存
    save_image_and_info(image, width_meter, height_meter, top_left_lat, top_left_lng, bottom_right_lat, bottom_right_lng, "map_info.yaml")
