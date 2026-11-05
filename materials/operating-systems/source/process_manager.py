"""
进程管理器模块
================
负责进程的创建、撤销、挂起、激活等进程控制操作，
是操作系统进程管理的核心模拟组件。

主要功能：
    1. 创建进程（分配PID、初始化PCB、分配内存）
    2. 撤销进程（回收PCB、释放内存）
    3. 挂起进程（暂停执行，移出内存）
    4. 激活进程（恢复执行，调入内存）
    5. 查询进程信息
"""

from pcb import PCB, ProcessState, ProcessType
from resource_manager import ResourceManager
from typing import List, Optional, Dict


class ProcessManager:
    """
    进程管理器
    ==========
    模拟操作系统的进程管理功能，维护系统中的所有PCB，
    协调与资源管理器的交互。

    状态转换图：
        NEW → READY → RUNNING → TERMINATED
                    ↓    ↑
                  WAITING |
                    ↓    |
                  SUSPENDED
    """

    def __init__(self, total_memory: int = 1024):
        """
        初始化进程管理器

        参数:
            total_memory: 系统总内存大小（MB），默认1024MB
        """
        self.processes: Dict[int, PCB] = {}   # PID → PCB 映射
        self._next_pid: int = 1                # 下一个可用的PID
        self.resource_manager = ResourceManager(total_memory)
        self.creation_log: List[str] = []      # 操作日志

    def create_process(self, name: str, ptype: ProcessType, priority: int,
                       arrival_time: float, burst_time: float,
                       memory_size: int,
                       deadline: float = 0, period: float = 0) -> Optional[PCB]:
        """
        创建新进程

        流程：
            1. 分配唯一的PID
            2. 尝试分配内存资源
            3. 初始化PCB
            4. 将进程加入就绪队列
            5. 记录操作日志

        参数:
            name: 进程名称
            ptype: 进程类型（批处理/分时/实时）
            priority: 优先级（0最高）
            arrival_time: 到达时间
            burst_time: CPU服务时间
            memory_size: 内存需求（MB）
            deadline: 截止时间（实时进程）
            period: 周期（实时进程）

        返回:
            创建成功的PCB对象，内存不足时返回None
        """
        # 尝试分配内存
        pid = self._next_pid
        addr = self.resource_manager.allocate(memory_size, pid=pid)
        if addr is None:
            log_msg = f"[创建失败] 进程 '{name}' 内存不足（需求{memory_size}MB，"
            log_msg += f"可用{self.resource_manager.available_memory}MB）"
            self.creation_log.append(log_msg)
            return None

        # 创建PCB
        self._next_pid += 1
        pcb = PCB(
            pid=pid, name=name, ptype=ptype, priority=priority,
            arrival_time=arrival_time, burst_time=burst_time,
            remaining_time=burst_time, memory_size=memory_size,
            deadline=deadline, period=period,
            allocated_memory=addr,
        )

        # 设置初始状态为就绪
        if arrival_time <= 0:
            pcb.state = ProcessState.READY
        else:
            pcb.state = ProcessState.NEW

        self.processes[pid] = pcb
        log_msg = (f"[创建成功] PID={pid} 名称='{name}' 类型={ptype.value} "
                   f"优先级={priority} 服务时间={burst_time} 内存={memory_size}MB "
                   f"地址=0x{addr:04X}")
        self.creation_log.append(log_msg)
        return pcb

    def destroy_process(self, pid: int) -> bool:
        """
        撤销（终止）进程

        流程：
            1. 查找PCB
            2. 释放内存资源
            3. 设置状态为终止
            4. 从进程表中移除

        参数:
            pid: 要撤销的进程ID

        返回:
            成功返回True，进程不存在返回False
        """
        pcb = self.processes.get(pid)
        if pcb is None:
            self.creation_log.append(f"[撤销失败] PID={pid} 不存在")
            return False

        # 释放内存
        self.resource_manager.deallocate(pcb.allocated_memory, pcb.memory_size)

        # 设置终止状态并移除
        pcb.state = ProcessState.TERMINATED
        del self.processes[pid]
        self.creation_log.append(f"[撤销成功] PID={pid} 名称='{pcb.name}' 内存已释放")
        return True

    def suspend_process(self, pid: int) -> bool:
        """
        挂起进程

        将进程从活动状态转为挂起状态，暂时移出内存（释放其占用的内存资源）。
        被挂起的进程不能被调度执行，直到被激活。

        参数:
            pid: 要挂起的进程ID

        返回:
            成功返回True，失败返回False
        """
        pcb = self.processes.get(pid)
        if pcb is None:
            return False

        if pcb.state in (ProcessState.RUNNING, ProcessState.READY, ProcessState.WAITING):
            # 挂起时释放内存（模拟换出到外存）
            self.resource_manager.deallocate(pcb.allocated_memory, pcb.memory_size)
            pcb.allocated_memory = None
            pcb.state = ProcessState.SUSPENDED
            self.creation_log.append(f"[挂起成功] PID={pid} 名称='{pcb.name}' 已换出到外存")
            return True
        else:
            self.creation_log.append(
                f"[挂起失败] PID={pid} 当前状态={pcb.state.value}，无法挂起")
            return False

    def activate_process(self, pid: int) -> bool:
        """
        激活进程

        将被挂起的进程重新调入内存，恢复为就绪状态。

        参数:
            pid: 要激活的进程ID

        返回:
            成功返回True，失败返回False
        """
        pcb = self.processes.get(pid)
        if pcb is None:
            return False

        if pcb.state == ProcessState.SUSPENDED:
            # 重新分配内存
            addr = self.resource_manager.allocate(pcb.memory_size, pid=pid)
            if addr is None:
                self.creation_log.append(
                    f"[激活失败] PID={pid} 内存不足，无法调入内存")
                return False
            pcb.allocated_memory = addr
            pcb.state = ProcessState.READY
            self.creation_log.append(
                f"[激活成功] PID={pid} 名称='{pcb.name}' 已调入内存，地址=0x{addr:04X}")
            return True
        else:
            self.creation_log.append(
                f"[激活失败] PID={pid} 当前状态={pcb.state.value}，非挂起状态")
            return False

    def get_process(self, pid: int) -> Optional[PCB]:
        """获取指定PID的进程"""
        return self.processes.get(pid)

    def get_all_processes(self) -> List[PCB]:
        """获取所有进程列表"""
        return list(self.processes.values())

    def get_ready_processes(self) -> List[PCB]:
        """获取所有就绪状态的进程"""
        return [p for p in self.processes.values() if p.state == ProcessState.READY]

    def get_memory_info(self) -> dict:
        """获取当前内存使用信息"""
        return self.resource_manager.get_info()

    def get_log(self) -> List[str]:
        """获取操作日志"""
        return self.creation_log.copy()

    def clear(self):
        """清空所有进程"""
        self.processes.clear()
        self._next_pid = 1
        self.resource_manager.reset()
        self.creation_log.clear()

    def reset_for_scheduling(self):
        """重置所有进程的运行时统计（用于多次调度测试）"""
        for pcb in self.processes.values():
            pcb.reset()
