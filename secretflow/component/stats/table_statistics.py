# Copyright 2023 Ant Group Co., Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from secretflow.component.component import Component, IoType
from secretflow.component.data_utils import (
    DistDataType,
    dump_table_statistics,
    load_table,
)
from secretflow.stats.table_statistics import table_statistics

table_statistics_comp = Component(
    name="table_statistics",
    domain="stats",
    version="0.0.1",
    desc="""Get a table of statistics,
    including each column's datatype, total_count, count, count_na, min, max,
    var, std, sem, skewness, kurtosis, q1, q2, q3, moment_2, moment_3, moment_4,
    central_moment_2, central_moment_3, central_moment_4, sum, sum_2, sum_3 and sum_4.

    moment_2 means E[X^2].
    central_moment_2 means E[(X - mean(X))^2].
    sum_2 means sum(X^2).
    """,
)


table_statistics_comp.io(
    io_type=IoType.INPUT,
    name="input_data",
    desc="Input data.",
    types=[DistDataType.VERTICAL_TABLE, DistDataType.INDIVIDUAL_TABLE],
    col_params=None,
)
table_statistics_comp.io(
    io_type=IoType.OUTPUT,
    name="report",
    desc="Output report.",
    types=[DistDataType.REPORT],
    col_params=None,
)


@table_statistics_comp.eval_fn
def table_statistics_eval_fn(*, ctx, input_data, report):
    input_df = load_table(
        ctx, input_data, load_features=True, load_labels=True, load_ids=True
    )

    with ctx.tracer.trace_running():
        stat = table_statistics(input_df)

    return {"report": dump_table_statistics(report, input_data.sys_info, stat)}