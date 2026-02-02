from graphlib import TopologicalSorter, CycleError
from logging import getLogger

logger = getLogger(__name__)


class DependencyResolver:
    """データ投入時の依存関係を解決するためのクラス"""

    def resolve_insertion_order(self, datamodels, schema):
        """
        DataModelリストを依存関係に基づいて並び替える

        優先順位:
        1. DataModelの明示的依存関係 (dependencies) - 最優先
        2. FK依存関係 - 循環を引き起こさない範囲で考慮

        Args:
            datamodels: DataModelのイテラブル
            schema: Schema オブジェクト

        Returns:
            list[DataModel]: 依存関係順に並び替えられたDataModelリスト

        Raises:
            ValueError: 明示的依存関係で循環依存が検出された場合
        """
        # DataModelをリストに変換し、キーマップを作成
        datamodels_list = list(datamodels)
        datamodel_map = {}

        # 明示的依存関係を収集
        explicit_dependencies = {}
        fk_dependencies = {}

        for dm in datamodels_list:
            key = f"{dm.schema_name}@{dm.table_name}"
            datamodel_map[key] = dm
            explicit_dependencies[key] = set()
            fk_dependencies[key] = set()

        # Phase 1: 明示的依存関係を収集
        for dm in datamodels_list:
            key = f"{dm.schema_name}@{dm.table_name}"

            for dep in dm.dependencies:
                # 同じデータセット内にある依存関係のみ追加
                if any(f"{target_dm.schema_name}@{target_dm.table_name}" == dep
                      for target_dm in datamodels_list):
                    explicit_dependencies[key].add(dep)
                    logger.debug(f"Explicit dependency: {key} -> {dep}")

        # Phase 2: 明示的依存関係で循環チェック（循環があればエラー）
        try:
            ts_explicit = TopologicalSorter(explicit_dependencies)
            list(ts_explicit.static_order())
            logger.info("Explicit dependencies validation passed (no cycles)")
        except CycleError as e:
            logger.error(f"Circular dependency detected in explicit dependencies: {e}")
            raise ValueError(f"Circular dependency detected in explicit dependencies: {e}")

        # Phase 3: FK依存関係を収集
        for dm in datamodels_list:
            key = f"{dm.schema_name}@{dm.table_name}"

            if dm.table_name in schema.tables:
                table = schema.tables[dm.table_name]
                for relation in table.relations:
                    target_key = f"{relation.target.schema_name}@{relation.target.table_name}"

                    # 自己参照リレーションを除外
                    if target_key == key:
                        logger.debug(f"Skipping self-reference FK: {key} -> {target_key}")
                        continue

                    # 同じデータセット内にある依存関係のみ追加
                    if any(target_dm.schema_name == relation.target.schema_name and
                          target_dm.table_name == relation.target.table_name
                          for target_dm in datamodels_list):
                        fk_dependencies[key].add(target_key)
                        logger.debug(f"FK dependency candidate: {key} -> {target_key}")

        # Phase 4: FK依存関係を明示的依存関係にマージ（循環を引き起こすFKは無視）
        combined_dependencies = {k: v.copy() for k, v in explicit_dependencies.items()}
        ignored_fks = []

        for key, fk_deps in fk_dependencies.items():
            for fk_dep in fk_deps:
                # FK依存関係を試しに追加
                test_dependencies = {k: v.copy() for k, v in combined_dependencies.items()}
                test_dependencies[key].add(fk_dep)

                try:
                    # 循環チェック
                    ts_test = TopologicalSorter(test_dependencies)
                    list(ts_test.static_order())
                    # 循環しなければ正式に追加
                    combined_dependencies[key].add(fk_dep)
                    logger.debug(f"FK dependency added: {key} -> {fk_dep}")
                except CycleError:
                    # 循環するFKは無視（警告のみ）
                    ignored_fks.append((key, fk_dep))
                    logger.warning(f"Ignoring FK dependency (would cause cycle): {key} -> {fk_dep}")

        # Phase 5: 最終的な順序を解決
        try:
            ts = TopologicalSorter(combined_dependencies)
            ordered_keys = list(ts.static_order())

            # DataModelオブジェクトの順序で返す
            result = [datamodel_map[key] for key in ordered_keys if key in datamodel_map]

            logger.info(f"Resolved insertion order: {[f'{dm.schema_name}@{dm.table_name}' for dm in result]}")
            if ignored_fks:
                logger.info(f"Ignored {len(ignored_fks)} FK dependencies to avoid cycles")

            return result

        except CycleError as e:
            # ここには到達しないはずだが、念のため
            logger.error(f"Unexpected circular dependency detected: {e}")
            raise ValueError(f"Circular dependency detected: {e}")

    def validate_dependencies(self, datamodels, schema):
        """
        依存関係の妥当性を検証する

        Args:
            datamodels: DataModelのイテラブル
            schema: Schema オブジェクト

        Returns:
            list[str]: 警告メッセージのリスト
        """
        warnings = []
        datamodels_list = list(datamodels)
        available_tables = {f"{dm.schema_name}@{dm.table_name}" for dm in datamodels_list}

        for dm in datamodels_list:
            # 明示的依存関係の存在チェック
            for dep in dm.dependencies:
                if dep not in available_tables:
                    warnings.append(f"Table {dm.schema_name}@{dm.table_name} depends on {dep}, but it's not in the data insertion set")

            # FK依存関係の存在チェック
            if dm.table_name in schema.tables:
                table = schema.tables[dm.table_name]
                for relation in table.relations:
                    target_key = f"{relation.target.schema_name}@{relation.target.table_name}"
                    current_key = f"{dm.schema_name}@{dm.table_name}"
                    
                    # 自己参照リレーションを除外
                    if target_key == current_key:
                        continue
                    
                    if target_key not in available_tables:
                        warnings.append(f"Table {dm.schema_name}@{dm.table_name} has FK to {target_key}, but it's not in the data insertion set")

        return warnings
