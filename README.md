# auto-join-meet

- 自動でgoogle meetに参加するプログラム
- 実行するとその日の全ての会議に自動で参加する
- 毎晩実行終了して毎朝実行開始する必要あり

## 事前準備
- gcpでgoogle calendar apiを有効化
- oauthクライアントIDを発行してjsonファイルをダウンロード
- ダウンロードしたファイルを`credentials.json`としてルートディレクトリに置く

## 動かし方
```shell
uv sync
uv run main.py
```

## 構成
```
.
├── README.md
├── credentials.json
├── main.py
├── pyproject.toml
├── token.pickle
└── uv.lock
```
