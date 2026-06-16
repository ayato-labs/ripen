import pytest

from ripen.core import logic, search
from ripen.infra.database import async_get_connection
from ripen.ops import management


@pytest.mark.asyncio
@pytest.mark.integration
async def test_save_and_hybrid_search_flow(uow):
    """
    Integration Test: 保存からハイブリッド検索、知識合成までの一連のフローを検証。
    """
    from ripen.common.utils import get_logger
    log = get_logger("tests.integration")

    # 1. 保存
    entities = [{"name": "IntegrationNode", "description": "Part of a larger system"}]
    observations = [{"entity_name": "IntegrationNode", "content": "Integration testing is crucial"}]
    bank_files = {"integration.md": "Bank file content for integration"}

    log.info("Step 1: Saving memory core...")
    result = await logic.save_memory_core(
        entities=entities, observations=observations, bank_files=bank_files
    )
    log.info(f"Save result: {result}")

    # 2. 検索 (キーワード + セマンティック)
    log.info("Step 2: Performing hybrid search...")
    graph_data, bank_data = await search.perform_search("Integration", uow)
    log.info(
        f"Search results: graph_entities={len(graph_data['entities'])}, "
        f"bank_files={len(bank_data)}"
    )

    # エンティティが見つかっているか
    entity_names = [e["name"] for e in graph_data["entities"]]
    assert "IntegrationNode" in entity_names, (
        f"IntegrationNode not found in {entity_names}. Graph data: {graph_data}"
    )

    # 観察が含まれているか
    obs_contents = [o["content"] for o in graph_data["observations"]]
    assert "Integration testing is crucial" in obs_contents, (
        f"Observation not found in {obs_contents}"
    )

    # バンクファイルが含まれているか
    assert "integration.md" in bank_data, f"integration.md not found in {bank_data.keys()}"

    # 3. 知識合成
    log.info("Step 3: Synthesizing knowledge...")
    summary = await search.synthesize_knowledge("IntegrationNode", uow)
    log.info(f"Synthesis summary: {summary[:100]}...")
    assert len(summary) > 0

    # 4. 監査ログの検証 (裏取り)
    log.info("Step 4: Verifying audit logs...")
    audit_logs = await management.get_audit_history_logic(10, None, uow)
    tables_in_audit = [log["table"] for log in audit_logs]
    assert "entities" in tables_in_audit, f"'entities' not in audit logs: {tables_in_audit}"
    assert "bank_files" in tables_in_audit, f"'bank_files' not in audit logs: {tables_in_audit}"



@pytest.mark.asyncio
@pytest.mark.integration
async def test_conflict_and_recovery_flow(uow):
    """
    Integration Test: 衝突検知と解決フローを検証。
    """
    from ripen.common.utils import get_logger
    log = get_logger("tests.integration")

    # 1. 初期データ保存 (観察事項を1つ入れておく)
    log.info("Step 1: Saving initial fact...")
    await logic.save_memory_core(
        entities=[{"name": "SkyNode", "description": "The sky above us"}],
        observations=[{"entity_name": "SkyNode", "content": "The sky is always blue."}],
    )

    # 2. 衝突するデータの保存試行
    log.info("Step 2: Attempting to save conflicting fact...")
    result = await logic.save_memory_core(
        observations=[{"entity_name": "SkyNode", "content": "The sky is always green."}]
    )
    log.info(f"Conflict save result: {result}")
    assert "CONFLICTS DETECTED" in result, f"Expected conflict not detected. Result: {result}"

    # 3. 未解決の衝突リスト取得
    log.info("Step 3: Fetching unresolved conflicts...")
    conflicts = await management.get_unresolved_conflicts_logic(uow)
    log.info(f"Found {len(conflicts)} unresolved conflicts.")
    assert len(conflicts) > 0
    target_conflict = next((c for c in conflicts if c["entity"] == "SkyNode"), None)
    assert target_conflict is not None, f"Conflict for SkyNode not found in {conflicts}"
    
    # 4. 衝突の解決 (Approve)
    log.info(f"Step 4: Resolving conflict {target_conflict['id']} with 'approve'...")
    await management.resolve_conflict_logic(target_conflict["id"], "approve", uow)

    # 5. 解決後の確認 (裏取り)
    log.info("Step 5: Verifying resolution in database...")
    async with await async_get_connection() as conn:
        # observations に追加されているか
        async with conn.execute(
            "SELECT content FROM observations WHERE entity_name='SkyNode' "
            "AND content='The sky is always green.'"
        ) as cursor:
            row = await cursor.fetchone()
            assert row is not None, "Approved observation not found in database."

        # 衝突が解決済みになっているか
        async with conn.execute(
            "SELECT resolved FROM conflicts WHERE id=?", (target_conflict["id"],)
        ) as cursor:
            row = await cursor.fetchone()
            assert row[0] == 1, "Conflict still marked as unresolved."

