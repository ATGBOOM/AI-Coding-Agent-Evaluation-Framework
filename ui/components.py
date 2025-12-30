"""
Reusable UI components for the evaluation dashboard.

This module contains functions that render different parts of the UI.
To add new components, simply add a new function following the existing patterns.
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any, Optional, List
import plotly.graph_objects as go
import plotly.express as px

from ui.config import (
    MetricConfig,
    MetricCategory,
    CORRECTNESS_METRICS,
    EXPLAINABILITY_METRICS,
    AGGREGATED_METRICS,
    get_metrics_by_category
)
from evaluators.correctness import CorrectnessResult, AggregatedMetrics


def render_metric_card(metric: MetricConfig, value: Any):
    """
    Render a single metric card.

    Args:
        metric: MetricConfig defining how to display the metric
        value: The metric value to display
    """
    formatted_value = metric.format_value(value)
    icon = metric.icon if metric.icon else ""

    st.metric(
        label=f"{icon} {metric.label}",
        value=formatted_value,
        help=metric.description
    )


def render_metrics_grid(result: Dict[str, Any], metrics: List[MetricConfig], columns: int = 3):
    """
    Render a grid of metric cards.

    Args:
        result: Evaluation result dictionary
        metrics: List of MetricConfig objects to display
        columns: Number of columns in the grid
    """
    cols = st.columns(columns)

    for idx, metric in enumerate(metrics):
        col_idx = idx % columns

        # Extract value using extractor function if provided
        if metric.extractor:
            try:
                value = metric.extractor(result)
            except (KeyError, AttributeError, TypeError):
                value = None
        else:
            value = result.get(metric.key)

        with cols[col_idx]:
            render_metric_card(metric, value)


def render_correctness_section(result: Dict[str, Any]):
    """
    Render the correctness metrics section.

    Args:
        result: Evaluation result dictionary
    """
    st.subheader("📊 Correctness Metrics")

    correctness_result = result.get('correctness_result')

    if not correctness_result:
        st.warning("No correctness evaluation available")
        return

    # Main metrics grid
    render_metrics_grid(result, CORRECTNESS_METRICS, columns=5)

    # Error details if failed
    if not correctness_result.passed and correctness_result.errors:
        with st.expander("❌ Error Details", expanded=False):
            for idx, error in enumerate(correctness_result.errors, 1):
                st.code(error, language="text")


def render_llm_test_correctness(result: Dict[str, Any]):
    """
    Render LLM-generated test correctness section.

    Args:
        result: Evaluation result dictionary
    """
    st.subheader("🧪 LLM-Generated Test Correctness")

    llm_tests_correctness = result.get('llm_tests_correctness')

    if not llm_tests_correctness:
        st.info("No LLM-generated tests available")
        return

    # Create temporary result dict for LLM test metrics
    llm_test_result = {'correctness_result': llm_tests_correctness}

    # Display metrics
    render_metrics_grid(llm_test_result, CORRECTNESS_METRICS[:3], columns=3)

    # Error details if failed
    if not llm_tests_correctness.passed and llm_tests_correctness.errors:
        with st.expander("❌ Error Details", expanded=False):
            for error in llm_tests_correctness.errors:
                st.code(error, language="text")


def render_explainability_section(result: Dict[str, Any]):
    """
    Render the explainability metrics section.

    Args:
        result: Evaluation result dictionary
    """
    st.subheader("💭 Explainability")

    # Metrics grid
    render_metrics_grid(result, EXPLAINABILITY_METRICS, columns=3)

    # Detailed thought process
    if result.get('thought'):
        with st.expander("🧠 Line of Thought", expanded=True):
            st.write(result['thought'])


def render_code_section(result: Dict[str, Any]):
    """
    Render the code solution section.

    Args:
        result: Evaluation result dictionary
    """
    st.subheader("💻 Generated Solution")

    if result.get('llm_solution'):
        st.code(result['llm_solution'], language='python', line_numbers=True)
    else:
        st.warning("No solution available")


def render_test_cases_section(result: Dict[str, Any]):
    """
    Render the test cases section.

    Args:
        result: Evaluation result dictionary
    """
    st.subheader("🧪 LLM-Generated Test Cases")

    if result.get('test_cases'):
        st.code(result['test_cases'], language='python', line_numbers=True)
    else:
        st.info("No test cases generated")


def render_canonical_comparison(result: Dict[str, Any]):
    """
    Render comparison with canonical solution.

    Args:
        result: Evaluation result dictionary
    """
    with st.expander("📖 Compare with Canonical Solution", expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Canonical Solution:**")
            st.code(result.get('canonical_solution', 'N/A'), language='python')

        with col2:
            st.markdown("**LLM Solution:**")
            st.code(result.get('llm_solution', 'N/A'), language='python')

        # Validation status
        canonical_result = result.get('canonical_test_result')
        if canonical_result:
            status = "✅ PASSED" if canonical_result.passed else "❌ FAILED"
            st.info(f"Canonical Solution Validation: {status}")


def render_problem_prompt(result: Dict[str, Any]):
    """
    Render the problem prompt section.

    Args:
        result: Evaluation result dictionary
    """
    with st.expander("📝 Problem Prompt", expanded=False):
        st.code(result.get('prompt', 'N/A'), language='python')


def render_aggregated_metrics(metrics: AggregatedMetrics):
    """
    Render aggregated metrics from batch evaluation.

    Args:
        metrics: AggregatedMetrics object
    """
    st.header("📈 Aggregated Metrics")

    # Convert to dict for rendering
    metrics_dict = metrics.to_dict()

    # Top-level metrics
    st.subheader("Overall Statistics")
    render_metrics_grid(metrics_dict, AGGREGATED_METRICS, columns=4)

    # Pass@k metrics
    if metrics.pass_at_k:
        st.subheader("Pass@k Analysis")

        # Create dataframe for chart
        pass_at_k_df = pd.DataFrame([
            {"k": k, "pass@k": v, "percentage": v * 100}
            for k, v in sorted(metrics.pass_at_k.items())
        ])

        col1, col2 = st.columns([2, 1])

        with col1:
            # Line chart
            fig = px.line(
                pass_at_k_df,
                x='k',
                y='percentage',
                markers=True,
                title='Pass@k Performance',
                labels={'percentage': 'Success Rate (%)', 'k': 'k (number of samples)'}
            )
            fig.update_layout(
                yaxis_range=[0, 100],
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Table
            st.dataframe(
                pass_at_k_df[['k', 'percentage']].rename(columns={'percentage': 'Pass Rate (%)'}),
                hide_index=True,
                use_container_width=True
            )


def render_batch_results_table(results: List[Dict[str, Any]]):
    """
    Render a table of batch evaluation results.

    Args:
        results: List of evaluation result dictionaries
    """
    st.subheader("📋 Individual Task Results")

    # Extract data for table
    table_data = []
    for result in results:
        correctness = result.get('correctness_result')
        if correctness:
            table_data.append({
                'Task ID': result.get('task_id'),
                'Status': '✅' if correctness.passed else '❌',
                'Pass@1': f"{correctness.pass_at_1:.2f}",
                'Test Pass Rate': f"{correctness.test_pass_rate:.1f}%",
                'Tests Passed': f"{correctness.num_passed}/{correctness.total_tests}",
                'Confidence': result.get('confidence', 'N/A'),
                'Has Tests': '✅' if result.get('test_cases') else '❌'
            })

    if table_data:
        df = pd.DataFrame(table_data)

        # Add filtering
        col1, col2 = st.columns([1, 3])
        with col1:
            filter_status = st.selectbox(
                "Filter by Status",
                ["All", "Passed Only", "Failed Only"]
            )

        # Apply filter
        if filter_status == "Passed Only":
            df = df[df['Status'] == '✅']
        elif filter_status == "Failed Only":
            df = df[df['Status'] == '❌']

        # Display table
        st.dataframe(
            df,
            hide_index=True,
            use_container_width=True,
            column_config={
                "Status": st.column_config.TextColumn("Status", width="small"),
                "Task ID": st.column_config.NumberColumn("Task ID", width="small"),
            }
        )

        # Download button
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download Results CSV",
            data=csv,
            file_name="evaluation_results.csv",
            mime="text/csv"
        )
    else:
        st.warning("No results to display")


def render_task_selector(max_task_id: int = 163):
    """
    Render task selection controls.

    Args:
        max_task_id: Maximum task ID available

    Returns:
        Selected task ID
    """
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        task_id = st.number_input(
            "Task ID",
            min_value=0,
            max_value=max_task_id,
            value=0,
            help=f"Select a task ID between 0 and {max_task_id}"
        )

    with col2:
        st.write("")  # Spacing
        st.write("")  # Spacing
        prev_disabled = task_id <= 0
        if st.button("⬅️ Previous", disabled=prev_disabled):
            task_id = max(0, task_id - 1)

    with col3:
        st.write("")  # Spacing
        st.write("")  # Spacing
        next_disabled = task_id >= max_task_id
        if st.button("Next ➡️", disabled=next_disabled):
            task_id = min(max_task_id, task_id + 1)

    return task_id


def render_batch_controls():
    """
    Render batch evaluation controls.

    Returns:
        Tuple of (start_id, end_id)
    """
    col1, col2 = st.columns(2)

    with col1:
        start_id = st.number_input(
            "Start Task ID",
            min_value=0,
            max_value=163,
            value=0
        )

    with col2:
        end_id = st.number_input(
            "End Task ID (exclusive)",
            min_value=1,
            max_value=164,
            value=5
        )

    if start_id >= end_id:
        st.error("End ID must be greater than Start ID")
        return None, None

    return start_id, end_id
