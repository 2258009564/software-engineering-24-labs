"""
性能分析模块
================
负责采集和比较不同调度算法的性能指标，生成对比图表数据。

核心指标：
    - 周转时间（Turnaround Time）：进程从提交到完成的总时间
    - 等待时间（Waiting Time）：进程在就绪队列中等待的总时间
    - 响应时间（Response Time）：从提交到首次获得CPU的时间
    - CPU利用率（CPU Utilization）：CPU保持忙碌的时间比例

通过对比不同算法在相同进程集上的性能，帮助理解各算法的优缺点和适用场景。
"""

from scheduler import (
    Scheduler, ScheduleResult,
    FCFSScheduler, SJFScheduler, RRScheduler, EDFScheduler, RMSScheduler,
    get_scheduler
)
from pcb import PCB
from typing import List, Dict
import copy
import json


class PerformanceAnalyzer:
    """
    性能分析器
    ==========
    对同一组进程运行多种调度算法，采集性能指标，生成对比分析。

    用法:
        analyzer = PerformanceAnalyzer()
        analyzer.run_all(processes)
        report = analyzer.get_comparison_report()
    """

    # 支持的算法列表
    ALGORITHMS = ["FCFS", "SJF", "RR", "EDF", "RMS"]

    def __init__(self):
        self.results: Dict[str, ScheduleResult] = {}

    def run_single(self, algorithm: str, processes: List[PCB],
                   time_quantum: float = 2.0) -> ScheduleResult:
        """
        运行单个调度算法

        参数:
            algorithm: 算法名称
            processes: 进程列表
            time_quantum: 时间片大小（RR算法使用）

        返回:
            调度结果
        """
        # 深拷贝进程列表，避免修改原始数据
        proc_copy = copy.deepcopy(processes)
        for p in proc_copy:
            p.reset()

        scheduler = get_scheduler(algorithm)
        result = scheduler.schedule(proc_copy, time_quantum)
        self.results[algorithm] = result
        return result

    def run_all(self, processes: List[PCB], time_quantum: float = 2.0) -> Dict[str, ScheduleResult]:
        """运行所有算法并采集结果"""
        for algo in self.ALGORITHMS:
            self.run_single(algo, processes, time_quantum)
        return self.results

    def get_comparison_data(self) -> dict:
        """
        获取算法对比数据（用于表格展示和图表绘制）

        返回格式:
        {
            "algorithms": ["FCFS", "SJF", "RR", "EDF", "RMS"],
            "avg_turnaround": [12.5, 10.0, ...],
            "avg_waiting": [5.0, 3.0, ...],
            "avg_response": [3.0, 2.0, ...],
            "cpu_utilization": [85.0, 90.0, ...],
        }
        """
        data = {
            "algorithms": [],
            "avg_turnaround": [],
            "avg_waiting": [],
            "avg_response": [],
            "cpu_utilization": [],
        }
        for algo in self.ALGORITHMS:
            if algo in self.results:
                r = self.results[algo]
                data["algorithms"].append(algo)
                data["avg_turnaround"].append(r.avg_turnaround_time)
                data["avg_waiting"].append(r.avg_waiting_time)
                data["avg_response"].append(r.avg_response_time)
                data["cpu_utilization"].append(r.cpu_utilization)
        return data

    def get_comparison_report(self) -> str:
        """
        生成文本对比报告

        返回:
            格式化的对比报告字符串
        """
        lines = []
        lines.append("=" * 70)
        lines.append("           调度算法性能对比报告")
        lines.append("=" * 70)
        lines.append("")

        header = f"{'算法':<25} {'平均周转':>8} {'平均等待':>8} {'平均响应':>8} {'CPU利用率':>10}"
        lines.append(header)
        lines.append("-" * 70)

        best_turnaround = ("", float('inf'))
        best_waiting = ("", float('inf'))
        best_response = ("", float('inf'))

        for algo in self.ALGORITHMS:
            if algo not in self.results:
                continue
            r = self.results[algo]
            display_name = r.algorithm_name
            line = (f"{display_name:<25} {r.avg_turnaround_time:>8.2f} "
                    f"{r.avg_waiting_time:>8.2f} {r.avg_response_time:>8.2f} "
                    f"{r.cpu_utilization:>9.1f}%")
            lines.append(line)

            if r.avg_turnaround_time < best_turnaround[1]:
                best_turnaround = (display_name, r.avg_turnaround_time)
            if r.avg_waiting_time < best_waiting[1]:
                best_waiting = (display_name, r.avg_waiting_time)
            if r.avg_response_time < best_response[1]:
                best_response = (display_name, r.avg_response_time)

        lines.append("-" * 70)
        lines.append("")
        lines.append("分析结论：")
        lines.append(f"  · 平均周转时间最优：{best_turnaround[0]}（{best_turnaround[1]:.2f}）")
        lines.append(f"  · 平均等待时间最优：{best_waiting[0]}（{best_waiting[1]:.2f}）")
        lines.append(f"  · 平均响应时间最优：{best_response[0]}（{best_response[1]:.2f}）")
        lines.append("")

        lines.append("算法特性说明：")
        lines.append("  · FCFS：实现简单，但存在护航效应，平均等待时间可能较长")
        lines.append("  · SJF：平均等待时间最优（非抢占式），但可能导致长作业饥饿")
        lines.append("  · RR：响应时间短且公平，适合交互式分时系统")
        lines.append("  · EDF：动态优先级，理论上是最优的实时调度算法")
        lines.append("  · RMS：静态优先级，适用于周期性实时任务")
        lines.append("=" * 70)

        return "\n".join(lines)

    def export_to_csv(self, filepath: str):
        """将对比数据导出为CSV文件"""
        data = self.get_comparison_data()
        with open(filepath, 'w', encoding='utf-8-sig') as f:
            f.write("算法,平均周转时间,平均等待时间,平均响应时间,CPU利用率(%)\n")
            for i, algo in enumerate(data["algorithms"]):
                f.write(f"{algo},")
                f.write(f"{data['avg_turnaround'][i]},")
                f.write(f"{data['avg_waiting'][i]},")
                f.write(f"{data['avg_response'][i]},")
                f.write(f"{data['cpu_utilization'][i]}\n")
        print(f"数据已导出至：{filepath}")

    def export_to_json(self, filepath: str):
        """将完整结果导出为JSON文件"""
        export_data = {}
        for algo, result in self.results.items():
            export_data[algo] = {
                "algorithm_name": result.algorithm_name,
                "total_time": result.total_time,
                "avg_turnaround_time": result.avg_turnaround_time,
                "avg_waiting_time": result.avg_waiting_time,
                "avg_response_time": result.avg_response_time,
                "cpu_utilization": result.cpu_utilization,
                "gantt_data": result.get_gantt_data(),
                "process_stats": result.process_stats,
            }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        print(f"数据已导出至：{filepath}")
