"""
PCB进程控制块模块
==================
定义进程的各种属性和状态，是整个进程调度系统的核心数据结构。

PCB（Process Control Block）是操作系统中用于管理和控制进程的数据结构，
本模块模拟实现了一个完整的PCB，包含进程标识、状态、调度信息、资源信息等。
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional


class ProcessState(Enum):
    """进程状态枚举"""
    NEW = "新建"          # 进程刚创建，尚未就绪
    READY = "就绪"        # 进程已准备好，等待CPU
    RUNNING = "运行"      # 进程正在CPU上执行
    WAITING = "阻塞"      # 进程等待某事件（如I/O）
    SUSPENDED = "挂起"    # 进程被挂起，不能被调度
    TERMINATED = "终止"   # 进程执行完毕或被撤销


class ProcessType(Enum):
    """进程类型枚举（对应不同操作系统特性）"""
    BATCH = "批处理"      # 批处理系统进程
    TIME_SHARING = "分时"  # 分时系统进程
    REALTIME = "实时"      # 实时系统进程


@dataclass
class PCB:
    """
    进程控制块（PCB）
    =================
    模拟操作系统中的进程控制块，记录进程的全部管理信息。

    属性说明：
        pid             - 进程标识符（唯一）
        name            - 进程名称
        state           - 进程当前状态
        ptype           - 进程类型（批处理/分时/实时）
        priority        - 优先级（数值越小优先级越高）
        arrival_time    - 到达时间（提交时间）
        burst_time      - CPU服务时间（需要运行的总时间）
        remaining_time  - 剩余运行时间
        memory_size     - 进程所需内存大小（MB）
        deadline        - 截止时间（实时进程用）
        period          - 周期（实时进程用，秒）
        start_time      - 首次开始执行的时间
        finish_time     - 完成时间
        waiting_time    - 等待时间
        turnaround_time - 周转时间
        response_time   - 响应时间
        allocated_memory- 已分配的内存地址
    """
    pid: int = 0
    name: str = ""
    state: ProcessState = ProcessState.NEW
    ptype: ProcessType = ProcessType.BATCH
    priority: int = 0
    arrival_time: float = 0.0
    burst_time: float = 0.0
    remaining_time: float = 0.0
    memory_size: int = 0
    deadline: float = 0.0
    period: float = 0.0

    # 运行时统计（调度完成后填充）
    start_time: float = -1
    finish_time: float = -1
    waiting_time: float = 0
    turnaround_time: float = 0
    response_time: float = -1
    allocated_memory: Optional[int] = None

    def __post_init__(self):
        """初始化后，剩余时间默认等于服务时间"""
        if self.remaining_time == 0:
            self.remaining_time = self.burst_time

    def reset(self):
        """重置进程的运行时统计（用于多次调度测试）"""
        self.state = ProcessState.READY
        self.remaining_time = self.burst_time
        self.start_time = -1
        self.finish_time = -1
        self.waiting_time = 0
        self.turnaround_time = 0
        self.response_time = -1

    def __repr__(self):
        return (f"PCB(pid={self.pid}, name='{self.name}', "
                f"state={self.state.value}, type={self.ptype.value}, "
                f"burst={self.burst_time}, remaining={self.remaining_time:.1f})")

    def to_dict(self) -> dict:
        """转换为字典，便于显示和导出"""
        return {
            "PID": self.pid,
            "进程名": self.name,
            "状态": self.state.value,
            "类型": self.ptype.value,
            "优先级": self.priority,
            "到达时间": self.arrival_time,
            "服务时间": self.burst_time,
            "剩余时间": round(self.remaining_time, 2),
            "内存需求(MB)": self.memory_size,
            "开始时间": self.start_time if self.start_time >= 0 else "-",
            "完成时间": self.finish_time if self.finish_time >= 0 else "-",
            "等待时间": round(self.waiting_time, 2),
            "周转时间": round(self.turnaround_time, 2),
            "响应时间": self.response_time if self.response_time >= 0 else "-",
        }
