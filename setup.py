from setuptools import find_packages, setup

setup(name="rlpack",
      version="0.1.0",
      packages=find_packages(),
      zip_safe=False,
      install_requires=[
          "ray",
          "opencv-python",
          "msgpack_numpy",
          "msgpack",
          "zmq",
          "tensorboardX",
      ])
