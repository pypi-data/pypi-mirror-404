#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
TextPreDeal.clean_text 方法测试脚本
"""

import pandas as pd
import sys
import os
sys.path.insert(0, '/ai/wks/aitpf/src')

from tpf.nlp.text import TextPreDeal


def test_clean_text_remove_mode():
    """测试1: clean_text 移除模式 (is_remove=True)"""
    print("=" * 70)
    print("测试1: clean_text 移除模式 (is_remove=True)")
    print("=" * 70)

    tp = TextPreDeal(use_custom_dict=True, min_word_length=2)

    test_cases = [
        # (原始文本, 预期结果关键词)
        ("<p>HTML标签</p>", "HTML标签"),
        ("访问 http://example.com 查看", "访问 查看"),
        ("邮箱test@example.com联系", "邮箱联系"),
        ("手机13812345678联系", "手机联系"),
        ("电话: 13812345678", "电话"),
        ("身份证123456789012345678", "身份证"),
        ("银行卡号6217000012345678901", "银行卡号"),
        ("日期2024-01-01到期", "日期到期"),
        ("金额1000元整", "金额整"),
        ("地址：北京市朝阳区", "地址："),
    ]

    print("\n测试结果:")
    for i, (text, expected_keyword) in enumerate(test_cases, 1):
        result = tp.clean_text(text, is_remove=True)
        print(f"\n{i}. 原始: {text}")
        print(f"   结果: {result}")

        # 验证敏感信息被移除
        if expected_keyword in result:
            print(f"   ✓ 通过 - 包含预期关键词: '{expected_keyword}'")
        else:
            print(f"   ✗ 失败 - 未找到预期关键词: '{expected_keyword}'")

    print("\n✓ 测试1完成\n")


def test_clean_text_mask_mode():
    """测试2: clean_text 脱敏模式 (is_remove=False)"""
    print("=" * 70)
    print("测试2: clean_text 脱敏模式 (is_remove=False)")
    print("=" * 70)

    tp = TextPreDeal(use_custom_dict=True, min_word_length=2)

    test_cases = [
        # (原始文本, 预期占位符)
        ("手机13812345678联系", "[手机号]"),
        ("电话: 13812345678", "[手机号]"),
        ("身份证123456789012345678", "[身份证号]"),
        ("银行卡号6217000012345678901", "[银行卡号]"),
        ("邮箱test@example.com联系", "[邮箱地址]"),
        ("日期2024-01-01到期", "[日期]"),
        ("金额1000元整", "[金额]"),
        ("地址：北京市朝阳区", "[地址]"),
        ("客户姓名：张三123", "[姓名]"),
        ("建设银行网点", "[银行名称]"),
    ]

    print("\n测试结果:")
    for i, (text, expected_placeholder) in enumerate(test_cases, 1):
        result = tp.clean_text(text, is_remove=False)
        print(f"\n{i}. 原始: {text}")
        print(f"   结果: {result}")

        # 验证占位符存在
        if expected_placeholder in result:
            print(f"   ✓ 通过 - 包含预期占位符: '{expected_placeholder}'")
        else:
            print(f"   ✗ 失败 - 未找到预期占位符: '{expected_placeholder}'")

    print("\n✓ 测试2完成\n")


def test_complex_text():
    """测试3: 复杂文本清洗"""
    print("=" * 70)
    print("测试3: 复杂文本清洗")
    print("=" * 70)

    tp = TextPreDeal(use_custom_dict=True, min_word_length=2)

    complex_text = """
    客户张三，手机号13812345678，于2024-01-15在建设银行北京朝阳区网点
    办理业务，银行卡号6217000012345678901，交易金额5000元，订单号TX2024011512345。
    联系邮箱：zhangsan@example.com，身份证号：123456789012345678。
    """

    print("\n原始文本:")
    print(complex_text)

    print("\n" + "-" * 70)
    print("移除模式 (is_remove=True):")
    print("-" * 70)
    result_remove = tp.clean_text(complex_text, is_remove=True)
    print(result_remove)

    print("\n" + "-" * 70)
    print("脱敏模式 (is_remove=False):")
    print("-" * 70)
    result_mask = tp.clean_text(complex_text, is_remove=False)
    print(result_mask)

    # 验证移除模式
    assert '13812345678' not in result_remove
    assert '2024-01-15' not in result_remove
    assert '6217000012345678901' not in result_remove
    assert '5000' not in result_remove
    print("\n✓ 移除模式验证通过")

    # 验证脱敏模式
    assert '[手机号]' in result_mask
    assert '[日期]' in result_mask
    assert '[银行卡号]' in result_mask
    assert '[金额]' in result_mask
    assert '[银行名称]' in result_mask
    print("✓ 脱敏模式验证通过")

    print("\n✓ 测试3完成\n")


def test_with_real_data():
    """测试4: 使用真实数据文件"""
    print("=" * 70)
    print("测试4: 使用真实数据文件")
    print("=" * 70)

    data_dir = "/ai/wks/alg/data/tousu/yushi_2026010"

    # 查找数据文件
    if os.path.exists(data_dir):
        files = [f for f in os.listdir(data_dir) if f.endswith(('.csv', '.txt', '.json'))]
        if files:
            print(f"\n找到数据文件: {files[0]}")
            file_path = os.path.join(data_dir, files[0])

            try:
                # 读取数据
                if files[0].endswith('.csv'):
                    df = pd.read_csv(file_path, nrows=5)
                    print(f"\n数据列名: {df.columns.tolist()}")

                    # 找到文本列
                    text_col = None
                    for col in df.columns:
                        if 'text' in col.lower() or '内容' in col or '描述' in col:
                            text_col = col
                            break

                    if text_col is None and len(df.columns) > 0:
                        text_col = df.columns[0]

                    if text_col:
                        print(f"使用列: {text_col}\n")

                        tp = TextPreDeal(use_custom_dict=True, min_word_length=2)

                        for idx, row in df.iterrows():
                            if idx >= 3:  # 只测试前3条
                                break
                            original_text = str(row[text_col])[:100]  # 只取前100字符
                            print(f"原始: {original_text}")

                            result_remove = tp.clean_text(original_text, is_remove=True)
                            print(f"移除: {result_remove}")

                            result_mask = tp.clean_text(original_text, is_remove=False)
                            print(f"脱敏: {result_mask}")
                            print("-" * 70)

                else:
                    print("文件格式不支持，仅支持CSV文件")

            except Exception as e:
                print(f"读取文件出错: {e}")
        else:
            print(f"目录 {data_dir} 中没有找到数据文件")
    else:
        print(f"数据目录不存在: {data_dir}")

    print("\n✓ 测试4完成\n")


def test_edge_cases():
    """测试5: 边界情况"""
    print("=" * 70)
    print("测试5: 边界情况")
    print("=" * 70)

    tp = TextPreDeal(use_custom_dict=True, min_word_length=2)

    edge_cases = [
        ("", "空字符串"),
        (None, "None值"),
        (12345, "数字类型"),
        ("   ", "纯空格"),
        ("正常文本，无敏感信息", "正常文本"),
    ]

    print("\n测试结果:")
    for value, desc in edge_cases:
        result = tp.clean_text(value, is_remove=True)
        print(f"\n{desc}: {repr(value)}")
        print(f"结果: {repr(result)}")

    print("\n✓ 测试5完成\n")


def test_performance():
    """测试6: 性能测试"""
    print("=" * 70)
    print("测试6: 性能测试")
    print("=" * 70)

    import time

    tp = TextPreDeal(use_custom_dict=True, min_word_length=2)

    # 生成测试文本
    test_text = "客户张三，手机13812345678，身份证123456789012345678，金额1000元。" * 10

    iterations = 100

    # 测试移除模式
    start = time.time()
    for _ in range(iterations):
        tp.clean_text(test_text, is_remove=True)
    time_remove = time.time() - start

    # 测试脱敏模式
    start = time.time()
    for _ in range(iterations):
        tp.clean_text(test_text, is_remove=False)
    time_mask = time.time() - start

    print(f"\n迭代次数: {iterations}")
    print(f"移除模式耗时: {time_remove:.3f}秒 ({time_remove/iterations*1000:.2f}ms/次)")
    print(f"脱敏模式耗时: {time_mask:.3f}秒 ({time_mask/iterations*1000:.2f}ms/次)")

    print("\n✓ 测试6完成\n")


if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("  TextPreDeal.clean_text 方法测试套件")
    print("=" * 70)
    print()

    try:
        test_clean_text_remove_mode()
        test_clean_text_mask_mode()
        test_complex_text()
        test_with_real_data()
        test_edge_cases()
        test_performance()

        print("=" * 70)
        print("  所有测试完成！✓")
        print("=" * 70)

    except AssertionError as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"\n✗ 发生错误: {e}")
        import traceback
        traceback.print_exc()
