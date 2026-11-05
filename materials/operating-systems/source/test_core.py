"""
核心功能回归测试
================
验证进程控制、资源管理和调度算法的关键路径。

运行方式：
    python -m unittest test_core.py
"""

import copy
import unittest

from pcb import ProcessState, ProcessType
from process_manager import ProcessManager
from scheduler import get_scheduler


def build_sample_processes():
    pm = ProcessManager(1024)
    pm.create_process("P1", ProcessType.BATCH, 3, 0, 8, 128, deadline=18, period=10)
    pm.create_process("P2", ProcessType.BATCH, 1, 1, 4, 64, deadline=9, period=8)
    pm.create_process("P3", ProcessType.TIME_SHARING, 2, 2, 6, 256, deadline=20, period=12)
    pm.create_process("P4", ProcessType.REALTIME, 4, 0, 5, 64, deadline=7, period=5)
    return pm


class ProcessAndResourceTests(unittest.TestCase):
    def test_memory_blocks_record_real_pid(self):
        pm = build_sample_processes()
        allocated_pids = [
            block["PID"]
            for block in pm.resource_manager.get_block_list()
            if block["状态"] == "已分配"
        ]
        self.assertEqual(allocated_pids, [1, 2, 3, 4])

    def test_suspend_and_activate_release_and_reallocate_memory(self):
        pm = build_sample_processes()
        self.assertTrue(pm.suspend_process(1))
        self.assertEqual(pm.get_process(1).state, ProcessState.SUSPENDED)
        self.assertEqual(pm.get_memory_info()["可用内存(MB)"], 640)

        self.assertTrue(pm.activate_process(1))
        self.assertEqual(pm.get_process(1).state, ProcessState.READY)
        self.assertEqual(pm.get_memory_info()["可用内存(MB)"], 512)


class SchedulerTests(unittest.TestCase):
    def test_all_schedulers_complete_sample_processes(self):
        processes = build_sample_processes().get_all_processes()
        for algorithm in ["FCFS", "SJF", "RR", "EDF", "RMS"]:
            with self.subTest(algorithm=algorithm):
                proc_copy = copy.deepcopy(processes)
                for p in proc_copy:
                    p.reset()

                result = get_scheduler(algorithm).schedule(proc_copy, time_quantum=2)

                self.assertGreater(len(result.events), 0)
                self.assertEqual(result.total_time, 23)
                self.assertEqual(result.cpu_utilization, 100)
                self.assertTrue(all(p.finish_time >= 0 for p in proc_copy))
                self.assertTrue(all(p.remaining_time == 0 for p in proc_copy))


if __name__ == "__main__":
    unittest.main()
