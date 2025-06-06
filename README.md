# slack-archive-custom

slack のアーカイブを作成するためのプログラムです。
[felixrieseberg/slack-archive](https://github.com/felixrieseberg/slack-archive)を改変したパッケージと、補助プログラムによって構成されています。
手順書は作成中です。

## 使い方

### 準備物

- slack の app token
  詳しくは[こちら](https://github.com/felixrieseberg/slack-archive)を参照してください。
- (free プランで 3 か月以上遡及する場合)
  slacklog の zip ファイル

### 手順 (1 ～ 2 は pro プランの場合パス)

1. slacklog の zip ファイルを解凍し、このディレクトリにフォルダを配置する。複数の zip ファイルがある場合は、一つのフォルダ群にマージする。
2. 解凍したディレクトリをプログラム内で指定し、`1_convert-json.py`を実行する。
3. `npx slack-archive`を実行する。指示に従う。
   詳しくは[こちら](https://github.com/felixrieseberg/slack-archive)を参照してください。
4. `3_ragex.py`を実行する。
5. 適当なエディタで`C:\Users\【ファイルの配置場所】\slack-archive\html\emojis\`を`emojis/`に置換する。
