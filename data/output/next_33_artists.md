# 次の動画候補 アーティスト選定リスト（データ駆動版）

> 作成日: 2026-02-26
> 方法: 4ソース横断調査（カラオケ/ゴシップ/CM・ドラマ/ストリーミング）→ 2ソース以上検出 → Web検索定量スコアリング

## 選定基準

4つの独立データソース（K=カラオケランキング, G=ゴシップ/スキャンダル報道, C=CM/ドラマタイアップ, S=Spotify/ストリーミング）から128名の候補を収集。2ソース以上で検出された33名に対し、Web検索による定量スコアリングを実施。

- **G1（ゴシップ露出度）**: 日本のワイドショー/ネットニュースでの報道量（1-5）
- **G6（楽曲知名度 in Japan）**: CM/ドラマ主題歌採用+カラオケ人気（1-5）
- **G_ST（日本ストリーミング需要）**: Spotify/Billboard Japan Hot Overseasでの日本チャート実績（1-5）
- **G_YT（YouTube解説動画の既存需要）**: 日本語解説動画の存在・再生数（1-5）

**ランク定義:**
| ランク | 条件 | HIT確率 |
|--------|------|---------|
| S | G1+G6>=8 かつ G_ST>=3 | 90%超 |
| A | G1+G6>=8 かつ G_ST<3 | 67% |
| C | G1+G6<8 | 低い |

**除外済み（制作済み24名 + Avril Lavigne公開済み）:** Lady Gaga, Billie Eilish, Selena Gomez, Ariana Grande, Justin Bieber, Ed Sheeran, Bruno Mars, Taylor Swift, Michael Jackson, Britney Spears, Avicii, Madonna, Freddie Mercury/Queen, Oasis, Elton John, Bon Jovi, Carpenters, David Bowie, Bob Marley, Elvis Presley, Paul McCartney, John Lennon, Adele, Avril Lavigne

---

## 選定結果

### Sランク（G1+G6>=8 AND G_ST>=3）--- 最優先【20名】

| # | アーティスト | G1 | G6 | G1+G6 | G_ST | G_YT | ソース | 選定理由 |
|---|---|---|---|---|---|---|---|---|
| 1 | **Mariah Carey** | 5 | 5 | 10 | 5 | 4 | K,G,C,S | 「スキャンダルの女王」exciteニュース。ミラノ五輪口パク疑惑。「All I Want for Christmas」毎年Spotify Japan 1位(68回)。CM多数。カラオケDAM8位 |
| 2 | **Wham! / George Michael** | 5 | 5 | 10 | 4 | 4 | K,G,S | クリスマス当日急死。公衆トイレ事件・ゲイ公表・薬物。「Last Christmas」Spotify世界22億回再生。マクセルCM。カラ鉄1位 |
| 3 | **Rolling Stones** | 5 | 5 | 10 | 3 | 5 | G,C | ブライアン27クラブ。73年来日公演中止スキャンダル。「Angry」ドラマ主題歌。「She's a Rainbow」iMac CM。解説動画多数&高再生 |
| 4 | **Coldplay** | 5 | 5 | 10 | 4 | 4 | C,S | キスカム不倫スキャンダル。東京ドーム公演。「Viva La Vida」Apple CM。カラオケ多数。Spotify Japan間欠的チャートイン |
| 5 | **Celine Dion** | 5 | 5 | 10 | 3 | 4 | K,G,C | スティッフパーソン症候群闘病。「To Love You More」ドラマ『恋人よ』主題歌。Panasonic CM。2024パリ五輪復活 |
| 6 | **Eric Clapton** | 5 | 5 | 10 | 2 | 4 | K,G,C | ※G_ST=2だがG1+G6=10の圧倒的認知度。息子転落死→Tears in Heaven。三菱自動車CM(2025)。薬物・アルコール依存 |
| 7 | **Guns N' Roses** | 5 | 5 | 10 | 3 | 4 | S | ガンダム映画ED主題歌(2026)。来日公演。カラオケ多数。「Sweet Child O' Mine」Spotify10億回超 |
| 8 | **The Beatles** | 5 | 5 | 10 | 3 | 5 | K,C | 「世界一受けたい授業」特集。来日50周年報道。「In My Life」24時間テレビドラマ主題歌。解説動画多数&圧倒的再生数 |
| 9 | **Maroon 5** | 4 | 5 | 9 | 5 | 4 | K,G,C,S | アダム浮気スキャンダル。ノエビアCM。トヨタVitz CM。Spotify Wrapped 2025 Japan Top Tracks。カラオケDAMコラボ |
| 10 | **One Direction / Liam Payne** | 5 | 4 | 9 | 4 | 4 | K,G,S | リアム・ペイン転落死(2024)。ドコモCM。Billboard Japan ST1億回突破。anan表紙12P特集 |
| 11 | **Shakira** | 5 | 4 | 9 | 4 | 3 | K,G,S | ピケ浮気離婚。脱税事件。「Try Everything」ズートピア主題歌。「Zoo」Spotify Japan Weekly 11位 |
| 12 | **Rihanna** | 5 | 4 | 9 | 4 | 4 | G,S | クリス・ブラウンDV事件。Dior CM。ニベアCM。Spotify Japan 33日チャートイン。Super Bowl復活 |
| 13 | **Whitney Houston** | 5 | 4 | 9 | 3 | 3 | K,G,C | 2012年薬物死が日経・ロイター等で大報道。「I Will Always Love You」カラオケ定番。映画ボディガード81万枚 |
| 14 | **Backstreet Boys** | 4 | 5 | 9 | 3 | 4 | K,C,S | AJリハビリ報道。GU CM。JAL CM「Shape of My Heart」。カラオケDAM多数。Mステ2時間SP |
| 15 | **Billy Joel** | 4 | 5 | 9 | 2 | 3 | K,G,C | ※G_ST=2だがG1+G6=9。正常圧水頭症報道。「ストレンジャー」SONY CM。「Honesty」日本限定人気。カラオケDAM19位 |
| 16 | **Sabrina Carpenter** | 5 | 4 | 9 | 5 | 4 | K,S | 「Espresso」ドラマ主題歌。Spotify Japan Weekly常連。NME Japan・Vogue特集多数。2024年の象徴 |
| 17 | **Charlie Puth** | 4 | 5 | 9 | 4 | 4 | K,S | 「See You Again」ワイスピ主題歌。世界仰天ニュース出演。Spotify Japan 504日チャートイン。日本版MV制作 |
| 18 | **P!NK** | 4 | 5 | 9 | 3 | 3 | C,S | ドラマ『ドクターX』主題歌。月9挿入歌。ディズニー映画主題歌。Spotify Japan 132日チャートイン |
| 19 | **Chester Bennington / Linkin Park** | 5 | 3 | 8 | 5 | 4 | K,G,C | 2017年自殺が世界的大ニュース。MTV追悼番組。2024年新ボーカル復活。Spotify年間ST20億回超(ロック唯一) |
| 20 | **Eminem** | 5 | 3 | 8 | 3 | 5 | K,G,C | 暴力事件・離婚スキャンダル。「Lose Yourself」カラオケ定番。Spotify Wrapped 2025上位。解説動画多数&超高再生 |

### Aランク（G1+G6>=8 AND G_ST<3）【10名】

| # | アーティスト | G1 | G6 | G1+G6 | G_ST | G_YT | ソース | 選定理由 |
|---|---|---|---|---|---|---|---|---|
| 21 | **Eagles** | 4 | 5 | 9 | 2 | 5 | K,C | 「Hotel California」カラオケ定番。ベストヒットUSA 2週連続特集。「Take It Easy」テレ東テーマ曲。解説動画多数&高再生 |
| 22 | **Stevie Wonder** | 3 | 5 | 8 | 3 | 5 | K,G | ※G_ST=3だが境界的。TDK CM・キリンFIRE CM(日本書き下ろし)・日本ハムCM等CM5曲以上。「日本のピアノに号泣」526万再生 |
| 23 | **Olivia Rodrigo** | 4 | 4 | 8 | 4 | 3 | C,S | 「vampire」映画主題歌。ZIP!インタビュー。Spotify Japan「good 4 u」147日チャートイン。Spotify 20億回突破 |
| 24 | **Alicia Keys** | 4 | 4 | 8 | 3 | 3 | K,S | SUMMER SONIC 2025ヘッドライナー。ティファニーCM。ノーメイク宣言。「No One」Spotify10億回突破 |
| 25 | **Green Day** | 5 | 3 | 8 | 3 | 5 | K,C | MAGAトランプ炎上。Super Bowl出演。来日公演。Spotify月間3820万リスナー。解説動画多数&高再生 |
| 26 | **Aerosmith** | 4 | 4 | 8 | 2 | 3 | K,G,C | 2024年引退表明。薬物・バンド危機。「I Don't Want to Miss a Thing」日清カップヌードルCM。カラオケ定番 |
| 27 | **Frank Sinatra** | 3 | 5 | 8 | 2 | 4 | K,C | マフィアとの繋がり。「My Way」SUBARU CM。トヨタ「クラウン」CM。「Strangers in the Night」ドラマ主題歌 |
| 28 | **Diana Ross** | 3 | 5 | 8 | 2 | 4 | K,C | 「If We Hold On Together」カラオケ定番(DAM32曲)。ネスカフェCM。2026年来日公演決定。和訳動画1235万再生 |
| 29 | **Simon & Garfunkel** | 3 | 5 | 8 | 2 | 4 | K,C | 「明日に架ける橋」IHI CM。DAM39曲登録。レコード・コレクターズ76P特集。和訳動画94万再生 |
| 30 | **Bette Midler** | 3 | 5 | 8 | 1 | 4 | K,C | 「The Rose」日本初ドラマ主題歌。映画「余命1ヶ月の花嫁」CM。「アンビリバボー」で大反響。和訳動画2384万再生 |

### Cランク（G1+G6<8）--- MISS予測【3名】

| # | アーティスト | G1 | G6 | G1+G6 | G_ST | G_YT | ソース | 備考 |
|---|---|---|---|---|---|---|---|---|
| 31 | **Benson Boone** | 2 | 3 | 5 | 4 | 2 | K,S | Billboard Japan Hot Overseas 3位だがG1+G6が低すぎる |
| 32 | **Rachel Platten** | 2 | 4 | 6 | 2 | 3 | C,S | 花王CM・大成建設CMあるがゴシップ/知名度不足 |
| 33 | **Boys Town Gang** | 1 | 5 | 6 | 2 | 3 | K,C | 「君の瞳に恋してる」1曲のみ。CM多数だが全て同一曲。ゴシップ皆無 |

---

## 補正メモ

1. **Eric Clapton**: G_ST=2だがG1+G6=10と全候補中最高タイ。Sランクに分類（P3条件は厳密にはG_ST>=3だが、認知度の圧倒的高さを考慮）
2. **Billy Joel**: G_ST=2だがG1+G6=9。同上の理由でSランクに分類
3. **Stevie Wonder**: G_ST=3でS条件を満たすが、G1=3が低めのためAランクに分類（保守的評価）
4. **Olivia Rodrigo/Alicia Keys/Green Day**: G_ST>=3だがS/A判定が微妙なライン。実質的にはS相当だがG_YT=3が低めのためAランクに分類
5. **Rihanna**: エージェント出力ではA判定だったがG1+G6=9, G_ST=4で条件上はSランク。修正済み
6. **Guns N' Roses**: candidate_pool_rawではSソースのみ(1ソース)だが、2026年ガンダム映画タイアップで急上昇。スコア上S条件を明確に満たす

## 推奨制作順序

1. **即制作推奨（S+圧倒的認知度）**: Mariah Carey, Wham!/George Michael, Rolling Stones, Celine Dion
2. **時事性あり（旬を逃さない）**: Sabrina Carpenter(2024-2025トレンド), Guns N' Roses(2026ガンダム), One Direction/Liam Payne(追悼需要)
3. **安定HIT候補**: Coldplay, Beatles, Eminem, Chester Bennington/Linkin Park, Maroon 5
4. **Aランク堅実候補**: Eagles, Stevie Wonder, Frank Sinatra, Diana Ross
