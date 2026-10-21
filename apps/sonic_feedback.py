"""Validate SONIC's actual ZMQ feedback, independent of ROS clocks and HTTP polling."""
from __future__ import annotations
from collections import deque
import time
from console_support import finite, now


class SonicFeedback:
    def __init__(self, max_age=.5, minimum_samples=3):
        self.max_age, self.minimum_samples = max_age, minimum_samples
        self.samples = deque(maxlen=200)
        self.last_index = None
        self.last_monotonic = None
        self.observed_at = None
        self.values = None
        self.message = None
        self.accepted = self.duplicates = self.rejected = 0
        self.consecutive = 0
        self.error = ''
        self.config_at = None
        self.config_monotonic = None

    def configuration(self, message):
        if not isinstance(message, dict) or not finite(message.get('control_frequency')) or not 1 <= message['control_frequency'] <= 1000:
            raise ValueError('robot_config 缺少有效 control_frequency')
        self.config_at, self.config_monotonic = now(), time.monotonic()

    def feed(self, message):
        try:
            if not isinstance(message, dict) or message.get('control_loop_type') != 'cpp':
                raise ValueError('反馈不是 SONIC C++ 的 g1_debug 数据')
            index = message.get('index')
            if type(index) is not int or index < 0:
                raise ValueError('g1_debug 缺少非负整数 index；ros_timestamp 不能代替控制序号')
            values = message.get('body_q_measured', message.get('body_q'))
            if not isinstance(values, (tuple, list)) or len(values) != 29 or not all(finite(v) for v in values):
                raise ValueError('g1_debug 的 29 维测量关节无效')
            for key in ('body_dq', 'last_action'):
                if key in message and (not isinstance(message[key], (tuple, list)) or len(message[key]) != 29 or not all(finite(v) for v in message[key])):
                    raise ValueError(key + ' 维度或数值无效')
            # ROS time is 0 when the input is ZMQ. Use monotonic receive time and index.
            stamp = message.get('ros_timestamp', 0)
            if not finite(stamp) or stamp < 0:
                raise ValueError('ros_timestamp 无效')
            if stamp > 1_000_000_000 and not -.5 <= time.time() - stamp <= 2:
                raise ValueError('源 ROS 时间戳已过期或时钟未同步')
            if self.last_index is not None:
                if index == self.last_index:
                    self.duplicates += 1
                    return False
                if index < self.last_index:
                    raise ValueError('同一订阅会话的 index 回退；需要重新连接确认新控制器')
            mono = time.monotonic()
            if self.last_monotonic is None or mono - self.last_monotonic > self.max_age:
                self.consecutive = 0
                self.samples.clear()
            self.consecutive += 1
            self.last_monotonic, self.observed_at = mono, now()
            self.last_index, self.values, self.message = index, list(values), message
            self.samples.append((mono, index))
            self.accepted += 1
            self.error = ''
            return True
        except (ValueError, TypeError, KeyError) as exc:
            self.rejected += 1
            self.consecutive = 0
            self.error = str(exc)
            return False

    def status(self):
        mono = time.monotonic()
        age = mono - self.last_monotonic if self.last_monotonic is not None else None
        valid = age is not None and age <= self.max_age and self.consecutive >= self.minimum_samples and not self.error
        samples = [row for row in self.samples if mono - row[0] <= 2]
        rate = (len(samples) - 1) / (samples[-1][0] - samples[0][0]) if len(samples) > 1 and samples[-1][0] > samples[0][0] else None
        config_age = mono - self.config_monotonic if self.config_monotonic is not None else None
        return {'valid': valid, 'observed_at': self.observed_at, 'control_index': self.last_index,
                'feedback_age_seconds': age, 'frequency_hz': round(rate, 1) if rate is not None else None,
                'accepted': self.accepted, 'duplicates': self.duplicates, 'rejected': self.rejected,
                'consecutive_samples': self.consecutive, 'error': self.error,
                'configuration_observed_at': self.config_at, 'configuration_age_seconds': config_age,
                'clock_basis': 'monotonic_receive_time_and_cpp_index', 'measurement_field': 'body_q_measured (body_q fallback)'}
