# Ripen マネタイズ・機能セグメンテーション戦略

## 1. 基本方針 (Philosophy)
Ripenは「個人の利便性や少人数での開発体験（Single-player utility）」を**永続的に無料（OSS）**で提供し、「組織の管理・統制・スケール（Multi-player / Enterprise scale）」に対するソリューションを**有料（Commercial / SaaS）**で提供するモデルを採用します。

ユーザーの成功（チームの拡大やリモート開発への移行）が、そのまま収益化のトリガーとなる「Ngrokモデル」を志向します。

## 2. 機能の境界線 (Feature Segmentation)

### 🆓 Ripen Core (無料・OSS版)
ターゲット：個人開発者、LAN内で完結する小規模チーム（2〜5人）
提供価値：摩擦のないAI間ナレッジ共有

- **基本インフラ**: ローカルホストでの SQLite + FAISS 稼働
- **基本共有**: 同一ネットワーク内での SSE ハブ機能（LAN内での共有）
- **AI機能**: バックグラウンドでの知識蒸留（Distillation）、Maturityスコアリング
- **認証**: 簡易的なローカルファイル (`auth.json`) ベースの認証

### 💰 Ripen Enterprise / Cloud (有料版)
ターゲット：フルリモート開発チーム、中規模以上の企業、厳格なセキュリティ要件を持つ組織
提供価値：インターネット越しの安全な同期、高度な統制、インフラ管理からの解放

#### ① インターネット公開機能（Tunneling / Cloud）
- 無料版ではLAN内に閉じていたハブを、インターネット経由で安全に共有可能にする機能。
- 例: `ripen --cloud` のような1コマンドで、セキュアなトンネルを開通させ、リモートワークの同僚と即座に共有環境を構築。

#### ② エンタープライズ認証（Advanced Auth & Security）
- インターネット公開に伴う必須機能としての高度な認証。
- SAML / SSO (Google Workspace, Okta 等) 連携。
- 細かな Role-Based Access Control (RBAC)。退職者アカウントの即時無効化機能。

#### ③ 本格的データベース・グローバル同期 (Advanced DB / Scale)
- 単一の SQLite WAL の限界を超えるためのインフラ拡張。
- クラウドでの PostgreSQL 等のフルマネージドDBサポート、または Turso (LibSQL) を用いた複数拠点間（エッジ）での高速なナレッジ自動同期。
- **Value Prop**: ユーザーが自分でDBサーバーを運用・監視する手間を「ゼロ」にするマネージド体験の提供。

## 3. 配信・運用スタック (Distribution & Operations)

個人開発者としての持続可能性を重視し、グローバルな税制対応やライセンス管理を自動化するスタックを採用します。

### 💳 支払窓口: Merchant of Record (MoR)
- **採用候補**: [Lemon Squeezy](https://www.lemonsqueezy.com/) または [Paddle](https://www.paddle.com/)
# Ripen マネタイズ・機能セグメンテーション戦略

## 1. 基本方針 (Philosophy)
Ripenは「個人の利便性や少人数での開発体験（Single-player utility）」を**永続的に無料（OSS）**で提供し、「組織の管理・統制・スケール（Multi-player / Enterprise scale）」に対するソリューションを**有料（Commercial / SaaS）**で提供するモデルを採用します。

ユーザーの成功（チームの拡大やリモート開発への移行）が、そのまま収益化のトリガーとなる「Ngrokモデル」を志向します。

## 2. 機能の境界線 (Feature Segmentation)

### 🆓 Ripen Core (無料・OSS版)
ターゲット：個人開発者、LAN内で完結する小規模チーム（2〜5人）
提供価値：摩擦のないAI間ナレッジ共有

- **基本インフラ**: ローカルホストでの SQLite + FAISS 稼働
- **基本共有**: 同一ネットワーク内での SSE ハブ機能（LAN内での共有）
- **AI機能**: バックグラウンドでの知識蒸留（Distillation）、Maturityスコアリング
- **認証**: 簡易的なローカルファイル (`auth.json`) ベースの認証

### 💰 Ripen Enterprise / Cloud (有料版)
ターゲット：フルリモート開発チーム、中規模以上の企業、厳格なセキュリティ要件を持つ組織
提供価値：インターネット越しの安全な同期、高度な統制、インフラ管理からの解放

#### ① インターネット公開機能（Tunneling / Cloud）
- 無料版ではLAN内に閉じていたハブを、インターネット経由で安全に共有可能にする機能。
- 例: `ripen --cloud` のような1コマンドで、セキュアなトンネルを開通させ、リモートワークの同僚と即座に共有環境を構築。

#### ② エンタープライズ認証（Advanced Auth & Security）
- インターネット公開に伴う必須機能としての高度な認証。
- SAML / SSO (Google Workspace, Okta 等) 連携。
- 細かな Role-Based Access Control (RBAC)。退職者アカウントの即時無効化機能。

#### ③ 本格的データベース・グローバル同期 (Advanced DB / Scale)
- 単一の SQLite WAL の限界を超えるためのインフラ拡張。
- クラウドでの PostgreSQL 等のフルマネージドDBサポート、または Turso (LibSQL) を用いた複数拠点間（エッジ）での高速なナレッジ自動同期。
- **Value Prop**: ユーザーが自分でDBサーバーを運用・監視する手間を「ゼロ」にするマネージド体験の提供。

## 3. 配信・運用スタック (Distribution & Operations)

個人開発者としての持続可能性を重視し、グローバルな税制対応やライセンス管理を自動化するスタックを採用します。

### 💳 支払窓口: Merchant of Record (MoR)
- **採用候補**: [Lemon Squeezy](https://www.lemonsqueezy.com/) または [Paddle](https://www.paddle.com/)
- **理由**: 世界各国の消費税・VATの計算、徴収、納税代行をすべて委託するため。

### 🔑 ライセンス管理: License-as-a-Service
- **採用候補**: [Keygen.sh](https://keygen.sh/)
- **内容**: APIベースのライセンス認証、デバイス制限（1ライセンスN台まで）、有効期限管理の自動化。

### 📦 配信・リポジトリモデル (Split Repository Strategy)
知的財産の保護とOSSコミュニティへの還元を両立するため、リポジトリを物理的に分離します。

1. **Public Repository (`ripen-core`)**
   - **内容**: コアエンジン、インターフェース定義、ローカルDB実装、CLI基盤。
   - **ライセンス**: AGPL-3.0 (OSS)。誰でも利用・改善・フォーク可能。
   - **役割**: 「シングルプレイヤー」としての利便性を最大化する。

2. **Private Repository (`ripen-enterprise`)**
   - **内容**: 有料版限定プロバイダー（Cloud/Postgres）、SSO連携、ライセンス検証ロジック。
   - **ライセンス**: 商用（非公開）。
   - **役割**: 企業のガバナンス・スケール要求に応える「アドオン」を提供。ソースコードの秘匿によるクラック防止。

### 🔌 統合メカニズム: Dynamic Plugin Architecture
- コア版は、実行環境に `ripen-enterprise` モジュールが存在するかを動的に検出し、存在すればその機能を優先的にインジェクト（DI）します。
- これにより、Public版のコードを汚さずに、商用機能へのシームレスなアップグレードを実現します。

## 4. 今後のアーキテクチャへの影響（技術的布石）
このマネタイズ戦略を将来スムーズに実行するため、オープンソース版のコードベースにおいて以下のアーキテクチャ準備を並行して進めます。

1. **DBの抽象化 (Repository Pattern)**:
   現在 SQLite (FTS5) に強く依存しているデータアクセス層を抽象化し、将来的に PostgreSQL や Turso 用のアダプターをシームレスに差し込める設計にしておく。
2. **認証ミドルウェアのプラガブル化**:
   現状のローカル認証機能を、将来 SSO などの外部認証モジュールをプラグインとして組み込めるように疎結合にしておく。
