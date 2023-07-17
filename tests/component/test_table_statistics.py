import logging
import os

import pandas as pd

from secretflow.component.data_utils import DistDataType, gen_table_statistic_report
from secretflow.component.stats.table_statistics import table_statistics_comp
from secretflow.protos.component.data_pb2 import (
    DistData,
    IndividualTable,
    TableSchema,
    VerticalTable,
)
from secretflow.protos.component.evaluation_pb2 import NodeEvalParam
from secretflow.protos.component.report_pb2 import Report
from secretflow.stats.table_statistics import table_statistics


def test_table_statistics_comp(comp_prod_sf_cluster_config):
    """
    This test shows that table statistics works on both pandas and VDataFrame,
        i.e. all APIs align and the result is correct.
    """
    alice_input_path = "test_table_statistics/alice.csv"
    bob_input_path = "test_table_statistics/bob.csv"

    self_party = comp_prod_sf_cluster_config.private_config.self_party
    local_fs_wd = comp_prod_sf_cluster_config.private_config.storage_config.local_fs.wd

    test_data = pd.DataFrame(
        {"a": [9, 6, 5, 5], "b": [5, 5, 6, 7], "c": [1, 1, 2, 4], "d": [11, 55, 1, 99]}
    )
    test_data = test_data.astype("float32")

    if self_party == "alice":
        df_alice = test_data.iloc[:, :2]
        os.makedirs(os.path.join(local_fs_wd, "test_table_statistics"), exist_ok=True)
        df_alice.to_csv(os.path.join(local_fs_wd, alice_input_path), index=False)
    elif self_party == "bob":
        df_bob = test_data.iloc[:, 2:]
        os.makedirs(os.path.join(local_fs_wd, "test_table_statistics"), exist_ok=True)
        df_bob.to_csv(os.path.join(local_fs_wd, bob_input_path), index=False)

    param = NodeEvalParam(
        domain="stats",
        name="table_statistics",
        version="0.0.1",
        attr_paths=[],
        attrs=[],
        inputs=[
            DistData(
                name="input_data",
                type=str(DistDataType.VERTICAL_TABLE),
                data_refs=[
                    DistData.DataRef(uri=alice_input_path, party="alice", format="csv"),
                    DistData.DataRef(uri=bob_input_path, party="bob", format="csv"),
                ],
            )
        ],
        output_uris=[""],
    )
    meta = VerticalTable(
        schemas=[
            TableSchema(
                types=["f32", "f32"],
                features=["a", "b"],
            ),
            TableSchema(
                types=["f32", "f32"],
                features=["c", "d"],
            ),
        ],
    )
    param.inputs[0].meta.Pack(meta)

    res = table_statistics_comp.eval(
        param=param, cluster_config=comp_prod_sf_cluster_config
    )
    comp_ret = Report()
    res.outputs[0].meta.Unpack(comp_ret)
    logging.info(comp_ret)
    assert comp_ret == gen_table_statistic_report(table_statistics(test_data))


def test_table_statistics_individual_comp(comp_prod_sf_cluster_config):
    """
    This test shows that table statistics works on both pandas and VDataFrame,
        i.e. all APIs align and the result is correct.
    """
    alice_input_path = "test_table_statistics/alice.csv"

    self_party = comp_prod_sf_cluster_config.private_config.self_party
    local_fs_wd = comp_prod_sf_cluster_config.private_config.storage_config.local_fs.wd

    test_data = pd.DataFrame(
        {"a": [9, 6, 5, 5], "b": [5, 5, 6, 7], "c": [1, 1, 2, 4], "d": [11, 55, 1, 99]}
    )
    test_data = test_data.astype(dtype="float32")

    if self_party == "alice":
        df_alice = test_data
        os.makedirs(os.path.join(local_fs_wd, "test_table_statistics"), exist_ok=True)
        df_alice.to_csv(os.path.join(local_fs_wd, alice_input_path), index=False)

    param = NodeEvalParam(
        domain="stats",
        name="table_statistics",
        version="0.0.1",
        attr_paths=[],
        attrs=[],
        inputs=[
            DistData(
                name="input_data",
                type=str(DistDataType.INDIVIDUAL_TABLE),
                data_refs=[
                    DistData.DataRef(uri=alice_input_path, party="alice", format="csv")
                ],
            )
        ],
        output_uris=[""],
    )
    meta = IndividualTable(
        schema=TableSchema(
            types=["f32", "f32", "f32", "f32"], features=["a", "b", "c", "d"]
        )
    )
    param.inputs[0].meta.Pack(meta)

    res = table_statistics_comp.eval(
        param=param, cluster_config=comp_prod_sf_cluster_config
    )

    comp_ret = Report()
    res.outputs[0].meta.Unpack(comp_ret)
    logging.info(comp_ret)
    assert comp_ret == gen_table_statistic_report(table_statistics(test_data))
