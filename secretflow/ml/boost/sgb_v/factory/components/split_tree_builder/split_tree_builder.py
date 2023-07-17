# Copyright 2023 Ant Group Co., Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import List, Union

from secretflow.device import PYUObject

from ....core.distributed_tree.distributed_tree import DistributedTree
from ..component import Component, Devices
from ..order_map_manager import OrderMapManager
from ..shuffler import Shuffler
from .split_tree_actor import SplitTreeBuilderActor


class SplitTreeBuilder(Component):
    def __init__(self) -> None:
        return

    def show_params(self):
        return

    def set_params(self, _):
        return

    def get_params(self, _):
        return

    def set_devices(self, devices: Devices):
        self.split_tree_builder_actors = [
            SplitTreeBuilderActor(i, device=w) for i, w in enumerate(devices.workers)
        ]
        self.workers = devices.workers
        self.label_holder = devices.label_holder

    def reset(self):
        for actor in self.split_tree_builder_actors:
            actor.reset()

    def set_col_choices_and_buckets(
        self,
        col_choices: List[PYUObject],
        total_buckets: List[PYUObject],
        feature_buckets: List[PYUObject],
    ):
        for actor, col_choice, feature_bucket in zip(
            self.split_tree_builder_actors, col_choices, feature_buckets
        ):
            actor.set_col_choices(col_choice)
            actor.set_feature_bucket(feature_bucket)
            # total number buckets is broadcasted
            actor.set_buckets_count(
                [buckets_count.to(actor.device) for buckets_count in total_buckets]
            )

    def split_bucket_to_partition(
        self, split_buckets: Union[PYUObject, List[PYUObject]]
    ) -> List[PYUObject]:
        """map split bucket to position in the partition or -1 if not in partition

        Args:
            split_buckets (Union[PYUObject, List[PYUObject]]): Either is a PYUObject or List[PYUObject],
                but in both cases it's in fact List[int].

        Returns:
            List[PYUObject]: each PYUObject is in fact a List[int]. split buckets viewed by each party
        """
        return [
            actor.split_buckets_to_paritition(
                split_buckets.to(actor.device)
                if isinstance(split_buckets, PYUObject)
                else [sb.to(actor.device) for sb in split_buckets]
            )
            for actor in self.split_tree_builder_actors
        ]

    def get_split_feature_list_wise_each_party(
        self, un_shuffled_split_buckets_each_party: List[PYUObject]
    ) -> List[PYUObject]:
        """map the unmasked split buckets to feature and split point

        Args:
            split_buckets_each_party (List[PYUObject]): split buckets viewed by each party. PYUOBject is a list of int. -1 if not here.

        Returns:
            List[PYUObject]: PYUObject is in fact a List[Union[None, Tuple[int, int]]], None if -1 else (feature_index, bucket_index) for split.
        """
        return [
            actor.get_split_feature_list_wise(split_buckets)
            for actor, split_buckets in zip(
                self.split_tree_builder_actors, un_shuffled_split_buckets_each_party
            )
        ]

    # TODO(zoupeicheng.zpc): Optimization. make gain is cost effective earlier.
    def do_split_list_wise_each_party(
        self,
        split_features: List[PYUObject],
        split_points: List[PYUObject],
        left_child_selects: List[PYUObject],
        gain_is_cost_effective: List[bool],
        node_indices: Union[List[int], PYUObject],
    ) -> List[List[int]]:
        """insert split points to split trees

        Args:
            split_features (List[PYUObject]): party wise. each PYUObject is List[Tuple[int, int]]. len = node indices length.
            split_points (List[PYUObject]): : party wise. each PYUObject is List[float]. len = node indices length.
            left_child_selects (List[PYUObject]):  party wise. each PYUObject is List[np.ndarray]
            gain_is_cost_effective (List[bool]): if gain is cost effective
            node_indices (Union[List[int], PYUObject]): node indices.

        Returns:
            left_child_selects: left child selects for the new split nodes.
        """
        lchild_selects = []
        for i, _ in enumerate(self.workers):
            split_node_indices_here = (
                node_indices.to(self.workers[i])
                if isinstance(node_indices, PYUObject)
                else [
                    node.to(self.workers[i]) if isinstance(node, PYUObject) else node
                    for node in node_indices
                ]
            )
            # split buckets is sent from label holder to workers
            selects = self.split_tree_builder_actors[i].do_split_list_wise(
                split_features[i],
                split_points[i],
                left_child_selects[i],
                gain_is_cost_effective,
                split_node_indices_here,
            )
            lchild_selects.append(selects.to(self.label_holder))
        return lchild_selects

    def do_split(
        self,
        split_buckets: List[int],
        sampled_rows: List[int],
        gain_is_cost_effective: List[bool],
        node_indices: Union[List[int], PYUObject],
        shuffler: Shuffler,
        order_map_manager: OrderMapManager,
    ) -> List[PYUObject]:
        lchild_selects = []
        for i, w in enumerate(self.workers):
            split_node_indices_here = (
                node_indices.to(self.workers[i])
                if isinstance(node_indices, PYUObject)
                else node_indices
            )
            # split buckets is sent from label holder to workers
            selects = self.split_tree_builder_actors[i].do_split(
                split_buckets.to(w),
                sampled_rows,
                gain_is_cost_effective,
                split_node_indices_here,
                shuffler.worker_shufflers[w],
                order_map_manager.order_map_actors[i],
            )
            lchild_selects.append(selects.to(self.label_holder))
        return lchild_selects

    def insert_split_trees_into_distributed_tree(
        self, distributed_tree: DistributedTree, leaf_node_indices: PYUObject
    ):
        for i, builder in enumerate(self.split_tree_builder_actors):
            tree = builder.tree_finish(leaf_node_indices.to(self.workers[i]))
            distributed_tree.insert_split_tree(self.workers[i], tree)
