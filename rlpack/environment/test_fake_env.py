from rlpack.environment.fake_env import AsyncFakeContinuousEnv, AsyncFakeDiscreteEnv, AsyncFlappyBirdEnv

# env = AsyncFakeDiscreteEnv(4, 4)
# env = AsyncFakeContinuousEnv(4, 4)
env = AsyncFlappyBirdEnv(4, 4)
s = env.reset()
print(s.shape)

for i in range(100):
    a = env.sample_action(4)
    s, r, d, info = env.step(a)

    print(f"s: {s.shape} a: {a.shape} r: {r.shape} d: {len(d)} info: {info}")
