import numpy as np
import tensorflow as tf

import secretflow as sf
from secretflow.ml.nn.sl.agglayer.agg_layer import AggLayer
from secretflow.ml.nn.sl.agglayer.agg_method import Average
from secretflow.utils.communicate import ForwardData


class TestPlainAggLayer:
    def test_plain_average(self, sf_simulation_setup_devices):
        # SETUP DEVICE
        alice, bob, carol = (
            sf_simulation_setup_devices.alice,
            sf_simulation_setup_devices.bob,
            sf_simulation_setup_devices.carol,
        )
        # GIVEN
        average_agglayer = AggLayer(
            device_agg=carol,
            parties=[alice, bob],
            device_y=bob,
            agg_method=Average(),
        )
        a = alice(
            lambda: ForwardData(
                hidden=tf.constant(
                    ([[1.0, 2.0], [3.0, 4.0]], [[10.0, 20.0], [30.0, 40.0]])
                )
            )
        )()
        b = bob(
            lambda: ForwardData(
                hidden=tf.constant(
                    ([[1.0, 2.0], [3.0, 4.0]], [[10.0, 20.0], [30.0, 40.0]])
                )
            )
        )()

        c = bob(
            lambda: tf.constant(
                ([[1.0, 2.0], [3.0, 4.0]], [[10.0, 20.0], [30.0, 40.0]])
            )
        )()

        # WHEN
        forward_obj = sf.reveal(average_agglayer.forward({alice: a, bob: b}, axis=0))
        backward_obj = sf.reveal(average_agglayer.backward(c))
        np.testing.assert_almost_equal(
            forward_obj.hidden.numpy(),
            tf.constant(
                ([[1.0, 2.0], [3.0, 4.0]], [[10.0, 20.0], [30.0, 40.0]])
            ).numpy(),
            decimal=5,
        )
        import logging

        logging.warning(sf.reveal(backward_obj))
        np.testing.assert_almost_equal(
            backward_obj[alice].numpy(),
            tf.constant(
                ([[0.5, 1.0], [1.5, 2.0]], [[5.0, 10.0], [15.0, 20.0]])
            ).numpy(),
            decimal=5,
        )

        np.testing.assert_almost_equal(
            backward_obj[bob].numpy(),
            tf.constant(
                ([[0.5, 1.0], [1.5, 2.0]], [[5.0, 10.0], [15.0, 20.0]])
            ).numpy(),
            decimal=5,
        )

    def test_plain_default(self, sf_simulation_setup_devices):
        # SETUP DEVICE
        alice, bob = (
            sf_simulation_setup_devices.alice,
            sf_simulation_setup_devices.bob,
        )
        # GIVEN
        default_agglayer = AggLayer(
            device_agg=bob,
            parties=[alice, bob],
            device_y=bob,
            agg_method=None,
        )
        default_agglayer.set_basenet_output_num({alice: 2, bob: 2})
        a = alice(
            lambda: ForwardData(
                hidden=tf.constant(
                    ([[1.0, 2.0], [3.0, 4.0]], [[10.0, 20.0], [30.0, 40.0]])
                )
            )
        )()
        b = bob(
            lambda: ForwardData(
                hidden=tf.constant(
                    ([[1.0, 2.0], [3.0, 4.0]], [[10.0, 20.0], [30.0, 40.0]])
                )
            )
        )()
        c = bob(
            lambda: tf.constant(
                (
                    [[1.0, 2.0], [3.0, 4.0]],
                    [[10.0, 20.0], [30.0, 40.0]],
                    [[1.0, 2.0], [3.0, 4.0]],
                    [[10.0, 20.0], [30.0, 40.0]],
                )
            )
        )()

        # WHEN
        forward_obj = sf.reveal(default_agglayer.forward({alice: a, bob: b}))
        backward_obj = sf.reveal(default_agglayer.backward(c))

        np.testing.assert_almost_equal(
            forward_obj[0].hidden.numpy(),
            tf.constant(
                ([[1.0, 2.0], [3.0, 4.0]], [[10.0, 20.0], [30.0, 40.0]])
            ).numpy(),
            decimal=5,
        )
        np.testing.assert_almost_equal(
            forward_obj[1].hidden.numpy(),
            tf.constant(
                ([[1.0, 2.0], [3.0, 4.0]], [[10.0, 20.0], [30.0, 40.0]])
            ).numpy(),
            decimal=5,
        )

        np.testing.assert_almost_equal(
            backward_obj[alice].numpy(),
            tf.constant(
                ([[1.0, 2.0], [3.0, 4.0]], [[10.0, 20.0], [30.0, 40.0]])
            ).numpy(),
            decimal=5,
        )
        np.testing.assert_almost_equal(
            backward_obj[bob].numpy(),
            tf.constant(
                ([[1.0, 2.0], [3.0, 4.0]], [[10.0, 20.0], [30.0, 40.0]])
            ).numpy(),
            decimal=5,
        )


class TestSPUAggLayer:
    def test_spu_average(self, sf_simulation_setup_devices):
        # SETUP DEVICE
        alice, bob = (
            sf_simulation_setup_devices.alice,
            sf_simulation_setup_devices.bob,
        )
        spu = sf_simulation_setup_devices.spu
        # GIVEN
        spu_agglayer = AggLayer(
            device_agg=spu,
            parties=[alice, bob],
            device_y=bob,
            agg_method=Average(),
        )
        a = alice(lambda: ForwardData(hidden=tf.constant([[1.0, 2.0], [3.0, 4.0]])))()
        b = bob(lambda: ForwardData(hidden=tf.constant([[1.0, 2.0], [3.0, 4.0]])))()
        c = bob(lambda: tf.constant([[1.0, 2.0], [3.0, 4.0]]))()
        # WHEN
        forward_obj = sf.reveal(spu_agglayer.forward({alice: a, bob: b}, axis=0))
        backward_obj = sf.reveal(spu_agglayer.backward(c))
        # THEN
        np.testing.assert_almost_equal(
            forward_obj.hidden.numpy(),
            tf.constant([[1.0, 2.0], [3.0, 4.0]]).numpy(),
            decimal=5,
        )
        np.testing.assert_almost_equal(
            backward_obj[alice].numpy(),
            tf.constant([[0.5, 1.0], [1.5, 2.0]]).numpy(),
            decimal=5,
        )
        np.testing.assert_almost_equal(
            backward_obj[bob].numpy(),
            tf.constant([[0.5, 1.0], [1.5, 2.0]]).numpy(),
            decimal=5,
        )
