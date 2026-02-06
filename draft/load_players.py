import csv
import os
import django
import sys

# 1. 現在のファイル(draft/load_players.py)から見て一階層上(プロジェクトルート)をパスに追加
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

# 2. settings.py がある場所を「フォルダ名.settings」で指定
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'draftproject.settings')

django.setup()

from draft.models import Player

def run():
    # 3. CSVファイルもdraftフォルダ内にあるのでパスを合わせる
    file_path = os.path.join(os.path.dirname(__file__), 'players.csv')
    
    if not os.path.exists(file_path):
        print(f"エラー: {file_path} が見つかりません。")
        return

    with open(file_path, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            try:
                def safe_int(val):
                    try: return int(val)
                    except: return 0

                Player.objects.create(
                    name=row['name'],
                    category=row['category'],
                    position=row['position'],
                    team=row['team'],
                    bats_throws=row['bats_throws'],
                    height=safe_int(row['height']),
                    weight=safe_int(row['weight']),
                    introduction=row.get('introduction', ''),
                    scout_comment=row.get('scout_comment', '')
                )
                count += 1
            except Exception as e:
                print(f"エラー（{row.get('name')}）: {e}")

    print(f"成功: {count} 名の選手を登録しました！")

if __name__ == '__main__':
    run()