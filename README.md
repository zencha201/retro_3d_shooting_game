# Pyxel 3D Shooting

Pyxelで作成した、ワイヤーフレーム表示の3Dシューティングゲームです。

- 画面解像度: `256x224`
- 描画スタイル: ワイヤーフレーム
- 画面構成: タイトル / ゲーム / ゲームオーバー

## ゲーム実行

[ゲーム実行](https://kitao.github.io/pyxel/wasm/launcher/?run=zencha201.retro_3d_shooting_game.retro_3d_shooting_game&gamepad=enabled)

## ゲーム内容

自機を上下左右に操作し、画面奥から迫ってくる敵をショットで破壊してスコアを稼ぎます。

- 自機: 白い三角錐（左右の翼つき）
- 敵: 赤い四角（回転しながら手前へ移動）
- 弾: 黄色い球体（連射可能、画面奥へまっすぐ発射）
- 演出: 流れる星背景、被弾時フラッシュ、敵破壊時の砕け散りアニメーション

## 操作方法

- `← / → / ↑ / ↓`: 自機移動
- `SPACE / GAMEPAD A`:
  - タイトル画面: ゲーム開始
  - ゲーム中: ショット連射
  - ゲームオーバー画面: タイトルへ戻る

## ルール

- HPは敵が自機に接触したときのみ減少します。
- HPが0になるとゲームオーバーです。
- 敵を破壊するとスコアが増加します。
- ハイスコアを更新すると、ゲームオーバー画面に `NEW HIGH SCORE!` が表示されます。

## 必要環境

- Python 3.10+
- `pyxel>=2.2.0`

## セットアップ

```bash
pip install -r requirements.txt
```

## 実行

```bash
python main.py
```

## ファイル構成

- `main.py`: ゲーム本体
- `requirements.txt`: 依存ライブラリ
- `README.md`: この説明ファイル
