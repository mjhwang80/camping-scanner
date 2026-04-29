import yaml
from pathlib import Path

def load_config():
    # 1. 현재 파일(config_loader.py)의 위치를 기준으로 프로젝트 루트 찾기
    # app/core/config_loader.py 기준 -> parent(core) -> parent(app) -> parent(root)
    current_path = Path(__file__).resolve()
    project_root = current_path.parent.parent.parent
    
    # 2. config/config.yaml 경로 생성
    config_path = project_root / "config" / "config.yaml"

    if not config_path.exists():
        raise FileNotFoundError(f"⚠️ 설정 파일을 찾을 수 없습니다: {config_path}")

    # 3. YAML 파일 읽기
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

# 싱글톤 인스턴스처럼 활용
CONFIG = load_config()