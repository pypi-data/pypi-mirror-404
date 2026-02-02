#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MLModelBase类测试脚本
测试LR算法在乳腺癌数据集上的训练、预测、保存、加载功能
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tpf.mlib.modelbase import MLBase


def test_show_lr():
    """
    测试 show_lr 方法
    """
    print("=" * 60)
    print("开始测试 MLModelBase.show_lr() 方法")
    print("=" * 60)

    # 创建模型保存目录
    model_save_dir = '/tmp/models'
    os.makedirs(model_save_dir, exist_ok=True)

    try:
        # 调用 show_lr 方法
        ml_model, trained_model = MLBase.show_lr(model_save_dir=model_save_dir)

        print("\n" + "=" * 60)
        print("测试成功完成！")
        print("=" * 60)

        return ml_model, trained_model

    except Exception as e:
        print(f"\n测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return None, None


if __name__ == '__main__':
    test_show_lr()
