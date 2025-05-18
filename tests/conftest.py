"""Global pytest fixtures.

テスト実行時に ``src/`` ディレクトリを ``PYTHONPATH`` に追加し、編集途中のパッケージを
インストールせずに直接 import できるようにする。これは *src-layout* プロジェクトで一般的に
用いられる手法である。
"""

from __future__ import annotations

import sys
from pathlib import Path

# ``src`` ディレクトリをパスに追加
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))
