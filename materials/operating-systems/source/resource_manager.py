"""
资源管理器模块
================
模拟操作系统的内存资源管理功能，采用分区分配策略。
负责内存的分配、回收，以及资源使用情况的统计和显示。

分配策略：首次适应算法（First-Fit）
    从内存起始位置开始扫描，找到第一个足够大的空闲分区进行分配。
    该算法简单高效，是实际操作系统中常用的内存分配策略。
"""

from typing import List, Optional, Dict
from dataclasses import dataclass


@dataclass
class MemoryBlock:
    """
    内存块
    ======
    表示一个连续的内存区域，可以是空闲块或已分配块。
    """
    start_addr: int      # 起始地址
    size: int            # 块大小（MB）
    allocated: bool = False  # 是否已分配
    pid: Optional[int] = None  # 占用该块的进程PID（已分配时）

    @property
    def end_addr(self) -> int:
        """结束地址"""
        return self.start_addr + self.size


class ResourceManager:
    """
    资源管理器
    ==========
    管理系统内存资源，支持动态分配和回收。

    使用空闲分区链表管理内存，采用首次适应算法进行分配。
    回收时会自动合并相邻的空闲块，减少外部碎片。

    示例:
        rm = ResourceManager(1024)  # 1024MB总内存
        addr = rm.allocate(256)     # 分配256MB
        rm.deallocate(addr, 256)    # 回收
    """

    def __init__(self, total_memory: int = 1024):
        """
        初始化资源管理器

        参数:
            total_memory: 系统总内存大小（MB）
        """
        self.total_memory = total_memory
        self.used_memory = 0
        # 初始时整个内存是一块空闲区域
        self.blocks: List[MemoryBlock] = [
            MemoryBlock(start_addr=0, size=total_memory, allocated=False)
        ]

    def allocate(self, size: int, pid: Optional[int] = None) -> Optional[int]:
        """
        分配内存（首次适应算法）

        参数:
            size: 需要分配的内存大小（MB）
            pid: 占用该内存块的进程PID

        返回:
            分配的起始地址，内存不足时返回None
        """
        if size <= 0 or size > self.total_memory:
            return None

        for i, block in enumerate(self.blocks):
            if not block.allocated and block.size >= size:
                # 找到合适的空闲块
                addr = block.start_addr

                if block.size == size:
                    # 刚好分配整个块
                    block.allocated = True
                    block.pid = pid
                else:
                    # 分割块：分配前半部分，保留后半部分为空闲
                    block.size -= size
                    new_block = MemoryBlock(
                        start_addr=addr, size=size,
                        allocated=True, pid=pid
                    )
                    # 更新原块的起始地址
                    block.start_addr = addr + size
                    self.blocks.insert(i, new_block)

                self.used_memory += size
                return addr

        return None  # 没有足够大的空闲块

    def deallocate(self, addr: Optional[int], size: int):
        """
        回收内存

        参数:
            addr: 要回收的内存起始地址
            size: 要回收的内存大小
        """
        if addr is None or size <= 0:
            return

        for i, block in enumerate(self.blocks):
            if block.allocated and block.start_addr == addr and block.size == size:
                block.allocated = False
                block.pid = None
                self.used_memory -= size
                # 合并相邻空闲块
                self._merge_blocks()
                return

    def _merge_blocks(self):
        """合并相邻的空闲内存块，减少碎片"""
        i = 0
        while i < len(self.blocks) - 1:
            current = self.blocks[i]
            next_block = self.blocks[i + 1]
            if (not current.allocated and not next_block.allocated and
                    current.end_addr == next_block.start_addr):
                # 合并
                current.size += next_block.size
                self.blocks.pop(i + 1)
            else:
                i += 1

    @property
    def available_memory(self) -> int:
        """可用内存"""
        return self.total_memory - self.used_memory

    @property
    def utilization(self) -> float:
        """内存利用率（百分比）"""
        if self.total_memory == 0:
            return 0.0
        return (self.used_memory / self.total_memory) * 100

    def get_info(self) -> dict:
        """获取内存使用信息摘要"""
        return {
            "总内存(MB)": self.total_memory,
            "已用内存(MB)": self.used_memory,
            "可用内存(MB)": self.available_memory,
            "内存利用率(%)": round(self.utilization, 2),
            "空闲块数": sum(1 for b in self.blocks if not b.allocated),
            "已分配块数": sum(1 for b in self.blocks if b.allocated),
        }

    def get_block_list(self) -> List[dict]:
        """获取所有内存块的详细信息"""
        return [
            {
                "起始地址": f"0x{b.start_addr:04X}",
                "大小(MB)": b.size,
                "状态": "已分配" if b.allocated else "空闲",
                "PID": b.pid if b.pid else "-",
            }
            for b in self.blocks
        ]

    def reset(self):
        """重置内存管理器"""
        self.used_memory = 0
        self.blocks = [MemoryBlock(start_addr=0, size=self.total_memory, allocated=False)]
