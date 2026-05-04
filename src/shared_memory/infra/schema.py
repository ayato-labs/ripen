from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class Column:
    name: str
    type: str
    description: str
    is_primary_key: bool = False
    is_autoincrement: bool = False
    is_unique: bool = False
    default: Optional[str] = None
    not_null: bool = False

@dataclass
class Index:
    name: str
    columns: List[str]
    is_unique: bool = False

@dataclass
class Table:
    name: str
    description: str
    columns: List[Column]
    indices: List[Index] = None
    constraints: List[str] = None

# --- SSoT: Schema Definition ---
TABLES: Dict[str, Table] = {
    "entities": Table(
        name="entities",
        description="抽出されたエンティティ（人物、組織、概念等）を保存するテーブル",
        columns=[
            Column("name", "TEXT", "エンティティ名", is_primary_key=True),
            Column("entity_type", "TEXT", "エンティティの種類"),
            Column("description", "TEXT", "エンティティの説明"),
            Column("importance", "INTEGER", "重要度スコア (1-10)", default="5"),
            Column("created_at", "TIMESTAMP", "作成日時", default="CURRENT_TIMESTAMP"),
            Column("updated_at", "TIMESTAMP", "更新日時", default="CURRENT_TIMESTAMP"),
            Column("created_by", "TEXT", "作成したエージェント/ユーザーID"),
            Column("updated_by", "TEXT", "更新したエージェント/ユーザーID"),
            Column("status", "TEXT", "状態 (active, archived, deleted)", default="'active'"),
        ]
    ),
    "relations": Table(
        name="relations",
        description="エンティティ間の関係性を保存するテーブル",
        columns=[
            Column("subject", "TEXT", "主語となるエンティティ名"),
            Column("object", "TEXT", "述語となるエンティティ名"),
            Column("predicate", "TEXT", "関係性の種類"),
            Column("justification", "TEXT", "関係性の根拠"),
            Column("created_at", "TIMESTAMP", "作成日時", default="CURRENT_TIMESTAMP"),
            Column("created_by", "TEXT", "作成したエージェント/ユーザーID"),
            Column("status", "TEXT", "状態", default="'active'"),
        ],
        constraints=["PRIMARY KEY (subject, object, predicate)"]
    ),
    "observations": Table(
        name="observations",
        description="エンティティに関する具体的な観察事実を保存するテーブル",
        columns=[
            Column("id", "INTEGER", "ID", is_primary_key=True, is_autoincrement=True),
            Column("entity_name", "TEXT", "対象エンティティ名"),
            Column("content", "TEXT", "観察内容"),
            Column("timestamp", "DATETIME", "発生/記録日時", default="CURRENT_TIMESTAMP"),
            Column("created_by", "TEXT", "作成したエージェント/ユーザーID"),
            Column("status", "TEXT", "状態", default="'active'"),
        ]
    ),
    "embedding_cache": Table(
        name="embedding_cache",
        description="ベクトルの計算結果を再利用するためのキャッシュテーブル",
        columns=[
            Column("content_hash", "TEXT", "内容のハッシュ値", is_primary_key=True),
            Column("vector", "BLOB", "ベクトルデータ"),
            Column("model_name", "TEXT", "使用したモデル名"),
            Column("created_at", "TIMESTAMP", "キャッシュ作成日時", default="CURRENT_TIMESTAMP"),
        ]
    ),
    "bank_files": Table(
        name="bank_files",
        description="Memory Bank（ファイルシステム）との同期対象ファイルを保存するテーブル",
        columns=[
            Column("filename", "TEXT", "ファイル名", is_primary_key=True),
            Column("content", "TEXT", "ファイルの内容"),
            Column("last_synced", "DATETIME", "最終同期日時", default="CURRENT_TIMESTAMP"),
            Column("updated_by", "TEXT", "更新したエージェント/ユーザーID"),
            Column("status", "TEXT", "状態", default="'active'"),
        ]
    ),
    "embeddings": Table(
        name="embeddings",
        description="検索用ベクトルの永続化テーブル",
        columns=[
            Column("content_id", "TEXT", "対象コンテンツのID (entity名 or id)", is_primary_key=True),
            Column("vector", "BLOB", "ベクトルデータ"),
            Column("model_name", "TEXT", "使用したモデル名"),
            Column("updated_at", "DATETIME", "更新日時", default="CURRENT_TIMESTAMP"),
        ]
    ),
    "knowledge_metadata": Table(
        name="knowledge_metadata",
        description="知識の忘却曲線や重要度を管理するためのメタデータ",
        columns=[
            Column("content_id", "TEXT", "対象コンテンツのID", is_primary_key=True),
            Column("access_count", "INTEGER", "累計アクセス回数", default="0"),
            Column("last_accessed", "DATETIME", "最終アクセス日時", default="CURRENT_TIMESTAMP"),
            Column("stability", "REAL", "知識の定着度", default="0.1"),
            Column("importance_score", "REAL", "重要度スコア", default="0.1"),
            Column("decay_rate", "REAL", "忘却率", default="0.01"),
        ]
    ),
    "audit_logs": Table(
        name="audit_logs",
        description="DBへの操作ログを記録するテーブル",
        columns=[
            Column("id", "INTEGER", "ID", is_primary_key=True, is_autoincrement=True),
            Column("table_name", "TEXT", "対象テーブル"),
            Column("content_id", "TEXT", "対象コンテンツID"),
            Column("action", "TEXT", "操作内容 (INSERT, UPDATE, DELETE)"),
            Column("old_data", "TEXT", "変更前のデータ (JSON)"),
            Column("new_data", "TEXT", "変更後のデータ (JSON)"),
            Column("timestamp", "DATETIME", "操作日時", default="CURRENT_TIMESTAMP"),
            Column("agent_id", "TEXT", "操作したエージェントID"),
            Column("meta_data", "TEXT", "補足情報"),
        ]
    ),
    "snapshots": Table(
        name="snapshots",
        description="データベースの状態を保存したスナップショット情報",
        columns=[
            Column("id", "INTEGER", "ID", is_primary_key=True, is_autoincrement=True),
            Column("name", "TEXT", "スナップショット名", not_null=True),
            Column("description", "TEXT", "説明"),
            Column("timestamp", "DATETIME", "作成日時", default="CURRENT_TIMESTAMP"),
            Column("file_path", "TEXT", "保存先のファイルパス", not_null=True),
        ]
    ),
    "conflicts": Table(
        name="conflicts",
        description="知識の不整合が検出された場合に記録されるテーブル",
        columns=[
            Column("id", "INTEGER", "ID", is_primary_key=True, is_autoincrement=True),
            Column("entity_name", "TEXT", "対象エンティティ名", not_null=True),
            Column("existing_content", "TEXT", "既存の内容", not_null=True),
            Column("new_content", "TEXT", "新しく提案された内容", not_null=True),
            Column("reason", "TEXT", "不整合の理由"),
            Column("agent_id", "TEXT", "不整合を提案したエージェントID"),
            Column("detected_at", "DATETIME", "検出日時", default="CURRENT_TIMESTAMP"),
            Column("resolved", "INTEGER", "解決済みフラグ (0 or 1)", default="0"),
        ]
    ),
    "search_stats": Table(
        name="search_stats",
        description="検索のヒット率や精度の統計情報を保存するテーブル",
        columns=[
            Column("id", "INTEGER", "ID", is_primary_key=True, is_autoincrement=True),
            Column("timestamp", "DATETIME", "記録日時", default="CURRENT_TIMESTAMP"),
            Column("query", "TEXT", "検索クエリ"),
            Column("results_count", "INTEGER", "ヒット件数"),
            Column("hit_content_ids", "TEXT", "ヒットしたコンテンツIDリスト"),
            Column("avg_similarity", "REAL", "平均類似度", default="0.0"),
            Column("meta_data", "TEXT", "補足情報"),
        ]
    ),
    "tags": Table(
        name="tags",
        description="各コンテンツに付与されたタグを管理するテーブル",
        columns=[
            Column("id", "INTEGER", "ID", is_primary_key=True, is_autoincrement=True),
            Column("tag", "TEXT", "タグ名", not_null=True),
            Column("content_id", "TEXT", "対象コンテンツID", not_null=True),
            Column("content_type", "TEXT", "対象コンテンツの種類 (entity, observation等)", not_null=True),
        ],
        indices=[
            Index("idx_tags_tag", ["tag"]),
            Index("idx_tags_content", ["content_id"]),
        ],
        constraints=["UNIQUE(tag, content_id, content_type)"]
    ),
    "troubleshooting_knowledge": Table(
        name="troubleshooting_knowledge",
        description="トラブルシューティングや既知のバグ・解決策を保存するナレッジベース",
        columns=[
            Column("id", "INTEGER", "ID", is_primary_key=True, is_autoincrement=True),
            Column("title", "TEXT", "タイトル", not_null=True),
            Column("solution", "TEXT", "解決策の内容", not_null=True),
            Column("affected_functions", "TEXT", "影響を受ける機能・関数"),
            Column("env_metadata", "TEXT", "環境メタデータ"),
            Column("access_count", "INTEGER", "アクセス回数", default="0"),
            Column("created_at", "DATETIME", "作成日時", default="CURRENT_TIMESTAMP"),
            Column("updated_at", "DATETIME", "更新日時", default="CURRENT_TIMESTAMP"),
        ]
    )
}

# FTS5 Virtual Tables
FTS_TABLES = {
    "entities_fts": "USING fts5(name, description, content='entities')",
    "observations_fts": "USING fts5(entity_name, content, content='observations', content_rowid='id')",
    "bank_files_fts": "USING fts5(filename, content, content='bank_files')"
}

# FTS Triggers
FTS_TRIGGERS = [
    # Entities
    \"\"\"
    CREATE TRIGGER IF NOT EXISTS entities_ai AFTER INSERT ON entities BEGIN
        INSERT INTO entities_fts(rowid, name, description) VALUES (new.rowid, new.name, new.description);
    END;
    \"\"\",
    \"\"\"
    CREATE TRIGGER IF NOT EXISTS entities_ad AFTER DELETE ON entities BEGIN
        INSERT INTO entities_fts(entities_fts, rowid, name, description) VALUES('delete', old.rowid, old.name, old.description);
    END;
    \"\"\",
    \"\"\"
    CREATE TRIGGER IF NOT EXISTS entities_au AFTER UPDATE ON entities BEGIN
        INSERT INTO entities_fts(entities_fts, rowid, name, description) VALUES('delete', old.rowid, old.name, old.description);
        INSERT INTO entities_fts(rowid, name, description) VALUES (new.rowid, new.name, new.description);
    END;
    \"\"\",
    # Observations
    \"\"\"
    CREATE TRIGGER IF NOT EXISTS observations_ai AFTER INSERT ON observations BEGIN
        INSERT INTO observations_fts(rowid, entity_name, content) VALUES (new.id, new.entity_name, new.content);
    END;
    \"\"\",
    \"\"\"
    CREATE TRIGGER IF NOT EXISTS observations_ad AFTER DELETE ON observations BEGIN
        INSERT INTO observations_fts(observations_fts, rowid, entity_name, content) VALUES('delete', old.id, old.entity_name, old.content);
    END;
    \"\"\",
    \"\"\"
    CREATE TRIGGER IF NOT EXISTS observations_au AFTER UPDATE ON observations BEGIN
        INSERT INTO observations_fts(observations_fts, rowid, entity_name, content) VALUES('delete', old.id, old.entity_name, old.content);
        INSERT INTO observations_fts(rowid, entity_name, content) VALUES (new.id, new.entity_name, new.content);
    END;
    \"\"\",
    # Bank Files
    \"\"\"
    CREATE TRIGGER IF NOT EXISTS bank_files_ai AFTER INSERT ON bank_files BEGIN
        INSERT INTO bank_files_fts(rowid, filename, content) VALUES (new.rowid, new.filename, new.content);
    END;
    \"\"\",
    \"\"\"
    CREATE TRIGGER IF NOT EXISTS bank_files_ad AFTER DELETE ON bank_files BEGIN
        INSERT INTO bank_files_fts(bank_files_fts, rowid, filename, content) VALUES('delete', old.rowid, old.filename, old.content);
    END;
    \"\"\",
    \"\"\"
    CREATE TRIGGER IF NOT EXISTS bank_files_au AFTER UPDATE ON bank_files BEGIN
        INSERT INTO bank_files_fts(bank_files_fts, rowid, filename, content) VALUES('delete', old.rowid, old.filename, old.content);
        INSERT INTO bank_files_fts(rowid, filename, content) VALUES (new.rowid, new.filename, new.content);
    END;
    \"\"\"
]

# 現状のスキーマバージョン (migrations/manager.py と同期)
CURRENT_SCHEMA_VERSION = 1

def get_create_table_sql(table_name: str) -> str:
    \"\"\"テーブル定義から SQLite 用の CREATE TABLE 文を生成する\"\"\"
    table = TABLES[table_name]
    cols = []
    for col in table.columns:
        line = f"{col.name} {col.type}"
        if col.is_primary_key:
            line += " PRIMARY KEY"
            if col.is_autoincrement:
                line += " AUTOINCREMENT"
        if col.not_null:
            line += " NOT NULL"
        if col.is_unique:
            line += " UNIQUE"
        if col.default:
            line += f" DEFAULT {col.default}"
        cols.append(line)
    
    if table.constraints:
        cols.extend(table.constraints)
    
    return f"CREATE TABLE IF NOT EXISTS {table.name} (\n    " + ",\n    ".join(cols) + "\n)"
