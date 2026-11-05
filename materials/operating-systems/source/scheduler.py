"""
调度算法模块
================
实现五种经典进程调度算法，覆盖批处理、分时、实时三种操作系统类型。

算法列表：
    1. FCFS（先来先服务）  - 批处理系统，非抢占式
    2. SJF （短作业优先）  - 批处理系统，非抢占式
    3. RR  （时间片轮转）  - 分时系统，抢占式
    4. EDF （最早截止时间优先）- 实时系统，抢占式，动态优先级
    5. RMS （速率单调调度）  - 实时系统，抢占式，静态优先级

每种算法返回调度时间线（Gantt Chart数据），记录哪个进程在哪个时间段运行。
"""

from pcb import PCB, ProcessState
from typing import List, Tuple
from dataclasses import dataclass, field


@dataclass
class ScheduleEvent:
    """
    调度事件（甘特图的一个段）
    ========================
    表示在某个时间段内，哪个进程在CPU上运行。
    """
    pid: int                    # 进程ID
    name: str                   # 进程名
    start_time: float           # 开始时间
    end_time: float             # 结束时间
    is_idle: bool = False       # 是否为CPU空闲


@dataclass
class ScheduleResult:
    """
    调度结果
    ========
    包含完整的调度时间线和每个进程的统计数据。
    """
    algorithm_name: str                          # 算法名称
    events: List[ScheduleEvent] = field(default_factory=list)  # 调度时间线
    total_time: float = 0                        # 总调度时间
    cpu_utilization: float = 0                   # CPU利用率
    avg_turnaround_time: float = 0               # 平均周转时间
    avg_waiting_time: float = 0                  # 平均等待时间
    avg_response_time: float = 0                 # 平均响应时间
    process_stats: dict = field(default_factory=dict)  # 各进程统计

    def get_gantt_data(self) -> List[Tuple[str, float, float, int]]:
        """获取甘特图数据：(进程名, 开始时间, 结束时间, PID)"""
        return [(e.name, e.start_time, e.end_time, e.pid) for e in self.events]


class Scheduler:
    """
    调度器基类
    ==========
    提供调度算法的通用接口和结果统计方法。
    """

    def __init__(self, name: str):
        self.name = name

    def schedule(self, processes: List[PCB], time_quantum: float = 1.0) -> ScheduleResult:
        """
        执行调度（子类实现）

        参数:
            processes: 待调度的进程列表
            time_quantum: 时间片大小（仅RR算法使用）

        返回:
            调度结果
        """
        raise NotImplementedError("子类必须实现schedule方法")

    def _calculate_stats(self, result: ScheduleResult, processes: List[PCB]):
        """计算性能统计指标"""
        total_turnaround = 0
        total_waiting = 0
        total_response = 0
        count = 0
        busy_time = 0

        for pcb in processes:
            if pcb.finish_time < 0:
                continue
            count += 1
            # 周转时间 = 完成时间 - 到达时间
            turnaround = pcb.finish_time - pcb.arrival_time
            # 等待时间 = 周转时间 - 服务时间
            waiting = turnaround - pcb.burst_time
            # 响应时间 = 首次执行时间 - 到达时间
            response = pcb.start_time - pcb.arrival_time if pcb.start_time >= 0 else 0

            pcb.turnaround_time = turnaround
            pcb.waiting_time = waiting
            pcb.response_time = response

            total_turnaround += turnaround
            total_waiting += waiting
            total_response += response
            busy_time += pcb.burst_time

            result.process_stats[pcb.pid] = {
                "进程名": pcb.name,
                "到达时间": pcb.arrival_time,
                "服务时间": pcb.burst_time,
                "开始时间": pcb.start_time,
                "完成时间": pcb.finish_time,
                "周转时间": round(turnaround, 2),
                "等待时间": round(waiting, 2),
                "响应时间": round(response, 2),
            }

        if count > 0:
            result.avg_turnaround_time = round(total_turnaround / count, 2)
            result.avg_waiting_time = round(total_waiting / count, 2)
            result.avg_response_time = round(total_response / count, 2)

        # CPU利用率
        if result.total_time > 0:
            result.cpu_utilization = round((busy_time / result.total_time) * 100, 2)


# ============================================================
# 1. FCFS 先来先服务（批处理系统）
# ============================================================
class FCFSScheduler(Scheduler):
    """
    先来先服务调度算法（First-Come First-Served）
    ==============================================
    最简单的调度算法，按照进程到达的先后顺序进行调度。
    非抢占式：一旦进程获得CPU，将一直运行到完成。

    特点：
        - 实现简单，公平（按到达顺序）
        - 平均等待时间可能较长（护航效应）
        - 适用于批处理系统
    """

    def __init__(self):
        super().__init__("FCFS（先来先服务）")

    def schedule(self, processes: List[PCB], time_quantum: float = 1.0) -> ScheduleResult:
        result = ScheduleResult(algorithm_name=self.name)
        # 按到达时间排序
        sorted_procs = sorted(processes, key=lambda p: p.arrival_time)

        current_time = 0.0
        for pcb in sorted_procs:
            # 如果CPU空闲，等待进程到达
            if current_time < pcb.arrival_time:
                # 添加空闲事件
                result.events.append(ScheduleEvent(
                    pid=-1, name="空闲",
                    start_time=current_time,
                    end_time=pcb.arrival_time,
                    is_idle=True
                ))
                current_time = pcb.arrival_time

            # 进程开始执行
            pcb.start_time = current_time
            pcb.state = ProcessState.RUNNING

            # 运行到完成（非抢占式）
            current_time += pcb.burst_time
            pcb.finish_time = current_time
            pcb.remaining_time = 0
            pcb.state = ProcessState.TERMINATED

            result.events.append(ScheduleEvent(
                pid=pcb.pid, name=pcb.name,
                start_time=pcb.start_time,
                end_time=pcb.finish_time
            ))

        result.total_time = current_time
        self._calculate_stats(result, sorted_procs)
        return result


# ============================================================
# 2. SJF 短作业优先（批处理系统）
# ============================================================
class SJFScheduler(Scheduler):
    """
    短作业优先调度算法（Shortest Job First）
    ========================================
    在就绪队列中选择服务时间最短的进程优先执行。
    非抢占式：一旦进程开始执行，将运行到完成。

    特点：
        - 平均等待时间最优（非抢占式情况下）
        - 可能导致长作业"饥饿"
        - 适用于批处理系统
    """

    def __init__(self):
        super().__init__("SJF（短作业优先）")

    def schedule(self, processes: List[PCB], time_quantum: float = 1.0) -> ScheduleResult:
        result = ScheduleResult(algorithm_name=self.name)
        remaining = list(processes)  # 待调度进程副本
        current_time = 0.0

        while remaining:
            # 找出当前时间已到达的进程
            arrived = [p for p in remaining if p.arrival_time <= current_time]

            if not arrived:
                # 没有进程到达，CPU空闲，快进到下一个到达的进程
                next_proc = min(remaining, key=lambda p: p.arrival_time)
                result.events.append(ScheduleEvent(
                    pid=-1, name="空闲",
                    start_time=current_time,
                    end_time=next_proc.arrival_time,
                    is_idle=True
                ))
                current_time = next_proc.arrival_time
                continue

            # 选择服务时间最短的进程
            selected = min(arrived, key=lambda p: p.burst_time)
            remaining.remove(selected)

            # 执行
            selected.start_time = current_time
            selected.state = ProcessState.RUNNING
            current_time += selected.burst_time
            selected.finish_time = current_time
            selected.remaining_time = 0
            selected.state = ProcessState.TERMINATED

            result.events.append(ScheduleEvent(
                pid=selected.pid, name=selected.name,
                start_time=selected.start_time,
                end_time=selected.finish_time
            ))

        result.total_time = current_time
        self._calculate_stats(result, processes)
        return result


# ============================================================
# 3. RR 时间片轮转（分时系统）
# ============================================================
class RRScheduler(Scheduler):
    """
    时间片轮转调度算法（Round Robin）
    =================================
    每个进程分配一个固定大小的时间片，时间片用完后被强制剥夺CPU，
    放到就绪队列末尾等待下一轮调度。
    抢占式算法，适合分时系统。

    特点：
        - 公平：每个进程获得相同的CPU时间
        - 响应时间短，适合交互式系统
        - 时间片大小影响性能：太大退化为FCFS，太小切换开销大
    """

    def __init__(self):
        super().__init__("RR（时间片轮转）")

    def schedule(self, processes: List[PCB], time_quantum: float = 2.0) -> ScheduleResult:
        result = ScheduleResult(algorithm_name=self.name)
        # 按到达时间排序，初始化剩余时间
        sorted_procs = sorted(processes, key=lambda p: p.arrival_time)
        for p in sorted_procs:
            p.remaining_time = p.burst_time
            p.start_time = -1

        current_time = 0.0
        ready_queue: List[PCB] = []
        idx = 0  # 下一个到达的进程索引

        while idx < len(sorted_procs) or ready_queue:
            # 将到达的进程加入就绪队列
            while idx < len(sorted_procs) and sorted_procs[idx].arrival_time <= current_time:
                ready_queue.append(sorted_procs[idx])
                idx += 1

            if not ready_queue:
                # 就绪队列为空，快进到下一个进程到达
                if idx < len(sorted_procs):
                    next_arrival = sorted_procs[idx].arrival_time
                    result.events.append(ScheduleEvent(
                        pid=-1, name="空闲",
                        start_time=current_time,
                        end_time=next_arrival,
                        is_idle=True
                    ))
                    current_time = next_arrival
                    continue
                else:
                    break

            # 取出队首进程
            pcb = ready_queue.pop(0)

            # 记录首次响应
            if pcb.start_time < 0:
                pcb.start_time = current_time

            # 运行一个时间片
            run_time = min(time_quantum, pcb.remaining_time)
            pcb.state = ProcessState.RUNNING
            pcb.remaining_time -= run_time
            current_time += run_time

            result.events.append(ScheduleEvent(
                pid=pcb.pid, name=pcb.name,
                start_time=current_time - run_time,
                end_time=current_time
            ))

            # 在运行期间到达的进程先入队（确保顺序正确）
            while idx < len(sorted_procs) and sorted_procs[idx].arrival_time <= current_time:
                ready_queue.append(sorted_procs[idx])
                idx += 1

            if pcb.remaining_time > 0:
                # 未完成，放回就绪队列末尾
                pcb.state = ProcessState.READY
                ready_queue.append(pcb)
            else:
                # 完成
                pcb.finish_time = current_time
                pcb.state = ProcessState.TERMINATED

        result.total_time = current_time
        self._calculate_stats(result, sorted_procs)
        return result


# ============================================================
# 4. EDF 最早截止时间优先（实时系统）
# ============================================================
class EDFScheduler(Scheduler):
    """
    最早截止时间优先调度算法（Earliest Deadline First）
    ===================================================
    动态优先级调度算法：截止时间（deadline）越早的进程优先级越高。
    抢占式：当新到达进程的截止时间更早时，可以抢占当前运行的进程。

    特点：
        - 理论上是最优的单处理器实时调度算法
        - 可调度利用率上限：100%
        - 动态优先级，每个时刻重新计算
    """

    def __init__(self):
        super().__init__("EDF（最早截止时间优先）")

    def schedule(self, processes: List[PCB], time_quantum: float = 1.0) -> ScheduleResult:
        result = ScheduleResult(algorithm_name=self.name)
        sorted_procs = sorted(processes, key=lambda p: p.arrival_time)
        for p in sorted_procs:
            p.remaining_time = p.burst_time
            p.start_time = -1
            # 如果未设置deadline，默认为到达时间+服务时间+10
            if p.deadline <= 0:
                p.deadline = p.arrival_time + p.burst_time + 10

        current_time = 0.0
        active: List[PCB] = []  # 已到达但未完成的进程
        idx = 0
        time_step = 0.5  # 模拟时间步长

        while idx < len(sorted_procs) or active:
            # 添加到达的进程
            while idx < len(sorted_procs) and sorted_procs[idx].arrival_time <= current_time:
                active.append(sorted_procs[idx])
                idx += 1

            if not active:
                if idx < len(sorted_procs):
                    next_arrival = sorted_procs[idx].arrival_time
                    result.events.append(ScheduleEvent(
                        pid=-1, name="空闲",
                        start_time=current_time,
                        end_time=next_arrival,
                        is_idle=True
                    ))
                    current_time = next_arrival
                    continue
                break

            # 选择截止时间最早的进程
            selected = min(active, key=lambda p: p.deadline)

            if selected.start_time < 0:
                selected.start_time = current_time

            # 运行一个时间步（抢占式检查粒度）
            run_time = min(time_step, selected.remaining_time)
            selected.remaining_time -= run_time
            old_time = current_time
            current_time += run_time

            # 合并连续相同进程的事件
            if result.events and result.events[-1].pid == selected.pid and not result.events[-1].is_idle:
                result.events[-1].end_time = current_time
            else:
                result.events.append(ScheduleEvent(
                    pid=selected.pid, name=selected.name,
                    start_time=old_time, end_time=current_time
                ))

            if selected.remaining_time <= 0.001:
                selected.finish_time = current_time
                selected.state = ProcessState.TERMINATED
                active.remove(selected)

        result.total_time = current_time
        self._calculate_stats(result, sorted_procs)
        return result


# ============================================================
# 5. RMS 速率单调调度（实时系统）
# ============================================================
class RMSScheduler(Scheduler):
    """
    速率单调调度算法（Rate Monotonic Scheduling）
    =============================================
    静态优先级调度算法：进程的优先级由其周期决定，周期越短（速率越快），
    优先级越高。优先级在系统运行期间保持不变。
    抢占式：高优先级进程可以抢占低优先级进程。

    特点：
        - 静态优先级，运行期间不变化
        - 可调度利用率上限：n(2^(1/n)-1) ≈ 69.3%（n→∞）
        - 适用于周期性实时任务
    """

    def __init__(self):
        super().__init__("RMS（速率单调调度）")

    def schedule(self, processes: List[PCB], time_quantum: float = 1.0) -> ScheduleResult:
        result = ScheduleResult(algorithm_name=self.name)
        sorted_procs = sorted(processes, key=lambda p: p.arrival_time)
        for p in sorted_procs:
            p.remaining_time = p.burst_time
            p.start_time = -1
            # 如果未设置period，根据burst_time估算
            if p.period <= 0:
                p.period = p.burst_time * 3

        current_time = 0.0
        active: List[PCB] = []
        idx = 0
        time_step = 0.5

        while idx < len(sorted_procs) or active:
            while idx < len(sorted_procs) and sorted_procs[idx].arrival_time <= current_time:
                active.append(sorted_procs[idx])
                idx += 1

            if not active:
                if idx < len(sorted_procs):
                    next_arrival = sorted_procs[idx].arrival_time
                    result.events.append(ScheduleEvent(
                        pid=-1, name="空闲",
                        start_time=current_time,
                        end_time=next_arrival,
                        is_idle=True
                    ))
                    current_time = next_arrival
                    continue
                break

            # 选择周期最短（速率最快）的进程 = 最高优先级
            selected = min(active, key=lambda p: p.period)

            if selected.start_time < 0:
                selected.start_time = current_time

            run_time = min(time_step, selected.remaining_time)
            selected.remaining_time -= run_time
            old_time = current_time
            current_time += run_time

            if result.events and result.events[-1].pid == selected.pid and not result.events[-1].is_idle:
                result.events[-1].end_time = current_time
            else:
                result.events.append(ScheduleEvent(
                    pid=selected.pid, name=selected.name,
                    start_time=old_time, end_time=current_time
                ))

            if selected.remaining_time <= 0.001:
                selected.finish_time = current_time
                selected.state = ProcessState.TERMINATED
                active.remove(selected)

        result.total_time = current_time
        self._calculate_stats(result, sorted_procs)
        return result


# ============================================================
# 调度器工厂
# ============================================================
def get_scheduler(algorithm: str) -> Scheduler:
    """
    根据算法名称获取调度器实例

    参数:
        algorithm: 算法名称（fcfs/sjf/rr/edf/rms）

    返回:
        对应的调度器实例
    """
    schedulers = {
        "FCFS": FCFSScheduler,
        "SJF": SJFScheduler,
        "RR": RRScheduler,
        "EDF": EDFScheduler,
        "RMS": RMSScheduler,
    }
    algo_upper = algorithm.upper().strip()
    if algo_upper not in schedulers:
        raise ValueError(f"未知调度算法: {algorithm}，可选: {list(schedulers.keys())}")
    return schedulers[algo_upper]()

