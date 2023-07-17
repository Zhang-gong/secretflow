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

import logging
from dataclasses import dataclass
from typing import List, Tuple, Union

import numpy as np

from secretflow.device import PYUObject, reveal

from ....core.distributed_tree.distributed_tree import DistributedTree
from ..bucket_sum_calculator import LeafWiseBucketSumCalculator
from ..component import Devices
from ..gradient_encryptor import GradientEncryptor
from ..leaf_manager import LeafManager
from ..loss_computer import LossComputer
from ..node_selector import NodeSelector
from ..order_map_manager import OrderMapManager
from ..sampler import Sampler
from ..shuffler import Shuffler
from ..split_candidate_manager import SplitCandidateManager
from ..split_finder import SplitFinder
from ..split_tree_builder import SplitTreeBuilder
from .tree_trainer import TreeTrainer


@dataclass
class LeafWiseTreeTrainerComponents:
    leaf_manager: LeafManager = LeafManager()
    node_selector: NodeSelector = NodeSelector()
    sampler: Sampler = Sampler()
    shuffler: Shuffler = Shuffler()
    gradient_encryptor: GradientEncryptor = GradientEncryptor()
    loss_computer: LossComputer = LossComputer()
    bucket_sum_calculator: LeafWiseBucketSumCalculator = LeafWiseBucketSumCalculator()
    split_finder: SplitFinder = SplitFinder()
    split_tree_builder: SplitTreeBuilder = SplitTreeBuilder()
    split_candidate_manager: SplitCandidateManager = SplitCandidateManager()


@dataclass
class LeafWiseTreeTrainerParams:
    """params specifically belonged to leaf wise booster, not its components.

    'max_leaf': int, maximum leaf of a tree.
            default: 15
            range: [1, 2**15]
    """

    max_leaf: int = 15


class LeafWiseTreeTrainer(TreeTrainer):
    def __init__(self) -> None:
        self.components = LeafWiseTreeTrainerComponents()
        self.params = LeafWiseTreeTrainerParams()

    def show_params(self):
        super().show_params()

    def set_params(self, params: dict):
        super().set_params(params)
        self._set_trainer_params(params)

    def get_params(self, params: dict):
        super().get_params(params)
        self._get_trainer_params(params)

    def set_devices(self, devices: Devices):
        super().set_devices(devices)
        self.workers = devices.workers
        self.label_holder = devices.label_holder
        self.party_num = len(self.workers)

    def _get_trainer_params(self, params: dict):
        params['max_leaf'] = self.params.max_leaf

    def _set_trainer_params(self, params: dict):
        leaf_num = int(params.pop('max_leaf', 15))
        assert (
            leaf_num > 0 and leaf_num <= 2**15
        ), f"max_depth should in [1, 2**15], got {leaf_num}"

        self.params.max_leaf = leaf_num

    def train_tree(
        self,
        cur_tree_num,
        order_map_manager: OrderMapManager,
        y: PYUObject,
        pred: Union[PYUObject, np.ndarray],
        x_shape: Tuple[int, int],
    ) -> DistributedTree:
        # sub sampling
        self.components.split_tree_builder.reset()
        feature_buckets = order_map_manager.get_feature_buckets()
        col_choices, total_buckets = self.components.sampler.generate_col_choices(
            feature_buckets
        )
        self.components.split_tree_builder.set_col_choices_and_buckets(
            col_choices, total_buckets, feature_buckets
        )
        row_choices = self.components.sampler.generate_row_choices(x_shape[0])
        y_sub = self.components.sampler.apply_vector_sampling(y, row_choices)
        pred_sub = self.components.sampler.apply_vector_sampling(pred, row_choices)
        order_map = order_map_manager.get_order_map()
        self.bucket_lists = order_map_manager.get_bucket_lists(col_choices)
        order_map_sub = self.components.sampler.apply_v_fed_sampling(
            order_map, row_choices, col_choices
        )
        self.row_choices = row_choices
        self.order_map_sub = order_map_sub
        self.bucket_num = order_map_manager.buckets

        # compute g, h and encryption
        g, h = self.components.loss_computer.compute_gh(y_sub, pred_sub)
        gh = self.components.gradient_encryptor.pack(g, h)
        encrypted_gh = self.components.gradient_encryptor.encrypt(gh, cur_tree_num)
        self.encrypted_gh_dict = self.components.gradient_encryptor.cache_to_workers(
            encrypted_gh, gh
        )

        # leaf wise train begins
        self.components.leaf_manager.clear_leaves()
        root_select = self.components.node_selector.root_select(order_map_sub.shape[0])

        new_split_node_selects = root_select
        new_split_node_indices = [0]

        for leaf in range(self.params.max_leaf):
            new_split_node_selects, new_split_node_indices = self._train_leaf(
                new_split_node_selects,
                new_split_node_indices,
                leaf,
                cur_tree_num,
                order_map_manager,
            )
            if reveal(
                self.components.node_selector.is_list_empty(new_split_node_indices)
            ):
                # pruned all nodes
                logging.info("all node pruned.")
                break

        # leaf nodes: all split candidates that are not pruned, but with max leaf reached, will turn into leaves
        # label_holder calc weights

        self.components.leaf_manager.extend_leaves(
            new_split_node_selects, new_split_node_indices
        )
        (
            leftover_ids,
            leftover_sample_selects,
        ) = self.components.split_candidate_manager.extract_all_nodes()
        self.components.leaf_manager.extend_leaves(
            leftover_sample_selects, leftover_ids
        )
        weight = self.components.leaf_manager.compute_leaf_weights(g, h)
        leaf_node_indices = self.components.leaf_manager.get_leaf_indices()
        tree = DistributedTree()
        self.components.split_tree_builder.insert_split_trees_into_distributed_tree(
            tree, leaf_node_indices
        )
        tree.set_leaf_weight(self.label_holder, weight)
        return tree

    def _preprare_new_split_candidates(
        self,
        new_split_node_selects: PYUObject,
        new_split_node_indices: List[int],
        tree_num: int,
        leaf: int,
    ):
        """Turn new split candidate into split candidate, by calculating its info.
        Info include sample_selects, bucket_sums and max gains.
        Pruned candiates will not appear in split candidate managers.

        new_split_node_indices: List[int]. has length 1 or 2. root or a pair of new split candidates from a splitted node.
        """

        # pick only one node to calculate bucket sum.
        (
            selected_node_selects,
            is_lefts,
            node_num,
        ) = self.components.node_selector.pick_children_node_ss(new_split_node_selects)
        # all parties knows the shape of tree, and which nodes in them, so this is fine.
        is_lefts = reveal(is_lefts)
        selected_children_node_indices = (
            self.components.node_selector.get_child_indices(
                new_split_node_indices, is_lefts
            )
        )

        # HEUObject cached with key node index
        selected_children_node_indices = reveal(selected_children_node_indices)
        # only compute the gradient sums of left or right children node. (choose fewer ones)
        (
            level_nodes_G,
            level_nodes_H,
        ) = self.components.bucket_sum_calculator.calculate_bucket_sum(
            self.components.shuffler,
            self.encrypted_gh_dict,
            selected_children_node_indices,
            new_split_node_indices,
            selected_node_selects,
            self.order_map_sub,
            self.bucket_num,
            self.bucket_lists,
            self.components.gradient_encryptor,
            node_num,
        )
        (
            split_buckets,
            split_gains,
            gain_is_cost_effective,
        ) = self.components.split_finder.find_best_splits_with_gains(
            level_nodes_G, level_nodes_H, tree_num, leaf
        )
        # all parties including driver know the shape of tree in each node
        # hence all parties including driver will know the pruning results.
        # hence we can reveal gain_is_cost_effective
        gain_is_cost_effective = reveal(gain_is_cost_effective)
        self.components.split_candidate_manager.batch_push(
            new_split_node_indices,
            new_split_node_selects,
            split_buckets,
            split_gains,
            gain_is_cost_effective,
        )
        return gain_is_cost_effective

    def _train_leaf(
        self,
        new_split_node_selects: PYUObject,
        new_split_node_indices: List[int],
        tree_num: int,
        leaf: int,
        order_map_manager: OrderMapManager,
    ) -> Tuple[PYUObject, PYUObject]:

        # new split candidates will be added to split candidates
        # or pruned away if gain is not cost effective
        gain_is_cost_effective = self._preprare_new_split_candidates(
            new_split_node_selects, new_split_node_indices, tree_num, leaf
        )
        # pruned node is given by gain_is_cost_effective and new_split_node_indices
        self.components.bucket_sum_calculator.remove_pruned_node_cache(
            new_split_node_indices, gain_is_cost_effective
        )
        (
            pruned_node_indices,
            pruned_s,
        ) = self.components.node_selector.get_pruned_indices_and_selects(
            new_split_node_indices, new_split_node_selects, gain_is_cost_effective
        )
        self.components.leaf_manager.extend_leaves(pruned_s, pruned_node_indices)

        # select the best candidate to do split
        (
            node_index,
            sample_selects,
            split_bucket,
        ) = self.components.split_candidate_manager.extract_best_split_info()

        # split not in party will be marked as -1
        split_buckets_viewed_each_party = (
            self.components.split_tree_builder.split_bucket_to_partition([split_bucket])
        )
        # -1 will retains
        unmasked_split_buckets_viewed_each_party = (
            self.components.shuffler.unshuffle_split_buckets_with_keys(
                split_buckets_viewed_each_party, [node_index]
            )
        )
        split_feature_buckets_each_party = (
            self.components.split_tree_builder.get_split_feature_list_wise_each_party(
                unmasked_split_buckets_viewed_each_party
            )
        )
        left_selects_each_party = (
            order_map_manager.batch_compute_left_child_selects_each_party(
                split_feature_buckets_each_party, self.row_choices
            )
        )
        split_points = order_map_manager.batch_query_split_points_each_party(
            split_feature_buckets_each_party
        )
        lchild_ss = self.components.split_tree_builder.do_split_list_wise_each_party(
            split_feature_buckets_each_party,
            split_points,
            left_selects_each_party,
            [True],
            [node_index],
        )
        (
            new_split_candidate_selects,
            new_split_candidate_indices,
            _,
            _,
        ) = self.components.node_selector.get_child_select(
            [sample_selects], lchild_ss, [True], [node_index]
        )
        # samples at each node indices and shape of tree are public
        return new_split_candidate_selects, reveal(new_split_candidate_indices)
