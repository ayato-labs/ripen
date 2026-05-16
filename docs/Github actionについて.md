# GitHub Actions の設計と使用方法

## 概要
Ripen プロジェクトでは、CI/CD パイプラインの効率化と品質保証のため、ワークフローを一本化（直列化）し、重複を排除した構成を採用しています。

## ワークフロー構成

### 1. CI/CD パイプライン (`main.yml`)
これがプロジェクトのメインパイプラインであり、以下の 3 つのジョブが直列に実行されます。

- **Job 1: Lint & Test**
  - **トリガー**: 全ブランチへの Push、および `main`, `develop` への Pull Request。
  - **内容**: 
    - `uv sync --all-extras` による依存関係のインストール。
    - `ruff` による Python コードの静的解析。
    - `djlint` による HTML の静的解析。
    - `pytest` によるテストの実行（PR時はユニットテストのみ、mainへのPush時は結合・システムテストを含むフルテスト）。
- **Job 2: Semantic Release**
  - **トリガー**: `main` ブランチへの Push のみ、かつ Job 1 が成功した場合。
  - **内容**: `python-semantic-release` を使用した自動バージョニングとチェンジログの生成。
- **Job 3: Build Windows Assets**
  - **トリガー**: `main` ブランチへの Push のみ、かつ Job 2 で新しいリリースが発行された場合。
  - **内容**: PyInstaller を使用して Windows 用のスタンドアロンバイナリ（EXE）をビルドし、GitHub Release にアップロードします。

### 2. CLA チェック (`cla-check.yml`)
- **トリガー**: Pull Request の作成・更新。
- **内容**: 外部貢献者が Contributor License Agreement（CLA）に署名しているかを確認する独立したボット連携です。

## 削除されたレガシーファイル
以下のファイルは、`main.yml` への統合に伴い削除されました。
- `ci.yml` (処理を `main.yml` に統合)
- `release.yml` (処理を `main.yml` に統合)
- `build-binaries.yml` (処理を `main.yml` に統合)

---
この設計により、テストが成功しない限りリリースやビルドが走らないことが保証され、品質が担保されます。
