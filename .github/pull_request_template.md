# Pull Request

## 変更内容

<!-- 何を、なぜ変更したかを記載してください。 -->

## 互換性への影響

<!-- CSV 6列、.ssproj、CLI、firmware、対応 version への影響を記載してください。 -->

## 検証

- [ ] `python -m unittest discover -s tests -v`
- [ ] `python -m compileall -q simulator tests`
- [ ] `ruff check simulator tests`
- [ ] `ruff format --check simulator tests`
- [ ] `mypy`
- [ ] firmware 変更時は対象 FQBN のコンパイル
- [ ] dashboard 変更時は Serial Studio 4.0.3 で表示確認

## 関連 Issue

<!-- 例: Closes #123 -->
