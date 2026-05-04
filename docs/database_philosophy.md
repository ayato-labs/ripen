# Database Management Philosophy

`SharedMemoryServer` におけるデータベース管理の原則を以下に定義します。

## 1. SSoT (Single Source of Truth)
データベースの構造に関する唯一の正解は `src/shared_memory/infra/schema.py` です。
SQLを直接記述するのではなく、この定義ファイルからDDLを生成し、ドキュメントを同期させます。

## 2. Schema-as-Code
スキーマはコード（Pythonオブジェクト）として管理します。これにより：
- バージョン管理（Git）が可能になる
- 静的解析やバリデーションが可能になる
- ドキュメント生成を自動化できる

## 3. バージョン管理 (Migrations)
スキーマの変更は必ず `src/shared_memory/migrations/versions` 以下に新しいマイグレーションスクリプトを作成して行います。
`init_db` 内での直接的な変更（`ALTER TABLE` 等）は禁止します。

## 4. データコントラクト (Data Contract)
本サーバーのデータベーススキーマは、外部のエージェントやツールとの「契約」です。
破壊的な変更（カラムの削除や型変更）を行う場合は、十分な移行期間と下位互換性の維持を検討してください。

## 5. 自動ドキュメント生成
`scripts/generate_db_docs.py` を使用して、常に最新のスキーマ仕様を `docs/db_schema.md` に反映させます。
ドキュメントと実装の乖離を許容しません。
