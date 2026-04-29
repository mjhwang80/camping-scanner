import PyInstaller.__main__
import os
import shutil

# 1. 이전 빌드 파일 정리
for folder in ['build', 'dist']:
    if os.path.exists(folder):
        try:
            shutil.rmtree(folder)
        except Exception as e:
            print(f"정리 중 오류 발생: {e}")

# 2. PyInstaller 실행
PyInstaller.__main__.run([
    'app/main.py',
    '--onefile',
    #'--windowed',
    '--console',     # <-- 콘솔 창이 뜨도록 변경
    '--name=CampingScanner',
    '--add-data=app/templates;app/templates',
    '--add-data=app/static;app/static',
    '--clean',
])

# 3. 외부 설정 파일 복사 (dist/config/ 경로 생성 및 복사)
# [수정] dist 내부에 config 폴더 생성
dist_config_dir = os.path.join('dist', 'config')
if not os.path.exists(dist_config_dir):
    os.makedirs(dist_config_dir)

# 원본 config/config.yaml 위치 확인 후 복사
src_config_path = os.path.join('config', 'config.yaml')
if os.path.exists(src_config_path):
    shutil.copy(src_config_path, os.path.join(dist_config_dir, 'config.yaml'))
    print("✓ config.yaml 복사 완료 (dist/config/config.yaml)")
else:
    print("! 원본 config.yaml을 찾을 수 없어 기본 파일을 생성합니다.")
    with open(os.path.join(dist_config_dir, 'config.yaml'), 'w', encoding='utf-8') as f:
        f.write("server:\n  port: 8000\n  host: '127.0.0.1'")

# 4. XML 데이터 폴더 복사
src_data_path = 'data' 
dist_data_path = os.path.join('dist', 'data')
if os.path.exists(src_data_path):
    shutil.copytree(src_data_path, dist_data_path)
    print(f"✓ data 폴더 복사 완료 ({dist_data_path})")
else:
    print(f"! 경고: {src_data_path} 폴더를 찾을 수 없습니다.")

print("\n=== 빌드 완료 ===")