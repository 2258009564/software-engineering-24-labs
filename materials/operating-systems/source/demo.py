"""
命令行演示脚本
================
无需 PyQt5 即可运行的命令行演示，展示系统全部核心功能。
适合在没有GUI环境下验证程序功能。

运行方式：
    python demo.py
"""

import sys
import os
import copy
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pcb import PCB, ProcessState, ProcessType
from process_manager import ProcessManager
from scheduler import get_scheduler
from performance import PerformanceAnalyzer


def print_separator(title=""):
    """打印分隔线"""
    width = 65
    if title:
        padding = (width - len(title) - 2) // 2
        print("=" * padding + f" {title} " + "=" * (width - padding - len(title) - 2))
    else:
        print("=" * width)


def demo_process_control():
    """演示1：进程控制操作"""
    print_separator("演示1：进程控制操作")
    pm = ProcessManager(1024)

    # 创建进程
    print("\n【创建进程】")
    p1 = pm.create_process("进程A", ProcessType.BATCH, 0, 0, 8, 128)
    p2 = pm.create_process("进程B", ProcessType.BATCH, 1, 1, 4, 64)
    p3 = pm.create_process("进程C", ProcessType.TIME_SHARING, 2, 2, 6, 256)
    p4 = pm.create_process("进程D", ProcessType.REALTIME, 3, 0, 5, 64)
    p5 = pm.create_process("进程E", ProcessType.REALTIME, 4, 0, 3, 128)

    print(f"\n当前进程列表（共{len(pm.get_all_processes())}个）：")
    print(f"{'PID':>4} {'名称':<8} {'状态':<6} {'类型':<6} {'优先级':>4} {'服务时间':>6} {'内存(MB)':>8}")
    print("-" * 55)
    for p in pm.get_all_processes():
        print(f"{p.pid:>4} {p.name:<8} {p.state.value:<6} {p.ptype.value:<6} "
              f"{p.priority:>4} {p.burst_time:>6.1f} {p.memory_size:>8}")

    # 内存信息
    info = pm.get_memory_info()
    print(f"\n【内存使用】 总计:{info['总内存(MB)']}MB 已用:{info['已用内存(MB)']}MB "
          f"可用:{info['可用内存(MB)']}MB 利用率:{info['内存利用率(%)']}%")

    # 挂起与激活：选择已经处于就绪态的进程，确保能展示换出/调入后的内存变化
    print("\n【挂起进程 PID=1（进程A）】")
    pm.suspend_process(1)
    info = pm.get_memory_info()
    print(f"  挂起后可用内存: {info['可用内存(MB)']}MB")

    print("\n【激活进程 PID=1（进程A）】")
    pm.activate_process(1)
    info = pm.get_memory_info()
    print(f"  激活后可用内存: {info['可用内存(MB)']}MB")

    # 撤销进程
    print("\n【撤销进程 PID=5（进程E）】")
    pm.destroy_process(5)
    print(f"  剩余进程数: {len(pm.get_all_processes())}")

    return pm


def demo_scheduling(pm: ProcessManager):
    """演示2：调度算法"""
    print_separator("演示2：调度算法执行")
    processes = pm.get_all_processes()

    for algo in ["FCFS", "SJF", "RR", "EDF", "RMS"]:
        proc_copy = copy.deepcopy(processes)
        for p in proc_copy:
            p.reset()

        scheduler = get_scheduler(algo)
        result = scheduler.schedule(proc_copy, time_quantum=2.0)

        print(f"\n--- {result.algorithm_name} ---")
        print(f"  甘特图时间线：")
        for e in result.events:
            if e.is_idle:
                print(f"    [{e.start_time:.1f} - {e.end_time:.1f}] CPU空闲")
            else:
                print(f"    [{e.start_time:.1f} - {e.end_time:.1f}] {e.name}(PID={e.pid})")

        print(f"\n  统计指标：")
        print(f"    总调度时间: {result.total_time:.1f}s")
        print(f"    平均周转时间: {result.avg_turnaround_time:.2f}s")
        print(f"    平均等待时间: {result.avg_waiting_time:.2f}s")
        print(f"    平均响应时间: {result.avg_response_time:.2f}s")
        print(f"    CPU利用率: {result.cpu_utilization:.1f}%")


def demo_performance(pm: ProcessManager):
    """演示3：性能对比分析"""
    print_separator("演示3：五种算法性能对比分析")
    processes = pm.get_all_processes()

    analyzer = PerformanceAnalyzer()
    analyzer.run_all(processes)
    print()
    print(analyzer.get_comparison_report())


def main():
    """主函数"""
    print()
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║        进程调度机制设计系统 — 命令行演示                    ║")
    print("║        操作系统课程设计 | 软件24-4班 | 第1组               ║")
    print("║        组长：梁震宇（2404060404）                          ║")
    print("╚═══════════════════════════════════════════════════════════╝")
    print()

    # 演示1：进程控制
    pm = demo_process_control()

    # 演示2：调度算法
    demo_scheduling(pm)

    # 演示3：性能对比
    demo_performance(pm)

    print()
    print_separator("演示完成")
    print("提示：运行 python main.py 可启动图形界面版本（需安装PyQt5）")
    print()


if __name__ == "__main__":
    main()
