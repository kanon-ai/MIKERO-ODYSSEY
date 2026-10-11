# MIKERO-ODYSSEY MSX2+ v0.1.4

MSX2+向けの公開試作版です。Z80で動作し、R800は使用していません。
[配布ZIP](https://github.com/kanon-ai/MIKERO-ODYSSEY/releases/tag/msx2plus-v0.1.4) · [MSX版](../README.md)

![タイトル](title.png)

![実速度プレイ](gameplay.gif)

SCREEN 5のカラフルなタイルとキャラクター、落ち着いた床、暗い視野外の壁を採用。
V9958の縦横スクロールを使い、1マスを2ピクセルずつ8段階で移動します。
音楽はOPLLの主旋律・和音・低音、効果音はPSG。行動に合わせて音楽が進み、停止後に静かになります。
下部はアイコン付き情報パネル。走査線の表示切り替え中は黒くして境目の乱れを軽減しています。

## 必要環境と起動

- MSX2+ / V9958、RAM 64KB以上、VRAM 128KB、512KB ASCII16 ROM。
- 音楽にはMSX-MUSIC（YM2413 / OPLL）が必要です。MSX2+でも非搭載機があります。
- 初代MSX / MSX2向けROMではありません。
- ZIPを展開して `START.cmd`。外部のopenMSXとC-BIOSが必要です。BIOS・エミュレータは同梱しません。
- 別のエミュレータではROMをASCII16として読み込みます。旧版のセーブステートは使わず新規起動してください。

## 操作とルール

左右でEASY / NORMAL / HARD、SPACEで開始。
方向キーで移動・肉球、SPACEで待機、Zで回復。Keeper・ショップは隣から方向入力。
結果画面はSPACEでNEW GAME、Xでタイトルへ。
EASYは15階、NORMAL/HARDは30階。HARDは鍵を取ってから階段を降ります。
[基本ルール・世界観](../docs/manual-ja.md)はMSX版と共通です。

## 検証範囲

openMSX / C-BIOS / Z80で確認しています。今回のパネル修正は50Hz・60Hzで、
数値、回復、移動、救出後の下部消去、タイトル復帰を確認。VRAMタイミング違反は0件。
[60Hz検証](panel-verification.json) · [50Hz検証](panel-verification-pal.json) · [収録記録](media-check.json)

GIFはこの配布ROMを通常のキー操作で収録した実速度・無音の画像です。
[OPLL・PSGの収録音声](opll-gameplay.wav)も同じ操作時のものです。
実機・各社純正BIOS・blueMSXでの動作と見え方、30階の連続プレイ全体は未検証です。
MSX1版と同等の移動速度にはまだ達していません。ちらつきの完全解消を保証するものではありません。

## ソースとビルド

Python 3 + Pillow、SDCC Z80を使用します。
このフォルダーで `python work/source/build.py` を実行してください。
必要に応じて `SDCC_BIN` をSDCCのbinディレクトリに設定します。
生成ROMは `outputs/MIKERO-ODYSSEY.rom` です。
