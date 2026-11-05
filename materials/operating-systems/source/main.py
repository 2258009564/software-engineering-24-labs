"""
进程调度机制设计系统 — 主程序入口
===================================

本程序是操作系统课程设计的完整实现，模拟操作系统的进程调度机制。

功能概述：
    1. 进程控制：创建、撤销、挂起、激活进程，显示进程状态
    2. 资源管理：内存分配与回收，实时显示资源变化
    3. 调度算法：实现FCFS、SJF、RR、EDF、RMS五种调度算法
    4. 性能分析：采集周转时间、等待时间、响应时间等指标并对比
    5. 图形界面：PyQt5实现的完整GUI，含甘特图、内存图、对比图表

运行方式：
    python main.py

依赖安装：
    pip install PyQt5

开发信息：
    课程：课程设计（操作系统）
    班级：软件24-4班
    第1组
    组长：梁震宇（2404060404）
"""

import sys
import os

# 确保能导入同目录下的模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def check_dependencies():
    """检查依赖库是否安装"""
    try:
        import PyQt5
    except ImportError:
        print("=" * 50)
        print("错误：未安装 PyQt5 库")
        print("请执行以下命令安装：")
        print("    pip install PyQt5")
        print("=" * 50)
        sys.exit(1)


def main():
    """主函数"""
    check_dependencies()

    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtGui import QFont
    from gui import MainWindow, STYLESHEET

    app = QApplication(sys.argv)

    # 设置全局字体
    font = QFont("Microsoft YaHei", 10)
    app.setFont(font)

    # 应用样式
    app.setStyleSheet(STYLESHEET)

    # 创建主窗口
    window = MainWindow()
    window.show()

    print("进程调度机制设计系统已启动")
    print("=" * 50)
    print("课程：课程设计（操作系统）")
    print("班级：软件24-4班 | 第1组")
    print("组长：梁震宇（2404060404）")
    print("=" * 50)

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
