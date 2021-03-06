import signal
import sys
import time
from multiprocessing.managers import BaseManager
from queue import Empty, Queue
from threading import Thread
from typing import Dict, List

import numpy as np


def exit_gracefully(signum, frame):
    sys.exit(0)


signal.signal(signal.SIGINT, exit_gracefully)


class DistributedEnvManager(Thread):
    """
    start on main gaming process.
    """

    def __init__(self, n_env, port=50000):
        super().__init__()
        self.n_env = n_env
        self.config_queue = Queue()
        self.srd_pad = {}
        self.a_pad = {}

        for env_id in range(n_env):
            self.srd_pad[env_id] = Queue()
            self.a_pad[env_id] = Queue()

        class SharedMemoryManager(BaseManager):
            pass

        SharedMemoryManager.register('get_config', callable=lambda: self.config_queue)
        SharedMemoryManager.register('get_srd', callable=lambda x: self.srd_pad[x])
        SharedMemoryManager.register('get_a', callable=lambda x: self.a_pad[x])

        m = SharedMemoryManager(address=('', port), authkey=b'abab')
        self.s = m.get_server()

    def run(self):
        self.s.serve_forever()

    def get_envs_to_inference(self, n: int, state_only: bool = False):
        """Get one step forward states, reward, dones, infos.

        Parameters:
            - n: an integer. the number of environmentsself.
            - state_only: True at the first step for reset.

        Returns:
            - 5 lists. environment_ids, next_observations, rewards, dones, infos.
        """
        srdis = []
        env_ids = []
        m = 0
        p = 0
        while m < n:
            if p == 0:
                time.sleep(0.0001)
            try:
                srdi = self.srd_pad[p].get(block=False)

                env_ids.append(p)
                m += 1
                srdis.append(srdi)
                p = (p + 1) % self.n_env
            except Empty:
                p = (p + 1) % self.n_env

        next_obs = [srdis[i][0] for i in range(n)]

        if state_only:
            return env_ids, next_obs
        rewards = [srdis[i][1] for i in range(n)]
        dones = [srdis[i][2] for i in range(n)]
        infos = [srdis[i][3] for i in range(n)]
        return env_ids, next_obs, rewards, dones, infos

    def step(self, actions: Dict):
        for env_id, a in actions.items():
            self.a_pad[env_id].put(a)

    def configure(self, configure_list: List[Dict] = []) -> None:
        if configure_list:
            assert self.n_env == len(configure_list)
            for c in configure_list:
                self.config_queue.put(c)
        else:
            for i in range(self.n_env):
                self.config_queue.put({'env_id': i})


if __name__ == '__main__':
    from tqdm import tqdm
    import random
    n_env = 8
    distributed_env_manager = DistributedEnvManager(n_env)
    distributed_env_manager.configure()
    distributed_env_manager.start()

    env_ids, obs = distributed_env_manager.get_envs_to_inference(n_env, state_only=True)
    print('get', env_ids)
    actions = dict((env_id, random.randrange(4)) for env_id in env_ids)
    distributed_env_manager.step(actions)

    for _ in tqdm(range(10000)):
        env_ids, obs, rewards, dones, infos = distributed_env_manager.get_envs_to_inference(n_env)
        actions = dict((env_id, random.randrange(4)) for env_id in env_ids)
        distributed_env_manager.step(actions)
