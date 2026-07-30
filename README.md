# Serial Studio ESP32 Telemetry Sample

ESP32の内蔵情報と疑似波形をSerial Studioに表示する、追加センサー不要のサンプルです。

以下の2通りで動かせます。

- ESP32実機: USBシリアル、115200 baud
- PCのみ: PythonシミュレーターからUDP、`127.0.0.1:9000`

Serial StudioのFree/GPL版で利用できるUART、UDP、Project File、Quick Plot、Gauge、Bar、Meter、Multi-Plot、Data Grid、LED表示だけを使っています。

## 表示するデータ

ESP32とPythonシミュレーターは、同じ6列のCSVを20 Hzで送ります。

```text
chip_temperature_c,free_heap_kb,uptime_s,sine,triangle,boot_button
```

実際のフレーム例:

```text
43.25,287.00,12.50,0.7071,-0.5000,0
```

| Index | Dataset | Unit | Dashboard |
|---:|---|---|---|
| 1 | Chip Temperature | deg C | Gauge + Plot |
| 2 | Free Heap | KiB | Bar |
| 3 | Uptime | s | Meter |
| 4 | Sine Wave | - | Multi-Plot |
| 5 | Triangle Wave | - | Multi-Plot |
| 6 | BOOT Button | 0/1 | Data Grid + LED |

## ESP32で動かす

### 必要なもの

- ESP32開発ボード
- USBデータケーブル
- Arduino IDE
- Arduino-ESP32 core
- Serial Studio 4.0.3以降

### 手順

1. Arduino IDEで`firmware/esp32_serial_studio_demo.ino`を開きます。
2. 使用するESP32ボードとシリアルポートを選びます。
3. ESP32へアップロードします。
4. Serial Studioで`dashboard/esp32_serial_dashboard.ssproj`を開きます。
5. ESP32のシリアルポートを選び、baud rateを`115200`にします。
6. `Connect`を押します。
7. BOOTボタンを押すと`BOOT Button`が`1`になります。

一般的なESP32 DevKitではBOOTボタンはGPIO 0です。別のピンを使うボードでは、スケッチ先頭の`BUTTON_PIN`を変更してください。

ESP32の`temperatureRead()`はチップ内部温度です。室温センサーではないため、室温より高く表示されることがあります。

## PCだけで動かす

追加パッケージは不要です。Python 3の標準ライブラリだけを使います。

```bash
python simulator/telemetry_simulator.py
```

次にSerial Studioで`dashboard/desktop_udp_dashboard.ssproj`を開き、`Connect`を押します。接続設定は次の値で保存済みです。

- Transport: UDP
- Address: `127.0.0.1`
- Local port: `9000`
- Remote port: `9000`

10秒だけ実行する例:

```bash
python simulator/telemetry_simulator.py --count 200
```

フレームを標準出力でも確認する例:

```bash
python simulator/telemetry_simulator.py --stdout --count 20
```

## Quick Plotで動かす

このサンプルは改行区切りの数値CSVなので、Project Fileを使わずQuick Plotでも表示できます。

1. ESP32版ではUARTと`115200`を選びます。
2. PC版ではNetwork、UDP、local port `9000`を選びます。
3. Operation Modeを`Quick Plot`にします。
4. `Connect`を押します。

Quick Plotでは列名や単位は表示されません。名前付きのGaugeやMulti-Plotを使う場合は、同梱の`.ssproj`を開いてください。

## テスト

プロジェクトJSON、dataset index、接続設定、シミュレーターのフレーム形式を確認します。

```bash
python -m unittest discover -s tests -v
```

## トラブルシューティング

### データが表示されない

- ESP32とSerial Studioのbaud rateが両方`115200`か確認します。
- Arduino IDEのSerial Monitorを閉じます。同じシリアルポートを2つのアプリから同時には開けません。
- Project Fileモードになっているか確認します。
- Consoleで1行に6個の数値が出ているか確認します。

### UDP版が表示されない

- Pythonシミュレーターを先に起動します。
- UDP local portが`9000`か確認します。
- 別のアプリがport `9000`を使用していないか確認します。
- OSのファイアウォールでPythonのlocalhost通信が拒否されていないか確認します。

### ESP32-S3/C3でシリアルポートが出ない

Arduino IDEのボード設定でUSB CDC On Bootが必要なボードがあります。使用するボードのArduino-ESP32設定に合わせて有効にしてください。

## 構成

```text
serial-studio-esp32-sample/
├── dashboard/
│   ├── desktop_udp_dashboard.ssproj
│   └── esp32_serial_dashboard.ssproj
├── firmware/
│   └── esp32_serial_studio_demo.ino
├── simulator/
│   └── telemetry_simulator.py
├── tests/
│   └── test_sample.py
├── LICENSE
└── README.md
```

## Compatibility

このサンプルの`.ssproj`はSerial Studio 4.0.3の`schemaVersion: 3`に合わせています。パーサーはSerial Studio 4.xのBuilt-In `Delimited text`テンプレートを使用します。

