# Implementation Guide: Extending the Evaluation Dashboard

This guide explains how to extend and customize the evaluation dashboard UI layer.

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Adding New Metrics](#adding-new-metrics)
3. [Creating Custom Components](#creating-custom-components)
4. [Integrating New Evaluators](#integrating-new-evaluators)
5. [Customizing the UI](#customizing-the-ui)
6. [Best Practices](#best-practices)

---

## Architecture Overview

The UI layer is structured for modularity and extensibility:

```
ui/
├── __init__.py          # Package initialization
├── config.py            # Metric definitions and configurations
├── components.py        # Reusable UI components
app.py                   # Main Streamlit application
```

### Design Principles

1. **Configuration-Driven**: Metrics are defined in `config.py`, making it easy to add new ones
2. **Component-Based**: Reusable components in `components.py` can be mixed and matched
3. **Separation of Concerns**: UI logic is separate from evaluation logic
4. **Type-Safe**: Uses dataclasses and type hints throughout

---

## Adding New Metrics

### Step 1: Define Metric Configuration

Add your metric to `ui/config.py`:

```python
from ui.config import MetricConfig, MetricCategory, MetricType

# Example: Adding a new design metric
DESIGN_METRICS: List[MetricConfig] = [
    MetricConfig(
        key="has_descriptive_naming",
        label="Descriptive Naming",
        category=MetricCategory.DESIGN,
        metric_type=MetricType.BINARY,
        description="Whether code uses descriptive variable/function names",
        icon="✏️",
        extractor=lambda result: result.get('design_result').has_descriptive_naming if result.get('design_result') else None
    ),
]
```

### Step 2: Update the Metric List

Add your new metric list to the appropriate location:

```python
# In config.py
def get_all_metrics() -> List[MetricConfig]:
    """Get all available metrics."""
    return CORRECTNESS_METRICS + EXPLAINABILITY_METRICS + DESIGN_METRICS
```

### Step 3: Add to UI Display

In `app.py` or create a new component in `components.py`:

```python
def render_design_section(result: Dict[str, Any]):
    """Render design metrics section."""
    st.subheader("🎨 Design Adherence")
    render_metrics_grid(result, DESIGN_METRICS, columns=3)
```

Then add to your page:

```python
# In app.py, within the metrics tab
with tab_design:
    render_design_section(result)
```

### Metric Configuration Options

```python
@dataclass
class MetricConfig:
    key: str                    # Key to access the metric value
    label: str                  # Display label in UI
    category: MetricCategory    # Category for organization
    metric_type: MetricType     # How to format (percentage, binary, etc.)
    description: str            # Tooltip help text
    precision: int = 2          # Decimal places for numbers
    icon: Optional[str] = None  # Emoji/icon to display
    extractor: Optional[Callable[[Any], Any]] = None  # Custom extraction function
```

### Supported Metric Types

```python
class MetricType(Enum):
    PERCENTAGE = "percentage"   # Displays as "75.5%"
    BINARY = "binary"          # Displays as "✅ PASS" or "❌ FAIL"
    COUNT = "count"            # Displays as integer "42"
    DECIMAL = "decimal"        # Displays as "3.14"
    TEXT = "text"              # Displays as-is "High"
```

---

## Creating Custom Components

### Component Structure

Components are functions that render UI elements. Follow this pattern:

```python
def render_my_component(result: Dict[str, Any], **kwargs):
    """
    Brief description of what this component renders.

    Args:
        result: Evaluation result dictionary
        **kwargs: Additional configuration options

    Returns:
        None (renders to Streamlit)
    """
    st.subheader("My Component Title")

    # Extract data
    data = result.get('my_data')

    if not data:
        st.warning("No data available")
        return

    # Render content
    st.write(data)
```

### Example: Creating a Complexity Analysis Component

```python
# In ui/components.py

def render_complexity_analysis(result: Dict[str, Any]):
    """
    Render code complexity analysis.

    Args:
        result: Evaluation result dictionary
    """
    st.subheader("🔬 Complexity Analysis")

    complexity_result = result.get('complexity_result')

    if not complexity_result:
        st.info("No complexity analysis available")
        return

    # Metrics
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Cyclomatic Complexity",
            complexity_result.cyclomatic,
            help="Number of linearly independent paths"
        )

    with col2:
        st.metric(
            "Lines of Code",
            complexity_result.loc,
            help="Total lines of code"
        )

    with col3:
        st.metric(
            "Maintainability Index",
            f"{complexity_result.maintainability:.1f}",
            help="Maintainability score (0-100)"
        )

    # Visualization
    if complexity_result.function_complexities:
        st.markdown("**Per-Function Complexity:**")

        import pandas as pd
        import plotly.express as px

        df = pd.DataFrame(complexity_result.function_complexities)
        fig = px.bar(df, x='function', y='complexity', title='Function Complexity')
        st.plotly_chart(fig, use_container_width=True)
```

### Using the Component

```python
# In app.py
with tab_complexity:
    render_complexity_analysis(result)
```

---

## Integrating New Evaluators

### Step 1: Create the Evaluator

Create your evaluator in `evaluators/my_evaluator.py`:

```python
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class MyEvaluatorResult:
    """Result from my evaluator."""
    score: float
    passed: bool
    details: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            'score': self.score,
            'passed': self.passed,
            'details': self.details
        }

class MyEvaluator:
    """Evaluates my custom metric."""

    def evaluate(self, solution_code: str) -> MyEvaluatorResult:
        """Run evaluation."""
        # Your evaluation logic here
        return MyEvaluatorResult(score=0.8, passed=True, details="Good!")
```

### Step 2: Integrate with EvaluationRunner

Update `evaluation_runner.py`:

```python
from evaluators.my_evaluator import MyEvaluator, MyEvaluatorResult

class EvaluationRunner:
    def __init__(self, ...):
        # ... existing code ...
        self.my_evaluator = MyEvaluator()

    def generate_solution(self, task_id: int) -> Dict:
        # ... existing code ...

        # Run your evaluator
        my_result = self.my_evaluator.evaluate(response.solution)

        return {
            # ... existing fields ...
            'my_evaluator_result': my_result
        }
```

### Step 3: Add UI Configuration

Add metrics in `ui/config.py`:

```python
MY_EVALUATOR_METRICS: List[MetricConfig] = [
    MetricConfig(
        key="score",
        label="My Score",
        category=MetricCategory.DESIGN,  # or create new category
        metric_type=MetricType.DECIMAL,
        description="My custom score",
        icon="🎯",
        extractor=lambda result: result.get('my_evaluator_result').score if result.get('my_evaluator_result') else None
    ),
]
```

### Step 4: Create UI Component

In `ui/components.py`:

```python
def render_my_evaluator_section(result: Dict[str, Any]):
    """Render my evaluator results."""
    st.subheader("🎯 My Evaluator")

    my_result = result.get('my_evaluator_result')

    if not my_result:
        st.warning("No evaluation available")
        return

    render_metrics_grid(result, MY_EVALUATOR_METRICS, columns=3)

    # Additional details
    st.write(my_result.details)
```

### Step 5: Add to Dashboard

In `app.py`:

```python
# Add new tab
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Metrics",
    "💻 Solution",
    "🧪 Tests",
    "📖 Comparison",
    "🎯 My Evaluator"  # New tab
])

with tab5:
    render_my_evaluator_section(result)
```

---

## Customizing the UI

### Adding a New Page

```python
# In app.py, update the navigation
page = st.radio(
    "Select View",
    ["Single Task Evaluation", "Batch Evaluation", "My Custom Page", "About"]
)

# Add page logic
elif page == "My Custom Page":
    st.header("🎨 My Custom Page")

    # Your custom page content here
    st.write("This is my custom page!")
```

### Custom Visualizations

Use Plotly for interactive charts:

```python
import plotly.graph_objects as go

def render_custom_chart(data):
    """Render a custom visualization."""
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=data['x'],
        y=data['y'],
        mode='lines+markers',
        name='My Data'
    ))

    fig.update_layout(
        title='My Custom Chart',
        xaxis_title='X Axis',
        yaxis_title='Y Axis'
    )

    st.plotly_chart(fig, use_container_width=True)
```

### Custom Styling

Create `.streamlit/config.toml` for custom theme:

```toml
[theme]
primaryColor = "#F63366"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"
```

---

## Best Practices

### 1. Component Design

- **Single Responsibility**: Each component should do one thing well
- **Error Handling**: Always check if data exists before rendering
- **Null Safety**: Handle missing/None values gracefully
- **Help Text**: Provide descriptions for metrics

```python
# Good
def render_metric_section(result: Dict[str, Any]):
    data = result.get('data')

    if not data:
        st.warning("No data available")
        return

    st.metric("My Metric", data, help="Description of metric")

# Bad
def render_metric_section(result):
    st.metric("My Metric", result['data'])  # Can crash!
```

### 2. Performance

- **Cache Data**: Use `@st.cache_data` for expensive operations
- **Lazy Loading**: Only compute what's visible
- **Batch Operations**: Group database/API calls

```python
@st.cache_data
def load_expensive_data(task_id: int):
    """Load data with caching."""
    # Expensive operation
    return data
```

### 3. State Management

- Use `st.session_state` for persistent data
- Clear state when appropriate
- Don't store large objects unnecessarily

```python
# Initialize state
if 'results' not in st.session_state:
    st.session_state.results = []

# Clear state
if st.button("Clear Results"):
    st.session_state.results = []
    st.rerun()
```

### 4. User Experience

- **Feedback**: Show progress bars for long operations
- **Validation**: Validate user input before processing
- **Error Messages**: Provide clear, actionable error messages
- **Defaults**: Set sensible default values

```python
# Good UX
with st.spinner("Processing..."):
    result = expensive_operation()

if result:
    st.success("✅ Operation successful!")
else:
    st.error("❌ Operation failed. Please check your input.")
```

### 5. Code Organization

```python
# Organize imports
import streamlit as st  # Framework
import pandas as pd  # Data
import plotly.express as px  # Visualization

from evaluation_runner import EvaluationRunner  # Application
from ui.components import render_metrics_grid  # UI

# Group related functionality
def render_metrics_tab(result):
    """Render all metrics in one tab."""
    render_correctness_section(result)
    st.markdown("---")
    render_explainability_section(result)
```

---

## Common Patterns

### Pattern 1: Expandable Sections

```python
with st.expander("🔍 Advanced Details", expanded=False):
    st.write("Detailed information here")
```

### Pattern 2: Side-by-Side Comparison

```python
col1, col2 = st.columns(2)

with col1:
    st.write("Option A")

with col2:
    st.write("Option B")
```

### Pattern 3: Conditional Display

```python
if result.get('has_advanced_features'):
    render_advanced_features(result)
else:
    st.info("Advanced features not available")
```

### Pattern 4: Interactive Filters

```python
# Filter options
filter_value = st.selectbox("Filter by", options)

# Apply filter
filtered_data = [d for d in data if d.matches(filter_value)]

# Display
st.dataframe(filtered_data)
```

### Pattern 5: Download Results

```python
import json

result_json = json.dumps(result, indent=2)

st.download_button(
    label="📥 Download JSON",
    data=result_json,
    file_name="result.json",
    mime="application/json"
)
```

---

## Testing Your Changes

### Manual Testing Checklist

- [ ] Single task evaluation works
- [ ] Batch evaluation works
- [ ] All metrics display correctly
- [ ] Error states are handled
- [ ] Navigation works smoothly
- [ ] Download buttons work
- [ ] Charts render properly

### Running the Dashboard

```bash
# Install dependencies
pip install streamlit plotly pandas

# Run the app
streamlit run app.py

# The app will open at http://localhost:8501
```

---

## Deployment

### Local Development

```bash
streamlit run app.py
```

### Streamlit Cloud (Free)

1. Push code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repository
4. Deploy!

### Docker

```dockerfile
FROM python:3.9

WORKDIR /app
COPY . /app

RUN pip install -r requirements.txt

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

---

## Additional Resources

- [Streamlit Documentation](https://docs.streamlit.io)
- [Plotly Documentation](https://plotly.com/python/)
- [Streamlit Components Gallery](https://streamlit.io/components)
- [Streamlit Forums](https://discuss.streamlit.io)

---

## Getting Help

If you encounter issues:

1. Check the console for error messages
2. Review the evaluation logs
3. Test components in isolation
4. Check the Streamlit documentation
5. Create an issue in the repository

---

## Example: Complete Feature Addition

Here's a complete example of adding a "Code Complexity" feature:

### 1. Create Evaluator

```python
# evaluators/complexity.py
from dataclasses import dataclass

@dataclass
class ComplexityResult:
    cyclomatic: int
    loc: int
    maintainability: float

    def to_dict(self):
        return {
            'cyclomatic': self.cyclomatic,
            'loc': self.loc,
            'maintainability': self.maintainability
        }

class ComplexityEvaluator:
    def evaluate(self, code: str) -> ComplexityResult:
        # Analysis logic here
        return ComplexityResult(cyclomatic=5, loc=50, maintainability=75.0)
```

### 2. Add Metrics

```python
# ui/config.py
COMPLEXITY_METRICS: List[MetricConfig] = [
    MetricConfig(
        key="cyclomatic",
        label="Cyclomatic Complexity",
        category=MetricCategory.DESIGN,
        metric_type=MetricType.COUNT,
        description="Cyclomatic complexity score",
        icon="🔢",
        extractor=lambda r: r.get('complexity_result').cyclomatic if r.get('complexity_result') else None
    ),
]
```

### 3. Create Component

```python
# ui/components.py
def render_complexity_section(result: Dict[str, Any]):
    st.subheader("🔬 Code Complexity")
    render_metrics_grid(result, COMPLEXITY_METRICS, columns=3)
```

### 4. Integrate

```python
# evaluation_runner.py
from evaluators.complexity import ComplexityEvaluator

# In __init__:
self.complexity_evaluator = ComplexityEvaluator()

# In generate_solution:
complexity_result = self.complexity_evaluator.evaluate(response.solution)
return {
    # ... existing fields ...
    'complexity_result': complexity_result
}
```

### 5. Add to UI

```python
# app.py
with tab_metrics:
    render_complexity_section(result)
```

Done! You've added a complete new feature to the dashboard.

---

**Happy coding! 🚀**
