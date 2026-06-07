# ADR-0002: 自動登録機能（RipenInstaller.exe / register.py）の完全廃止とコード削除

- **Date**: 2026-05-24
- **Status**: Proposed
- **Deciders**: ayato-labs (Human), Antigravity (Agent)

## Context

Ripen には、Cursor や Claude Desktop 等の IDE 設定ファイル（`mcp_config.json` 等）を自動探索し、Ripen MCP サーバーの起動構成を自動で追加する機能（`RipenInstaller.exe`、および `register.py` / `unregister.py`）が存在していました。

しかし、この機能には以下の設計的・実用的な課題がありました：

1. **責務の分離（Separation of Concerns）の違反**: Ripen は「Streamable HTTP Hub（サーバー）」であり、サーバー側バイナリがクライアント側（IDE）のプライベートな設定ファイルを探索して改ざんするのは責務の境界を越えていました。
2. **セキュリティおよび誤検知リスク**: アプリケーションが他アプリの構成ファイルを書き換える挙動は、Windows Defender などのセキュリティソフトから「不正な改ざん（トロイの木馬）」と誤検知されるリスクが極めて高い状態でした。
3. **メンテナンスコストの増大**: 各 IDE のアップデートや、Cline/Roo Code 等の派生ツールの増加により、設定ファイルのパスやスキーマが頻繁に変更され、自動登録ロジックの保守負荷が非常に高くなっていました。
4. **バイナリ肥大化**: `RipenInstaller.exe` を個別に `--onefile` ビルドすることで、リリースバイナリのアセット数が無駄に増え、アセット全体のディスク容量増加や CI/CD でのビルド時間増大を招いていました。

## Decision

自動登録機能および関連するすべてのコード（`register.py`, `unregister.py`）を完全に廃止・削除します。

- 関連するエントリーポイント（`ripen-register`, `ripen-unregister`）を `pyproject.toml` から削除。
- GitHub Actions のビルド・リリースアセットから `RipenInstaller.exe` を除外。
- IDE への登録は、`README.md` やダッシュボード（`http://localhost:8377/dashboard`）に設定用の JSON スニペットを明記し、**開発者による手動コピペ接続**に一本化します。

## Consequences

### Positive
- **セキュリティ・安全性の向上**: 設定ファイルを勝手に書き換えないため、セキュリティソフトによる誤検知リスクを完全に排除できます。
- **メンテナンス負荷の削減**: IDE の仕様変更に伴う自動登録ロジックの修正が一切不要になります。
- **リリースバイナリの軽量化**: ビルドする `.exe` ファイルが3つから2つ（将来的には1つ）へ削減され、リリース容量が減少し、CI ビルド時間が短縮されます。
- **アーキテクチャの健全化**: サーバーとクライアントの責務の境界が明確になります。

### Negative / Risks
- 初回セットアップ時に、ユーザーが設定ファイルに数行の JSON を手動でコピー＆ペーストするステップが発生します（ただし、開発者にとっては標準的な手順であり、摩擦は最小限と判断します）。

## References
- Issue: #168
- PR: (作成予定)
