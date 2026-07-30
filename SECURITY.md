# Security Policy

## Supported versions

このサンプルは `main` の最新状態のみをサポートします。過去の commit や改変版で見つかった問題も、最新 `main` で再現するか確認してください。

## Reporting a vulnerability

脆弱性の詳細、exploit、個人情報、token、デバイス固有情報を公開 Issue に投稿しないでください。

1. [Private vulnerability reporting](https://github.com/hjosugi/serial-lab/security/advisories/new) を使用してください。
2. 影響するファイル、再現条件、想定される影響、可能なら最小の再現例を記載してください。
3. 公開してよい状態になるまで、Issue や Discussion へ詳細を転載しないでください。

GitHub の非公開報告画面を利用できない場合は、詳細を公開せず、リポジトリ owner の GitHub profile から連絡方法を確認してください。

## Scope

このポリシーの対象:

- `simulator/telemetry_simulator.py` の入力処理と UDP 送信
- ESP32 firmware
- Serial Studio project files
- GitHub Actions とリポジトリ内の開発設定

Serial Studio 本体または Arduino-ESP32 本体の脆弱性は、それぞれの upstream security policy に従って報告してください。
