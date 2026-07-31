# Serial Lab: ESP32 Telemetry for Serial Studio

[![CI](https://github.com/hjosugi/serial-lab/actions/workflows/ci.yml/badge.svg)](https://github.com/hjosugi/serial-lab/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

ESP32 の内蔵情報と疑似波形を [Serial Studio](https://github.com/Serial-Studio/Serial-Studio) に表示する、追加センサー不要の日本語サンプルです。

次の2通りで同じダッシュボードを試せます。

- ESP32 実機: USB シリアル、115200 baud、20 Hz
- PC のみ: Python 標準ライブラリによる UDP、`127.0.0.1:9000`、20 Hz

UART、UDP、Project File、Quick Plot と標準 widget だけを使用します。必要機能は Serial Studio の GPL source build に含まれます。公式バイナリと Pro 機能の提供条件は upstream の最新説明を確認してください。

## 現在の検証範囲

| 対象 | 固定・検証 version | 自動検証 | 備考 |
|---|---|---|---|
| Serial Studio project | 4.0.3 / schema 3 | JSON と意味的契約 | 公式 4.0.3 UDP project と source 設定を照合 |
| Python simulator | Python 3.10 / 3.14 | unit、CLI、UDP integration、Ruff、mypy | 実行時の外部 package なし |
| ESP32 firmware | Arduino-ESP32 3.3.10 | ESP32 / C3 / S3 compile | upload と実描画は未検証 |
| 実機受け入れ | Serial Studio 4.0.3 | 対象外 | 手順と結果記録は [#6](https://github.com/hjosugi/serial-lab/issues/6) |

「コンパイル成功」と「実機で upload・描画成功」は分けて扱います。物理ボードで未確認の内容を検証済みとは表記しません。

## 送信データ契約

firmware と simulator は、同じ6列の改行区切り CSV を送ります。

```text
chip_temperature_c,free_heap_kib,uptime_s,sine,triangle,boot_button
```

フレーム例:

```text
43.25,287.00,12.50,0.7071,-0.5000,0
```

| Index | Dataset | 単位 | 表示 |
|---:|---|---|---|
| 1 | Chip Temperature | deg C | Gauge + Plot |
| 2 | Free Heap | KiB | Bar |
| 3 | Uptime | s | Meter（0〜86400 s）|
| 4 | Sine Wave | - | Multi-Plot |
| 5 | Triangle Wave | - | Multi-Plot |
| 6 | BOOT Button | 0/1 | Data Grid + LED |

列順は `.ssproj` の dataset index と直結しています。変更するときは firmware、simulator、両 project file、テスト、README を同時に更新してください。

### Uptime と連続稼働時間

想定する最大連続稼働時間は **24 時間（86400 s）** です。Uptime Meter の range はこの値に合わせています。

- firmware は 64-bit の `esp_timer_get_time()`（起動からの microsecond）を `double` 秒へ変換して送ります。32-bit の `millis()` は使いません。約49.7日で0へ戻る wrap は発生しません。
- simulator は `time.monotonic()` 起点で、同じく wrap しません。firmware と simulator の Uptime semantics は一致しています。
- sine と triangle の位相は、32-bit float へ落とす前に1周期へ畳み込みます。畳み込まない場合、24時間後の位相は約271000 rad に達し、32-bit float の分解能は約0.03 rad まで低下して波形が階段状に見えます。
- 24時間を超えても値は増え続けます。Meter の針だけが上限で止まります。

これらは `tests/test_simulator.py` と `tests/test_firmware_layout.py` で検証しています。

## PC だけで最短実行

### PC に必要なもの

- Python 3.10 以降
- Serial Studio 4.0.3

追加 package は不要です。

```bash
python simulator/telemetry_simulator.py
```

次に Serial Studio で `dashboard/desktop_udp_dashboard.ssproj` を開き、`Connect` を押します。project file には次の接続設定が保存されています。

- Transport: UDP
- Address: `127.0.0.1`
- Local port: `9000`
- Remote port: `9000`

終了は `Ctrl+C` です。10秒相当の200 frame だけ送る例:

```bash
python simulator/telemetry_simulator.py --count 200
```

送信 frame を terminal にも表示する例:

```bash
python simulator/telemetry_simulator.py --stdout --count 20
```

### Simulator CLI

```text
python simulator/telemetry_simulator.py [options]
```

| Option | Default | 制約・意味 |
|---|---:|---|
| `--host HOST` | `127.0.0.1` | 空でない IPv4 address または IPv4 へ解決できる hostname |
| `--port PORT` | `9000` | `1`〜`65535` |
| `--rate HZ` | `20.0` | 有限の正数、最大 `1000` Hz |
| `--count N` | `0` | `0` 以上。`0` は停止するまで送信 |
| `--stdout` | off | UDP と同じ frame を標準出力にも表示 |

正常終了と `Ctrl+C` は exit code `0`、入力検証または socket error は stderr へ理由を出して `1` を返します。`argparse` 自体の構文エラーは `2` です。

## ESP32 で実行

### ESP32 に必要なもの

- ESP32 開発ボード
- USB データケーブル
- Arduino IDE または Arduino CLI
- Arduino-ESP32 3.3.10
- Serial Studio 4.0.3

### Arduino IDE

1. `firmware/esp32_serial_studio_demo/esp32_serial_studio_demo.ino` を開きます。
2. 使用する ESP32 ボードと serial port を選びます。
3. ESP32 へ upload します。
4. Serial Studio で `dashboard/esp32_serial_dashboard.ssproj` を開きます。
5. ESP32 の serial port と `115200` baud を選びます。
6. `Connect` を押します。
7. BOOT button を押し、`BOOT Button` が `1`、解放時に `0` になることを確認します。

一般的な ESP32 DevKit の BOOT button は GPIO 0 / active-low です。異なる pin のボードでは、スケッチ先頭の `BUTTON_PIN` を変更してください。

ESP32-S3/C3 などでは Arduino IDE の `USB CDC On Boot` 設定が必要な場合があります。ボード固有の Arduino-ESP32 設定に従ってください。

### Arduino CLI でコンパイル

ESP32 DevKit の例:

```bash
arduino-cli core update-index \
  --additional-urls https://espressif.github.io/arduino-esp32/package_esp32_index.json
arduino-cli core install esp32:esp32@3.3.10 \
  --additional-urls https://espressif.github.io/arduino-esp32/package_esp32_index.json
arduino-cli compile \
  --fqbn esp32:esp32:esp32 \
  firmware/esp32_serial_studio_demo
```

CI では FQBN `esp32:esp32:esp32`、`esp32:esp32:esp32c3`、`esp32:esp32:esp32s3` を個別にコンパイルします。

## Quick Plot

このサンプルは数値 CSV なので、Project File を使わず Quick Plot でも表示できます。

1. ESP32 版では UART と `115200` baud、PC 版では Network / UDP / local port `9000` を選びます。
2. Operation Mode を `Quick Plot` にします。
3. `Connect` を押します。

Quick Plot では列名や単位が付きません。名前付き Gauge や Multi-Plot には同梱 `.ssproj` を使用してください。

## 開発・検証

標準ライブラリだけで行える検証:

```bash
python -m compileall -q simulator tests
python -m unittest discover -s tests -v
```

品質 tool を含む完全なローカル検証:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --requirement requirements-dev.txt
ruff check simulator tests
ruff format --check simulator tests
mypy
```

Windows PowerShell では activate に `.venv\Scripts\Activate.ps1` を使用してください。CI と依存 version は `requirements-dev.txt` と `.github/workflows/ci.yml` に固定しています。

Markdown 文書の検証には Node.js / npm がある環境で次を使用できます。

```bash
npx --yes markdownlint-cli2@0.19.0 \
  README.md CONTRIBUTING.md SECURITY.md .github/pull_request_template.md
```

テストが検証する主な契約:

- frame の6列、数値 format、wave range、button cycle
- Uptime が `millis()` の wrap 点を越えても増加し続けること
- wave 位相の1周期畳み込みと、32-bit float 化後の精度
- CLI option、境界値、`NaN` / `Infinity` / 過大 rate の拒否
- 指定 count の UDP 送信と標準出力
- Serial Studio schema、parser、source 接続設定
- dataset の index / title / unit / widget / range
- UART / UDP dashboard の意図しない差分
- group と dataset の ID、`nextUniqueId`
- Arduino の主 sketch と directory 名の一致
- firmware が 64-bit timer を使い `millis()` を使わないこと

## 制約

- `temperatureRead()` は ESP32 内部の chip temperature です。室温センサーではなく、室温より高く表示されることがあります。
- BOOT button の pin と USB 設定はボードごとに異なります。
- UDP simulator は IPv4 socket を使用します。
- Uptime の Meter は 24 時間で表示上限に達します。値自体はその後も増え続けますが、針は上限に張り付きます。
- 自動コンパイルは実機 upload、USB 再接続、Serial Studio GUI の描画を保証しません。

## トラブルシューティング

### UART データが表示されない

- ESP32 と Serial Studio が両方 `115200` baud か確認します。`.ssproj` の `baudRate` は baud 値そのものではなく Serial Studio の baud リストへの index で、`10` が `115200` です。手で編集するときは値を直接書かないでください。
- Arduino IDE の Serial Monitor を閉じます。同じ port は同時に占有できません。
- Project File mode か確認します。
- Console で1行に6個の数値が届いているか確認します。
- S3/C3 では `USB CDC On Boot` を確認します。

### UDP データが表示されない

- simulator を先に起動します。
- UDP local port が `9000` か確認します。
- 別の process が port `9000` を使っていないか確認します。
- OS firewall が Python の localhost UDP を拒否していないか確認します。
- `--stdout --count 20` で simulator 自体が frame を生成しているか確認します。

### CLI が入力を拒否する

- `--rate` は `0` より大きく `1000` 以下の有限値です。
- `--port` は `1`〜`65535` です。
- `--count` は `0` 以上です。
- stderr の `error:` 以降に拒否理由が表示されます。

## 構成

```text
serial-lab/
├── .github/
│   ├── ISSUE_TEMPLATE/
│   └── workflows/ci.yml
├── dashboard/
│   ├── desktop_udp_dashboard.ssproj
│   └── esp32_serial_dashboard.ssproj
├── firmware/
│   └── esp32_serial_studio_demo/
│       └── esp32_serial_studio_demo.ino
├── simulator/
│   ├── __init__.py
│   └── telemetry_simulator.py
├── tests/
│   ├── test_firmware_layout.py
│   ├── test_project_files.py
│   └── test_simulator.py
├── CONTRIBUTING.md
├── LICENSE
├── README.md
├── SECURITY.md
├── pyproject.toml
└── requirements-dev.txt
```

## Upstream とライセンス

- [Serial Studio 4.0.3 release](https://github.com/Serial-Studio/Serial-Studio/releases/tag/v4.0.3)
- [Serial Studio source and feature overview](https://github.com/Serial-Studio/Serial-Studio)
- [Arduino-ESP32 3.3.10 documentation](https://docs.espressif.com/projects/arduino-esp32/en/latest/)
- [Arduino CLI](https://github.com/arduino/arduino-cli)
- [Python socket documentation](https://docs.python.org/3/library/socket.html)

このリポジトリのコードと文書は [MIT License](LICENSE) です。Serial Studio、Arduino-ESP32、利用する tool と binary にはそれぞれの upstream license と利用条件が適用されます。

貢献手順は [CONTRIBUTING.md](CONTRIBUTING.md)、脆弱性の非公開報告は [SECURITY.md](SECURITY.md) を参照してください。
