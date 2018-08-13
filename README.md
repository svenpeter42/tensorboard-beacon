# Tensorboard-beacon
Small server that can run multiple tensorboard instances at once and add/remove individual log directories from each without restarting.

Useful if you're running multiple distinct experiements and don't want them all to appear in the same web interface.

# Example usage:

```
% python beacon.py --port 6006
2018-08-13 11:06:43.440048: I tensorflow/core/platform/cpu_feature_guard.cc:140] Your CPU supports instructions that this TensorFlow binary was not compiled to use: AVX2 FMA
Serving on http://HOSTNAME:6006/TOKEN
(tensorboard-beacon) start test0
Started test0
(tensorboard-beacon) start test1
Started test1
(tensorboard-beacon) add test0 /path/to/tensorboard/logs/exp0
Added /path/to/tensorboard/logs/exp0 to test0.
(tensorboard-beacon) add test0 /path/to/tensorboard/logs/exp1
Added /path/to/tensorboard/logs/exp1 to test0.
(tensorboard-beacon) add test0 /path/to/tensorboard/logs/exp2
Added /path/to/tensorboard/logs/exp2 to test0.
(tensorboard-beacon) add test1 /path/to/different/tensorboard/logs/exp0
Added /path/to/different/tensorboard/logs/exp0 to test1.
(tensorboard-beacon) add test1 /path/to/different/tensorboard/logs/exp1
Added /path/to/different/tensorboard/logs/exp1 to test1.
(tensorboard-beacon) add test1 /path/to/different/tensorboard/logs/exp2
Added /path/to/different/tensorboard/logs/exp2 to test1.
```
