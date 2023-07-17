import logging

from secretflow.component.test_framework.test_case import PipelineCase, TestComp
from secretflow.component.test_framework.test_controller import TestController
from secretflow.utils.logging import LOG_FORMAT

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT, force=True)

    aci_pipe = PipelineCase("aci_pipe")

    attrs = {
        "protocol": "ECDH_PSI_2PC",
        "receiver": "alice",
        "precheck_input": True,
        "sort": True,
        "broadcast_result": True,
        "bucket_size": 1048576,
        "curve_type": "CURVE_FOURQ",
        "input/receiver_input/key": ["id0"],
        "input/sender_input/key": ["id1"],
    }
    # 测试psi
    psi = TestComp("psi_test", "psi", "two_party_balanced_psi", "0.0.1", attrs)
    aci_pipe.add_comp(psi, ["DAGInput.alice", "DAGInput.bob"])

    attrs = {
        "input/in_ds/drop_features": ["alice1", "bob9"],
    }
    # 测试feature_filter
    feature_filter = TestComp("ff", "preprocessing", "feature_filter", "0.0.1", attrs)
    aci_pipe.add_comp(feature_filter, ["psi_test.0"])

    attrs = {
        "train_size": 0.7,
        "test_size": 0.3,
        "random_state": 42,
        "shuffle": False,
    }
    # 测试train_test_split
    ds_split = TestComp("ds_split", "preprocessing", "train_test_split", "0.0.1", attrs)
    aci_pipe.add_comp(ds_split, ["ff.0"])

    attrs = {
        "epochs": 2,
        "learning_rate": 0.1,
        "batch_size": 512,
        "sig_type": "t1",
        "reg_type": "logistic",
    }
    # 测试ss_sgd_train
    sslr = TestComp("sslr_train", "ml.linear", "ss_sgd_train", "0.0.1", attrs)
    aci_pipe.add_comp(sslr, ["ds_split.0"])

    attrs = {
        "batch_size": 32,
        "receiver": "alice",
        "save_ids": True,
        "save_label": True,
    }
    # 测试ss_sgd_predict
    sslr = TestComp("sslr_pred", "ml.linear", "ss_sgd_predict", "0.0.1", attrs)
    aci_pipe.add_comp(sslr, ["sslr_train.0", "ds_split.1"])

    # TODO: add others comp

    test = TestController(aci_mode=True)
    test.add_pipeline_case(aci_pipe)

    test.run(True)
