# Contributing

serial-lab への改善提案を歓迎します。小さな修正でも、変更理由と再現方法が分かる形にしてください。

## Issue を作る前に

- 既存 Issue と [Serial Studio upstream](https://github.com/Serial-Studio/Serial-Studio) の既知情報を検索してください。
- 不具合では、OS、Python、Serial Studio、Arduino-ESP32、ボード名を可能な範囲で記載してください。
- token、個人情報、デバイス固有情報、未公開の脆弱性を公開 Issue に含めないでください。
- 脆弱性は [SECURITY.md](SECURITY.md) の非公開報告手順を使用してください。

## ローカルセットアップ

実行時依存は Python 標準ライブラリだけです。品質検査用ツールは別にインストールします。

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install --requirement requirements-dev.txt
```

Windows PowerShell では activate に `.venv\Scripts\Activate.ps1` を使用してください。

## 必須検証

すべての変更:

```bash
python -m compileall -q simulator tests
python -m unittest discover -s tests -v
ruff check simulator tests
ruff format --check simulator tests
mypy
```

firmware を変更した場合は、少なくとも変更対象の FQBN で Arduino-ESP32 3.3.10 のコンパイルを確認してください。CI は ESP32、ESP32-C3、ESP32-S3 を検証します。

`.ssproj` を変更した場合は、両 transport の共通 dashboard が意図せずずれていないことをテストし、可能なら Serial Studio 4.0.3 で実表示も確認してください。

Markdown を変更し Node.js / npm を利用できる場合:

```bash
npx --yes markdownlint-cli2@0.19.0 \
  README.md CONTRIBUTING.md SECURITY.md .github/pull_request_template.md
```

## データ契約

firmware と simulator は次の6列をこの順番で送ります。

```text
chip_temperature_c,free_heap_kib,uptime_s,sine,triangle,boot_button
```

列順、単位、範囲を変更する場合は、firmware、simulator、両 `.ssproj`、テスト、README を同じ変更で更新してください。

## Pull Request

- 1つの PR は1つの目的に絞ってください。
- 関連 Issue を `Closes #123` または `Refs #123` で結び付けてください。
- ハードウェア未検証の場合は、その事実と代わりに実施した検証を明記してください。
- 自動生成物、cache、秘密情報を commit しないでください。
