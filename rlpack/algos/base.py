import os
from abc import ABC, abstractmethod

import tensorflow as tf


class Base(ABC):
    """Algorithm base class."""

    def __init__(self, config):
        # Environment parameters.
        self.n_env = config.n_env
        self.dim_observation = config.dim_observation
        self.dim_action = config.dim_action
        self.n_action = config.n_action

        # Training parameters.
        self.discount = config.discount
        self.batch_size = config.batch_size
        self.training_epoch = config.training_epoch
        self.max_grad_norm = config.max_grad_norm

        # Save.
        self.save_path = config.save_path
        self.save_model_freq = config.save_model_freq

        # ------------------------ Reset graph ------------------------
        tf.reset_default_graph()
        tf.Variable(0, name="global_step", trainable=False)

        # ------------------------ Build network ------------------------
        self.build_network()

        # ------------------------ Build algorithm ------------------------
        self.build_algorithm()

        # ------------------------ Initialize model store and reload. ------------------------
        self._prepare()

    @abstractmethod
    def build_network(self):
        """Build tensorflow operations for algorithms."""
        pass

    @abstractmethod
    def build_algorithm(self):
        """Build algorithms using prebuilt networks."""
        pass

    def _prepare(self):
        # ------------------------ Initialize saver. ------------------------
        self.saver = tf.train.Saver(max_to_keep=50000)

        # ------------------------ Initialize Session. ------------------------
        conf = tf.ConfigProto(allow_soft_placement=True)
        conf.gpu_options.allow_growth = True  # pylint: disable=E1101
        self.sess = tf.Session(config=conf)

        # ------------------------ Initialize tensorflow variables.  ------------------------
        self.sess.run(tf.global_variables_initializer())

        # ------------------------ Reload model from the saved path. ------------------------
        self.load_model()

        # ------------------------ 初始化其他 ------------------------
        # self.total_reward = 0

    @abstractmethod
    def get_action(self, obs):
        """Return action according to the observations.
        :param obs: the observation that could be image or real-number features
        :return: actions
        """
        pass

    @abstractmethod
    def update(self, minibatch, update_ratio):
        """Update policy using minibatch samples.
        :param minibatch: a minibatch of training data
        :param update_ratio: the ratio of current update step in total update step
        :return: update info, i.e. loss.
        """
        pass

    def save_model(self):
        """Save model to `save_path`."""
        global_step = self.sess.run(tf.train.get_global_step())
        self.saver.save(
            self.sess,
            os.path.join(self.save_path, "model", "model"),
            global_step,
            write_meta_graph=True
        )

    def load_model(self):
        """Load model from `save_path` if there exists."""
        latest_checkpoint = tf.train.latest_checkpoint(os.path.join(self.save_path, "model"))
        if latest_checkpoint:
            print("## Loading model checkpoint {} ...".format(latest_checkpoint))
            self.saver.restore(self.sess, latest_checkpoint)
        else:
            print("## New start!")
