"""
Streamlit Dashboard for LLM Coding Agent Evaluation.

This is the main entry point for the evaluation dashboard.
Run with: streamlit run app.py
"""

import streamlit as st
from typing import Dict, List, Any

from evaluators.context_handling import ContextHandlingEvaluator
from utils.context_tasks import load_context_tasks

from evaluation_runner import EvaluationRunner
from ui.components import (
    render_correctness_section,
    render_llm_test_correctness,
    render_explainability_section,
    render_code_section,
    render_test_cases_section,
    render_canonical_comparison,
    render_problem_prompt,
    render_aggregated_metrics,
    render_batch_results_table,
    render_task_selector,
    render_batch_controls
)


# =============================================================================
# PAGE CONFIGURATION
# =============================================================================

st.set_page_config(
    page_title="LLM Coding Agent Evaluator",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =============================================================================
# SESSION STATE INITIALIZATION
# =============================================================================

def init_session_state():
    """Initialize session state variables."""
    if 'runner' not in st.session_state:
        st.session_state.runner = None
    if 'current_result' not in st.session_state:
        st.session_state.current_result = None
    if 'batch_results' not in st.session_state:
        st.session_state.batch_results = None
    if 'aggregated_metrics' not in st.session_state:
        st.session_state.aggregated_metrics = None
    if 'task_id' not in st.session_state:
        st.session_state.task_id = 0
    if 'evaluator_initialized' not in st.session_state:
        st.session_state.evaluator_initialized = False
    if 'context_evaluator' not in st.session_state:
        st.session_state.context_evaluator = None
    if 'context_tasks' not in st.session_state:
        st.session_state.context_tasks = []


init_session_state()


# =============================================================================
# SIDEBAR - CONFIGURATION
# =============================================================================

with st.sidebar:
    st.title("⚙️ Configuration")

    st.markdown("---")

    st.subheader("API Settings")
    st.info("API key and model settings are loaded from .env file")

    # Initialize runner button
    if st.button("🚀 Initialize Evaluator", type="primary", use_container_width=True):
        try:
            with st.spinner("Initializing evaluation runner..."):
                st.session_state.runner = EvaluationRunner()
                st.session_state.context_evaluator = ContextHandlingEvaluator(st.session_state.runner.llm)
                st.session_state.context_tasks = load_context_tasks()
            st.session_state.evaluator_initialized = True
            st.success("✅ Evaluator initialized!")
        except Exception as e:
            st.error(f"❌ Initialization failed: {str(e)}")

    st.markdown("---")

    # Navigation
    st.subheader("📍 Navigation")
    page = st.radio(
        "Select View",
        ["Single Task Evaluation", "Batch Evaluation", "Context Handling", "About"],
        label_visibility="collapsed"
    )

    st.markdown("---")

    # Status
    st.subheader("📊 Status")
    if st.session_state.runner:
        st.success("✅ Evaluator Ready")
    else:
        st.warning("⚠️ Evaluator Not Initialized")

    if st.session_state.current_result:
        task_id = st.session_state.current_result.get('task_id')
        st.info(f"📋 Current Task: {task_id}")


# =============================================================================
# MAIN CONTENT
# =============================================================================

st.title("🤖 LLM Coding Agent Evaluation Dashboard")
st.markdown("Evaluate and analyze LLM-generated code solutions against the HumanEval benchmark")

# Check if runner is initialized
if not st.session_state.runner:
    st.warning("⚠️ Please initialize the evaluator from the sidebar to begin")
    st.stop()


# =============================================================================
# PAGE: SINGLE TASK EVALUATION
# =============================================================================

if page == "Single Task Evaluation":
    st.header("📝 Single Task Evaluation")

    # Task selector
    task_id = render_task_selector(max_task_id=163)
    st.session_state.task_id = task_id

    # Evaluation button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        run_button = st.button(
            f"▶️ Run Evaluation for Task {task_id}",
            type="primary",
            use_container_width=True
        )

    if run_button:
        try:
            with st.spinner(f"Evaluating task {task_id}..."):
                result = st.session_state.runner.generate_solution(task_id)
                st.session_state.current_result = result

            st.success(f"✅ Evaluation complete for task {task_id}")

        except Exception as e:
            st.error(f"❌ Evaluation failed: {str(e)}")
            st.exception(e)

    # Display results if available
    if st.session_state.current_result:
        result = st.session_state.current_result

        st.markdown("---")

        # Task info
        st.subheader(f"📋 Task {result.get('task_id')}")

        # Problem prompt
        render_problem_prompt(result)

        st.markdown("---")

        # Main content in tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 Metrics",
            "💻 Solution",
            "🧪 Tests",
            "📖 Comparison"
        ])

        with tab1:
            # Correctness metrics
            render_correctness_section(result)

            st.markdown("---")

            # LLM test correctness
            render_llm_test_correctness(result)

            st.markdown("---")

            # Explainability
            render_explainability_section(result)

        with tab2:
            render_code_section(result)

        with tab3:
            render_test_cases_section(result)

        with tab4:
            render_canonical_comparison(result)

elif page == "Context Handling":
    st.header("Context Handling (Retrieval + Utilisation)")

    if st.session_state.runner is None or st.session_state.context_evaluator is None:
        st.warning("Please initialize the evaluator from the sidebar first.")
    else:
        tasks = st.session_state.context_tasks
        options = [f"{t.id} — {t.title}" for t in tasks]
        selected = st.selectbox("Select a context task", options)
        top_k = st.slider("Top-K files to retrieve", min_value=1, max_value=5, value=3)

        selected_id = selected.split("—")[0].strip()
        task = next(t for t in tasks if t.id == selected_id)

        if st.button("Run Context Handling Evaluation"):
            with st.spinner("Running context handling evaluation..."):
                result = st.session_state.context_evaluator.evaluate(task, top_k=top_k)

            st.subheader("Results")
            st.write("**Retrieved files (retrieval output):**", result["retrieved_files"])
            st.write("**Gold files (ground truth):**", result["gold_files"])
            st.metric("retrieval_recall@k", f"{result['retrieval_recall_at_k']:.2f}")
            st.metric("answer_accuracy", f"{result['answer_accuracy']:.2f}")
            st.metric("context_handling_score", f"{result['context_handling_score']:.2f}")

            st.subheader("Model Answer")
            st.write(result["model_answer"])

            st.subheader("Expected Answer")
            st.write(result["expected_answer"])



# =============================================================================
# PAGE: BATCH EVALUATION
# =============================================================================

elif page == "Batch Evaluation":
    st.header("📊 Batch Evaluation")

    # Batch controls
    start_id, end_id = render_batch_controls()

    if start_id is not None and end_id is not None:
        # Run batch button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            run_batch = st.button(
                f"▶️ Run Batch Evaluation ({start_id} to {end_id-1})",
                type="primary",
                use_container_width=True
            )

        if run_batch:
            try:
                # Progress tracking
                progress_bar = st.progress(0)
                status_text = st.empty()

                total_tasks = end_id - start_id
                results = []
                correctness_results = []

                for idx, task_id in enumerate(range(start_id, end_id)):
                    status_text.text(f"Evaluating task {task_id}... ({idx+1}/{total_tasks})")

                    try:
                        result = st.session_state.runner.generate_solution(task_id)
                        results.append(result)

                        if result.get('correctness_result'):
                            correctness_results.append(result['correctness_result'])

                    except Exception as e:
                        st.warning(f"Failed to evaluate task {task_id}: {str(e)}")

                    progress_bar.progress((idx + 1) / total_tasks)

                status_text.text("✅ Batch evaluation complete!")
                st.session_state.batch_results = results

                # Aggregate metrics
                if correctness_results:
                    k_values = [1]
                    if len(correctness_results) >= 5:
                        k_values.extend([5, 10])

                    aggregated = st.session_state.runner.correctness_evaluator.aggregate_results(
                        results=correctness_results,
                        k_values=k_values
                    )
                    st.session_state.aggregated_metrics = aggregated

                st.success(f"✅ Evaluated {len(results)} tasks successfully!")

            except Exception as e:
                st.error(f"❌ Batch evaluation failed: {str(e)}")
                st.exception(e)

    # Display batch results if available
    if st.session_state.batch_results:
        st.markdown("---")

        # Aggregated metrics
        if st.session_state.aggregated_metrics:
            render_aggregated_metrics(st.session_state.aggregated_metrics)

        st.markdown("---")

        # Individual results table
        render_batch_results_table(st.session_state.batch_results)


# =============================================================================
# PAGE: ABOUT
# =============================================================================

elif page == "About":
    st.header("ℹ️ About This Dashboard")

    st.markdown("""
    ## LLM Coding Agent Evaluation Framework

    This dashboard evaluates LLM coding agents across three key dimensions:

    ### 📊 Correctness Metrics
    - **Pass@1**: Binary pass/fail for single attempt
    - **Test Pass Rate**: Percentage of individual test cases passed
    - **Pass@k**: Probability of passing with k attempts (batch evaluation)
    - **Functional Correctness**: Validation against HumanEval test suite

    ### 💭 Explainability Metrics
    - **Confidence Level**: LLM's self-assessed confidence (High/Medium/Low)
    - **Line of Thought**: Explanation of approach
    - **Test Case Generation**: Whether LLM provides test cases

    ### 🎨 Design Principles (Coming Soon)
    - Descriptive naming
    - Single responsibility
    - Small functions
    - TDD approach
    - Logging readiness
    - Edge case handling

    ---

    ## How to Use

    ### Single Task Evaluation
    1. Initialize the evaluator from the sidebar
    2. Select a task ID (0-163)
    3. Click "Run Evaluation"
    4. View metrics, solution, and test results

    ### Batch Evaluation
    1. Select start and end task IDs
    2. Click "Run Batch Evaluation"
    3. View aggregated metrics and individual results
    4. Download results as CSV

    ---

    ## Extending the Dashboard

    See `IMPLEMENTATION.md` for detailed instructions on:
    - Adding new metrics
    - Creating custom components
    - Integrating new evaluators
    - Customizing the UI

    ---

    ## Tech Stack
    - **Framework**: Streamlit
    - **LLM**: Groq API (configurable)
    - **Dataset**: HumanEval
    - **Evaluation**: Custom correctness, explainability, and design evaluators

    ---

    ## Links
    - [HumanEval Benchmark](https://github.com/openai/human-eval)
    - [Streamlit Documentation](https://docs.streamlit.io)
    """)

    st.markdown("---")

    st.info("💡 **Tip**: Use the sidebar to navigate between different views!")
