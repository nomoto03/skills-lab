---
name: youtube-summary
description: Use when the user shares a YouTube URL and wants its content summarized or explained — triggers include "このYouTube要約して", "この動画の内容を教えて", "動画をまとめて", "summarize this YouTube video", or a YouTube link pasted together with a summarization request. Fetches the video's subtitles with a bundled yt-dlp script, silently corrects likely speech-recognition errors, and returns a structured Japanese summary in chat.
---

# YouTube Summary

YouTube動画のURLから字幕を取得し、聞き取りミスを補正した日本語要約をチャットに返す。

## フロー

1. **字幕取得**: セッションのスクラッチパッドを出力先にしてスクリプトを実行する:

   ```
   python <このスキルのベースディレクトリ>/scripts/fetch_transcript.py "<URL>" --out "<スクラッチパッド>/youtube-summary"
   ```

   成功時(exit 0)はstdoutにメタデータJSONが出る:
   `title` / `channel` / `duration_human` / `language` /
   `subtitle_type`(manual|auto|translated)/ `transcript_path` / `char_count`

2. **エラー分岐**(stderrの `ERROR:<CODE>` と終了コードで判定):
   - `YTDLP_MISSING`(exit 3): `pip install yt-dlp` を実行して**1回だけ**リトライ
   - `NO_SUBTITLES`(exit 2): 「この動画には字幕がないため要約できない」と報告して終了。
     内容を推測・捏造しない
   - `VIDEO_UNAVAILABLE`(exit 4): 非公開・年齢制限・地域制限等で取得できない旨を
     エラー内容とともに報告して終了
   - その他(exit 1): **1回だけ**リトライし、2回目も失敗したらエラー内容を報告して終了。
     無限リトライ禁止

3. **transcript読み込み**: `transcript_path` のファイルを読む。
   `char_count` が **80,000 を超える**場合は Read の offset/limit で分割して読み、
   チャンクごとに中間要約を作ってから最後に統合する

4. **聞き取りミス補正**: 文脈から明らかな誤認(同音語の取り違え、固有名詞の表記揺れ)は
   黙って直した内容で要約する。確信が持てない重要語のみ「(原文: ○○)」と注記する。
   補正箇所の一覧は出さない

5. **要約出力**: 動画が何語でも**日本語**で、下のテンプレでチャットに出力する。
   ファイル保存はしない

## 要約テンプレ

```markdown
## 要約: <動画タイトル>
<チャンネル名> / <長さ> / <字幕種別: 手動字幕 or 自動生成字幕>
※自動生成字幕ベースのため、固有名詞などに誤りが残っている可能性があります
(↑この注記行は subtitle_type が auto または translated の場合のみ)

**概要**
2〜3文。

**主要ポイント**
- 内容量に応じて3〜8点の箇条書き

**結論・所感**
話者の結論と、要約者としての短い所感。
```

## 注意

- プレイリストURLでも対象は動画単体(`v=` の動画のみ)。一括要約はしない
- 字幕なし動画への音声認識フォールバックはスコープ外
