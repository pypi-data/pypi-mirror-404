# -*- coding: utf-8 -*-
"""DataDeal data_filter method test cases"""

import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from d1 import DataDeal


def test_data_filter_basic():
    """Test basic functionality with default column names"""
    print("=" * 60)
    print("Test 1: Basic functionality")
    print("=" * 60)

    data = {
        'sim_text': ['text1', 'text2', 'text3', 'text4', 'text5', 'text6', 'text7', 'text8'],
        'sim_label': ['A', 'A', 'A', 'B', 'B', 'B', 'C', 'C'],
        'sim_score': [0.9, 0.7, 0.5, 0.8, 0.6, 0.4, 0.95, 0.85],
        'mean_score': [0.8, 0.6, 0.4, 0.7, 0.5, 0.3, 0.9, 0.8],
        'real_label': ['X', 'X', 'Y', 'X', 'Y', 'Y', 'X', 'X'],
        'query_text': ['q1', 'q2', 'q3', 'q4', 'q5', 'q6', 'q7', 'q8'],
        'match': [1, 0, 1, 1, 0, 0, 1, 1],
        'is_ok': [True, False, True, True, False, False, True, True]
    }

    df = pd.DataFrame(data)
    print("\nOriginal data:")
    print(df)
    print(f"\nOriginal shape: {df.shape}")

    df_filtered = DataDeal.data_filter(df, top_k=2)

    print("\nFiltered data (top_k=2):")
    print(df_filtered)
    print(f"\nFiltered shape: {df_filtered.shape}")

    print("\nVerification:")
    print(f"Group A count: {len(df_filtered[df_filtered['sim_label'] == 'A'])} (expected: 2)")
    print(f"Group B count: {len(df_filtered[df_filtered['sim_label'] == 'B'])} (expected: 2)")
    print(f"Group C count: {len(df_filtered[df_filtered['sim_label'] == 'C'])} (expected: 2)")

    for label in ['A', 'B', 'C']:
        group_data = df_filtered[df_filtered['sim_label'] == label]
        scores = group_data['sim_score'].values
        is_descending = all(scores[i] >= scores[i + 1] for i in range(len(scores) - 1))
        print(f"Group {label} descending order: {is_descending}")

    print("\n" + "=" * 60 + "\n")


def test_data_filter_custom_columns():
    """Test with custom column names"""
    print("=" * 60)
    print("Test 2: Custom column names")
    print("=" * 60)

    data = {
        'category': ['type1', 'type1', 'type1', 'type2', 'type2'],
        'score': [100, 80, 60, 90, 70],
        'name': ['item1', 'item2', 'item3', 'item4', 'item5']
    }

    df = pd.DataFrame(data)
    print("\nOriginal data:")
    print(df)

    df_filtered = DataDeal.data_filter(
        df,
        group_col='category',
        score_col='score',
        top_k=2
    )

    print("\nFiltered data:")
    print(df_filtered)
    print(f"\nFiltered shape: {df_filtered.shape}")

    print("\n" + "=" * 60 + "\n")


def test_data_filter_edge_cases():
    """Test edge cases"""
    print("=" * 60)
    print("Test 3: Edge cases")
    print("=" * 60)

    print("\nCase 1: Group size less than top_k")
    data = {
        'sim_label': ['A', 'A', 'B'],
        'sim_score': [0.9, 0.7, 0.8],
        'text': ['t1', 't2', 't3']
    }
    df = pd.DataFrame(data)
    print("Original data:")
    print(df)

    df_filtered = DataDeal.data_filter(df, top_k=5)
    print("\nFiltered data (top_k=5, but group A has 2 rows, group B has 1 row):")
    print(df_filtered)

    print("\nCase 2: Empty dataframe")
    df_empty = pd.DataFrame({'sim_label': [], 'sim_score': [], 'text': []})
    print("Original data: empty dataframe")
    df_filtered_empty = DataDeal.data_filter(df_empty, top_k=2)
    print(f"Filtered shape: {df_filtered_empty.shape}")

    print("\nCase 3: top_k=1")
    data3 = {
        'sim_label': ['A', 'A', 'B', 'B', 'C', 'C'],
        'sim_score': [0.5, 0.9, 0.3, 0.7, 0.6, 0.4],
        'text': ['t1', 't2', 't3', 't4', 't5', 't6']
    }
    df3 = pd.DataFrame(data3)
    print("Original data:")
    print(df3)

    df_filtered3 = DataDeal.data_filter(df3, top_k=1)
    print("\nFiltered data (top_k=1, take highest score from each group):")
    print(df_filtered3)

    print("\n" + "=" * 60 + "\n")


def test_data_filter_multi_column_grouping():
    """Test multi-column grouping functionality"""
    print("=" * 60)
    print("Test 4: Multi-column grouping")
    print("=" * 60)

    data = {
        'category': ['A', 'A', 'A', 'A', 'B', 'B', 'B', 'B', 'C', 'C', 'C', 'C'],
        'subcategory': ['X', 'X', 'Y', 'Y', 'X', 'X', 'Y', 'Y', 'X', 'X', 'Y', 'Y'],
        'score': [90, 80, 70, 60, 95, 85, 75, 65, 88, 78, 68, 58],
        'name': ['item1', 'item2', 'item3', 'item4', 'item5', 'item6', 'item7', 'item8', 'item9', 'item10', 'item11', 'item12']
    }

    df = pd.DataFrame(data)
    print("\nOriginal data:")
    print(df)
    print(f"\nOriginal shape: {df.shape}")

    df_filtered = DataDeal.data_filter(
        df,
        group_col=['category', 'subcategory'],
        score_col='score',
        top_k=1
    )

    print("\nFiltered data (multi-column grouping, top_k=1):")
    print(df_filtered)
    print(f"\nFiltered shape: {df_filtered.shape}")

    print("\nVerification:")
    expected_groups = [('A', 'X'), ('A', 'Y'), ('B', 'X'), ('B', 'Y'), ('C', 'X'), ('C', 'Y')]
    for cat, subcat in expected_groups:
        group_count = len(df_filtered[
            (df_filtered['category'] == cat) & 
            (df_filtered['subcategory'] == subcat)
        ])
        print(f"Group ({cat}, {subcat}): {group_count} rows (expected: 1)")

    print("\n" + "=" * 60 + "\n")


def test_data_filter_multi_column_top_k():
    """Test multi-column grouping with different top_k values"""
    print("=" * 60)
    print("Test 5: Multi-column grouping with top_k=2")
    print("=" * 60)

    data = {
        'category': ['A', 'A', 'A', 'A', 'A', 'A', 'B', 'B', 'B', 'B'],
        'subcategory': ['X', 'X', 'X', 'Y', 'Y', 'Y', 'X', 'X', 'Y', 'Y'],
        'score': [100, 90, 80, 85, 75, 65, 95, 88, 78, 68],
        'name': ['i1', 'i2', 'i3', 'i4', 'i5', 'i6', 'i7', 'i8', 'i9', 'i10']
    }

    df = pd.DataFrame(data)
    print("\nOriginal data:")
    print(df)

    df_filtered = DataDeal.data_filter(
        df,
        group_col=['category', 'subcategory'],
        score_col='score',
        top_k=2
    )

    print("\nFiltered data (top_k=2):")
    print(df_filtered)
    print(f"\nFiltered shape: {df_filtered.shape}")

    print("\nVerification:")
    groups = [('A', 'X'), ('A', 'Y'), ('B', 'X'), ('B', 'Y')]
    for cat, subcat in groups:
        group_count = len(df_filtered[
            (df_filtered['category'] == cat) & 
            (df_filtered['subcategory'] == subcat)
        ])
        print(f"Group ({cat}, {subcat}): {group_count} rows (expected: 2)")

    print("\n" + "=" * 60 + "\n")


def test_data_filter_backward_compatibility():
    """Test backward compatibility with single column grouping"""
    print("=" * 60)
    print("Test 6: Backward compatibility (single column as string)")
    print("=" * 60)

    data = {
        'sim_label': ['A', 'A', 'A', 'B', 'B', 'B'],
        'sim_score': [0.9, 0.7, 0.5, 0.8, 0.6, 0.4],
        'text': ['t1', 't2', 't3', 't4', 't5', 't6']
    }

    df = pd.DataFrame(data)
    print("\nOriginal data:")
    print(df)

    df_filtered = DataDeal.data_filter(df, group_col='sim_label', top_k=2)
    print("\nFiltered with group_col='sim_label' (string):")
    print(df_filtered)

    df_filtered_list = DataDeal.data_filter(df, group_col=['sim_label'], top_k=2)
    print("\nFiltered with group_col=['sim_label'] (list):")
    print(df_filtered_list)

    print("\nVerification - Both methods produce same result:")
    print(f"String param result count: {len(df_filtered)}")
    print(f"List param result count: {len(df_filtered_list)}")
    print(f"Results are identical: {df_filtered.equals(df_filtered_list)}")

    print("\n" + "=" * 60 + "\n")


def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("Testing DataDeal.data_filter method (Enhanced with Multi-column)")
    print("=" * 60 + "\n")

    test_data_filter_basic()
    test_data_filter_custom_columns()
    test_data_filter_edge_cases()
    test_data_filter_multi_column_grouping()
    test_data_filter_multi_column_top_k()
    test_data_filter_backward_compatibility()

    print("=" * 60)
    print("All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
