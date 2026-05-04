# Database Schema Documentation

**Current Schema Version: 1**

This document is automatically generated from `src/shared_memory/infra/schema.py`. **Do not edit manually.**

## Table of Contents
- [entities](#entities)
- [relations](#relations)
- [observations](#observations)
- [embedding_cache](#embedding_cache)
- [bank_files](#bank_files)
- [embeddings](#embeddings)
- [knowledge_metadata](#knowledge_metadata)
- [audit_logs](#audit_logs)
- [snapshots](#snapshots)
- [conflicts](#conflicts)
- [search_stats](#search_stats)
- [tags](#tags)
- [troubleshooting_knowledge](#troubleshooting_knowledge)

<a id='entities'></a>
## Table: `entities`

抽出されたエンティティ（人物、組織、概念等）を保存するテーブル

| Column | Type | PK | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `name` | `TEXT` | ✅ | - | エンティティ名 |
| `entity_type` | `TEXT` |  | - | エンティティの種類 |
| `description` | `TEXT` |  | - | エンティティの説明 |
| `importance` | `INTEGER` |  | `5` | 重要度スコア (1-10) |
| `created_at` | `TIMESTAMP` |  | `CURRENT_TIMESTAMP` | 作成日時 |
| `updated_at` | `TIMESTAMP` |  | `CURRENT_TIMESTAMP` | 更新日時 |
| `created_by` | `TEXT` |  | - | 作成したエージェント/ユーザーID |
| `updated_by` | `TEXT` |  | - | 更新したエージェント/ユーザーID |
| `status` | `TEXT` |  | `'active'` | 状態 (active, archived, deleted) |

<a id='relations'></a>
## Table: `relations`

エンティティ間の関係性を保存するテーブル

| Column | Type | PK | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `subject` | `TEXT` |  | - | 主語となるエンティティ名 |
| `object` | `TEXT` |  | - | 述語となるエンティティ名 |
| `predicate` | `TEXT` |  | - | 関係性の種類 |
| `justification` | `TEXT` |  | - | 関係性の根拠 |
| `created_at` | `TIMESTAMP` |  | `CURRENT_TIMESTAMP` | 作成日時 |
| `created_by` | `TEXT` |  | - | 作成したエージェント/ユーザーID |
| `status` | `TEXT` |  | `'active'` | 状態 |

<a id='observations'></a>
## Table: `observations`

エンティティに関する具体的な観察事実を保存するテーブル

| Column | Type | PK | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | ✅ | - | ID |
| `entity_name` | `TEXT` |  | - | 対象エンティティ名 |
| `content` | `TEXT` |  | - | 観察内容 |
| `timestamp` | `DATETIME` |  | `CURRENT_TIMESTAMP` | 発生/記録日時 |
| `created_by` | `TEXT` |  | - | 作成したエージェント/ユーザーID |
| `status` | `TEXT` |  | `'active'` | 状態 |

<a id='embedding_cache'></a>
## Table: `embedding_cache`

ベクトルの計算結果を再利用するためのキャッシュテーブル

| Column | Type | PK | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `content_hash` | `TEXT` | ✅ | - | 内容のハッシュ値 |
| `vector` | `BLOB` |  | - | ベクトルデータ |
| `model_name` | `TEXT` |  | - | 使用したモデル名 |
| `created_at` | `TIMESTAMP` |  | `CURRENT_TIMESTAMP` | キャッシュ作成日時 |

<a id='bank_files'></a>
## Table: `bank_files`

Memory Bank（ファイルシステム）との同期対象ファイルを保存するテーブル

| Column | Type | PK | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `filename` | `TEXT` | ✅ | - | ファイル名 |
| `content` | `TEXT` |  | - | ファイルの内容 |
| `last_synced` | `DATETIME` |  | `CURRENT_TIMESTAMP` | 最終同期日時 |
| `updated_by` | `TEXT` |  | - | 更新したエージェント/ユーザーID |
| `status` | `TEXT` |  | `'active'` | 状態 |

<a id='embeddings'></a>
## Table: `embeddings`

検索用ベクトルの永続化テーブル

| Column | Type | PK | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `content_id` | `TEXT` | ✅ | - | 対象コンテンツのID (entity名 or id) |
| `vector` | `BLOB` |  | - | ベクトルデータ |
| `model_name` | `TEXT` |  | - | 使用したモデル名 |
| `updated_at` | `DATETIME` |  | `CURRENT_TIMESTAMP` | 更新日時 |

<a id='knowledge_metadata'></a>
## Table: `knowledge_metadata`

知識の忘却曲線や重要度を管理するためのメタデータ

| Column | Type | PK | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `content_id` | `TEXT` | ✅ | - | 対象コンテンツのID |
| `access_count` | `INTEGER` |  | `0` | 累計アクセス回数 |
| `last_accessed` | `DATETIME` |  | `CURRENT_TIMESTAMP` | 最終アクセス日時 |
| `stability` | `REAL` |  | `0.1` | 知識の定着度 |
| `importance_score` | `REAL` |  | `0.1` | 重要度スコア |
| `decay_rate` | `REAL` |  | `0.01` | 忘却率 |

<a id='audit_logs'></a>
## Table: `audit_logs`

DBへの操作ログを記録するテーブル

| Column | Type | PK | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | ✅ | - | ID |
| `table_name` | `TEXT` |  | - | 対象テーブル |
| `content_id` | `TEXT` |  | - | 対象コンテンツID |
| `action` | `TEXT` |  | - | 操作内容 (INSERT, UPDATE, DELETE) |
| `old_data` | `TEXT` |  | - | 変更前のデータ (JSON) |
| `new_data` | `TEXT` |  | - | 変更後のデータ (JSON) |
| `timestamp` | `DATETIME` |  | `CURRENT_TIMESTAMP` | 操作日時 |
| `agent_id` | `TEXT` |  | - | 操作したエージェントID |
| `meta_data` | `TEXT` |  | - | 補足情報 |

<a id='snapshots'></a>
## Table: `snapshots`

データベースの状態を保存したスナップショット情報

| Column | Type | PK | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | ✅ | - | ID |
| `name` | `TEXT` |  | - | スナップショット名 |
| `description` | `TEXT` |  | - | 説明 |
| `timestamp` | `DATETIME` |  | `CURRENT_TIMESTAMP` | 作成日時 |
| `file_path` | `TEXT` |  | - | 保存先のファイルパス |

<a id='conflicts'></a>
## Table: `conflicts`

知識の不整合が検出された場合に記録されるテーブル

| Column | Type | PK | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | ✅ | - | ID |
| `entity_name` | `TEXT` |  | - | 対象エンティティ名 |
| `existing_content` | `TEXT` |  | - | 既存の内容 |
| `new_content` | `TEXT` |  | - | 新しく提案された内容 |
| `reason` | `TEXT` |  | - | 不整合の理由 |
| `agent_id` | `TEXT` |  | - | 不整合を提案したエージェントID |
| `detected_at` | `DATETIME` |  | `CURRENT_TIMESTAMP` | 検出日時 |
| `resolved` | `INTEGER` |  | `0` | 解決済みフラグ (0 or 1) |

<a id='search_stats'></a>
## Table: `search_stats`

検索のヒット率や精度の統計情報を保存するテーブル

| Column | Type | PK | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | ✅ | - | ID |
| `timestamp` | `DATETIME` |  | `CURRENT_TIMESTAMP` | 記録日時 |
| `query` | `TEXT` |  | - | 検索クエリ |
| `results_count` | `INTEGER` |  | - | ヒット件数 |
| `hit_content_ids` | `TEXT` |  | - | ヒットしたコンテンツIDリスト |
| `avg_similarity` | `REAL` |  | `0.0` | 平均類似度 |
| `meta_data` | `TEXT` |  | - | 補足情報 |

<a id='tags'></a>
## Table: `tags`

各コンテンツに付与されたタグを管理するテーブル

| Column | Type | PK | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | ✅ | - | ID |
| `tag` | `TEXT` |  | - | タグ名 |
| `content_id` | `TEXT` |  | - | 対象コンテンツID |
| `content_type` | `TEXT` |  | - | 対象コンテンツの種類 (entity, observation等) |

**Indices:**
- `idx_tags_tag`: `tag`
- `idx_tags_content`: `content_id`

<a id='troubleshooting_knowledge'></a>
## Table: `troubleshooting_knowledge`

トラブルシューティングや既知のバグ・解決策を保存するナレッジベース

| Column | Type | PK | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | ✅ | - | ID |
| `title` | `TEXT` |  | - | タイトル |
| `solution` | `TEXT` |  | - | 解決策の内容 |
| `affected_functions` | `TEXT` |  | - | 影響を受ける機能・関数 |
| `env_metadata` | `TEXT` |  | - | 環境メタデータ |
| `access_count` | `INTEGER` |  | `0` | アクセス回数 |
| `created_at` | `DATETIME` |  | `CURRENT_TIMESTAMP` | 作成日時 |
| `updated_at` | `DATETIME` |  | `CURRENT_TIMESTAMP` | 更新日時 |
