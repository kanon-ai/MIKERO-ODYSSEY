# MIKERO-ODYSSEY v1.5.5 テスト版

右上に階段の方角を示す黄色い三角マーカーを追加しました。上下左右・斜めの8方向で、移動に合わせて向きが変わります。階段が未発見でも方角が分かります。壁や通路を考慮した道順ではなく、おおよその直線方向です。最終30階では王冠の方向を示します。

画面最下段のキー説明、移動速度、8ドット×2回のスクロール、救出演出、BGM、回復量、地形サイズは変更していません。

START.cmdをダブルクリックして起動してください。外部openMSXとC-BIOSを使用します。MSX1・RAM32KB・VRAM16KB・512KB ASCII16 ROMです。

矢印：移動／肉球攻撃、SPACE：開始・待機・再挑戦、Z：回復薬。ジョイスティックのボタン1は待機、ボタン2は回復です。30階の王冠を取ると完走します。ハイスコアは再挑戦をまたいで保持し、電源OFFで消えます。

NTSC/PALで8方向、階層移動時の目標更新、最下段のキー説明、スクロールを検証しました。compass.pngは実エミュレーターの画面です。実機試験は未実施です。

BGMはP. I. Tchaikovsky『くるみ割り人形・行進曲』をもとにした独自PSG編曲・変奏です。
[参照楽譜](https://imslp.org/wiki/The_Nutcracker_(suite),_Op.71a_(Tchaikovsky,_Pyotr))

ビルドにはPython 3とSDCCが必要です。SDCCをPATHに追加するかSDCC_BINを設定し、python work/source/build.pyを実行します。検証にはPillow、外部openMSXとC-BIOSが必要です。
