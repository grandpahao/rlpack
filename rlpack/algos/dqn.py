# -*- coding: utf-8 -*-
from collections import deque

import numpy as np
import tensorflow as tf
from tqdm import tqdm

from ..common.utils import assert_shape
from ..common.network import mlp, cnn1d, cnn2d
from .base import Base


class DQN(Base):
    def __init__(self,
                 rnd=1,
                 n_env=1,
                 dim_obs=None,
                 dim_act=None,
                 discount=0.99,
                 save_path="./log",
                 save_model_freq=1000,
                 update_target_freq=10000,
                 log_freq=1000,
                 epsilon_schedule=lambda x: min(1.0, x / 1e6),
                 lr=2.5e-4):
        """Deep Q Network.

        Keyword Arguments:
            rnd {int} -- [description] (default: {1})
            n_env {int} -- [description] (default: {1})
            dim_obs {[type]} -- [description] (default: {None})
            dim_act {[type]} -- [description] (default: {None})
            discount {float} -- [description] (default: {0.99})
            save_path {str} -- [description] (default: {"./log"})
            save_model_freq {int} -- [description] (default: {1000})
            update_target_freq {int} -- [description] (default: {10000})
            log_freq {int} -- [description] (default: {1000})
            epsilon_schedule {func} -- epsilon schedule. (default: {lambdax:(1-x)*1})
            lr {[type]} -- [description] (default: {2.5e-4})
        """
        self.n_env = n_env
        self.dim_obs = dim_obs
        self.dim_act = dim_act
        self.discount = discount
        self.save_model_freq = save_model_freq
        self.update_target_freq = update_target_freq
        self.log_freq = log_freq
        self.epsilon_schedule = epsilon_schedule
        self.epsilon = self.epsilon_schedule(0)
        self.lr = lr

        super().__init__(save_path=save_path, rnd=rnd)

        self.all_loss = deque(maxlen=20)
        self.all_max_q = deque(maxlen=20)

    def safemean(self, x):
        return np.nan if len(x) == 0 else np.mean(x)

    def build_network(self):
        """Build networks for algorithm."""
        self.observation = tf.placeholder(shape=[None, *self.dim_obs], dtype=tf.uint8, name="observation")
        self.observation = tf.to_float(self.observation) / 255.0

        # self.observation = tf.placeholder(shape=[None, *self.dim_obs], dtype=tf.float32, name="observation")

        self.action = tf.placeholder(dtype=tf.int32, shape=[None], name="action")
        self.reward = tf.placeholder(dtype=tf.float32, shape=[None], name="reward")
        self.done = tf.placeholder(dtype=tf.float32, shape=[None], name="done")

        self.next_observation = tf.placeholder(dtype=tf.uint8, shape=[None, *self.dim_obs], name="next_observation")
        self.next_observation = tf.to_float(self.next_observation) / 255.0
        # self.next_observation = tf.placeholder(dtype=tf.float32, shape=[None, *self.dim_obs], name="next_observation")

        with tf.variable_scope("main/qnet"):
            # Atari
            # x = tf.layers.conv2d(self.observation, 32, 8, 4, activation=tf.nn.relu)
            # x = tf.layers.conv2d(x, 64, 4, 2, activation=tf.nn.relu)
            # x = tf.layers.conv2d(x, 64, 3, 1, activation=tf.nn.relu)
            # x = tf.contrib.layers.flatten(x)  # pylint: disable=E1101
            # x = tf.layers.dense(x, 512, activation=tf.nn.relu)
            # self.qvals = tf.layers.dense(x, self.dim_act)
            # self.qvals = cnn2d(self.observation, cnn2d_hidden_sizes=[(32, 8, 4), (64, 4, 2), (64, 3, 1)], mlp_hidden_sizes=[512, self.dim_act])

            # Atari-ram
            # x = tf.layers.conv1d(self.observation, 32, 8, 4, activation=tf.nn.relu)
            # x = tf.layers.conv1d(x, 64, 4, 2, activation=tf.nn.relu)
            # x = tf.contrib.layers.flatten(x)
            # x = tf.layers.dense(x, 64, activation=tf.nn.relu)
            # self.qvals = tf.layers.dense(x, self.dim_act)
            self.qvals = cnn1d(self.observation, cnn1d_hidden_sizes=[(32, 8, 4), (64, 4, 2)], mlp_hidden_sizes=[64, self.dim_act])

            # Classic control
            # x = tf.layers.dense(self.observation, 64, activation=tf.nn.relu)
            # x = tf.layers.dense(x, 64, activation=tf.nn.relu)
            # x = tf.layers.dense(x, 32, activation=tf.nn.relu)
            # self.qvals = tf.layers.dense(x, self.dim_act)
            # self.qvals = mlp(self.observation, hidden_sizes=[64, 64, 32, self.dim_act])

        with tf.variable_scope("target/qnet"):
            # Atari
            # x = tf.layers.conv2d(self.next_observation, 32, 8, 4, activation=tf.nn.relu, trainable=False)
            # x = tf.layers.conv2d(x, 64, 4, 2, activation=tf.nn.relu, trainable=False)
            # x = tf.layers.conv2d(x, 64, 3, 1, activation=tf.nn.relu, trainable=False)
            # x = tf.contrib.layers.flatten(x)  # pylint: disable=E1101
            # x = tf.layers.dense(x, 512, activation=tf.nn.relu, trainable=False)
            # self.target_qvals = tf.layers.dense(x, self.dim_act, trainable=False)

            # Atari-ram
            # x = tf.layers.conv1d(self.next_observation, 32, 8, 4, activation=tf.nn.relu, trainable=False)
            # x = tf.layers.conv1d(x, 64, 4, 2, activation=tf.nn.relu, trainable=False)
            # x = tf.contrib.layers.flatten(x)
            # x = tf.layers.dense(x, 64, activation=tf.nn.relu, trainable=False)
            # self.target_qvals = tf.layers.dense(x, self.dim_act, trainable=False)
            self.target_qvals = cnn1d(self.observation, cnn1d_hidden_sizes=[(32, 8, 4), (64, 4, 2)], mlp_hidden_sizes=[64, self.dim_act])

            # Classic control
            # x = tf.layers.dense(self.next_observation, 64, activation=tf.nn.relu, trainable=False)
            # x = tf.layers.dense(x, 64, activation=tf.nn.relu, trainable=False)
            # x = tf.layers.dense(x, 32, activation=tf.nn.relu, trainable=False)
            # self.target_qvals = tf.layers.dense(x, self.dim_act, trainable=False)

            # x = tf.layers.dense(self.next_observation, 64, activation=tf.nn.relu)
            # x = tf.layers.dense(x, 64, activation=tf.nn.relu)
            # self.target_qvals = tf.layers.dense(x, self.dim_act)

    def build_algorithm(self):
        """Build networks for algorithm."""
        self.optimizer = tf.train.AdamOptimizer(self.lr, epsilon=1.5e-8)
        trainable_variables = tf.trainable_variables("main/qnet")

        print("trainable variables:", trainable_variables)
        input()

        # Compute the state value.
        batch_size = tf.shape(self.observation)[0]
        action_index = tf.stack([tf.range(batch_size), self.action], axis=1)
        action_q = tf.gather_nd(self.qvals, action_index)
        assert_shape(action_q, [None])

        # Compute back up.
        assert_shape(tf.reduce_max(self.target_qvals, axis=1), [None])
        q_backup = tf.stop_gradient(self.reward + self.discount * (1 - self.done) * tf.reduce_max(self.target_qvals, axis=1))

        # Compute loss and optimize the object.
        self.loss = tf.reduce_mean(tf.squared_difference(q_backup, action_q))   # 损失值。
        self.train_op = self.optimizer.minimize(self.loss, var_list=trainable_variables)

        # Update target network.
        def _update_target(old_net, new_net):
            params1 = tf.trainable_variables(old_net)
            params1 = sorted(params1, key=lambda v: v.name)
            params2 = tf.global_variables(new_net)
            params2 = sorted(params2, key=lambda v: v.name)
            assert len(params1) == len(params2)
            update_ops = []
            for param1, param2 in zip(params1, params2):
                update_ops.append(param2.assign(param1))
            return update_ops

        self.update_target_op = _update_target("main/qnet", "target/qnet")

        self.max_qval = tf.reduce_max(self.qvals)

    def get_action(self, obs):
        """Get actions according to the given observation.

        Parameters:
            - ob: An ndarray with shape (n, state_dimension).

        Returns:
            - An ndarray for action with shape (n).
        """
        # if obs.ndim == 1 or obs.ndim == 3:
        #     newobs = np.array(obs)[np.newaxis, :]
        # else:
        #     assert obs.ndim == 2 or obs.ndim == 4
        #     newobs = obs

        # print("obs:", obs.shape)

        q = self.sess.run(self.qvals, feed_dict={self.observation: obs})
        max_a = np.argmax(q, axis=1)

        # Epsilon greedy method.
        batch_size = obs.shape[0]
        actions = np.random.randint(self.dim_act, size=batch_size)
        idx = np.random.uniform(size=batch_size) < self.epsilon
        actions[idx] = max_a[idx]

        return actions

    def update(self, minibatch, update_step: int):
        """Update the algorithm by suing a batch of data.

        Parameters:
            - minibatch:  a list of ndarray containing a minibatch of state, action, reward, done, next_state.

                - state shape: (n_env, batch_size, state_dimension)
                - action shape: (n_env, batch_size)
                - reward shape: (n_env, batch_size)
                - done shape: (n_env, batch_size)
                - next_state shape: (n_env, batch_size, state_dimension)

            - update_step: a int scalar.

        Returns:
            - training infomation.
        """

        self.epsilon = self.epsilon_schedule(update_step)

        s_batch, a_batch, r_batch, d_batch, next_s_batch = minibatch

        n_env, batch_size = s_batch.shape[:2]
        s_batch = s_batch.reshape(n_env * batch_size, *self.dim_obs)
        a_batch = a_batch.reshape(n_env * batch_size)
        r_batch = r_batch.reshape(n_env * batch_size)
        d_batch = d_batch.reshape(n_env * batch_size)
        next_s_batch = next_s_batch.reshape(n_env * batch_size, *self.dim_obs)

        # print("state", "shape:", s_batch.shape, "dtype:", s_batch.dtype, "max:", np.max(s_batch), "min:", np.min(s_batch))
        # input()

        _, loss, max_q_val = self.sess.run(
            [self.train_op,
             self.loss,
             self.max_qval],
            feed_dict={
                self.observation: s_batch,
                self.action: a_batch,
                self.reward: r_batch,
                self.done: d_batch,
                self.next_observation: next_s_batch
            }
        )

        global_step, _ = self.sess.run([tf.train.get_global_step(), self.increment_global_step])
        # Store model.
        if global_step % self.save_model_freq == 0:
            self.save_model()

        # Update target policy.
        if global_step % self.update_target_freq == 0:
            self.sess.run(self.update_target_op)

        self.all_loss.append(loss)
        self.all_max_q.append(max_q_val)

        if global_step % self.log_freq == 0:
            tqdm.write(f"meanloss: {self.safemean(self.all_loss)}  meanmaxq: {self.safemean(self.all_max_q)} epsilon: {self.epsilon}")

        return {"loss": loss, "max_q_value": max_q_val, "global_step": global_step}
