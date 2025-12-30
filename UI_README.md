# Evaluation Dashboard UI

A Streamlit-based interactive dashboard for evaluating LLM coding agents.

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

The key UI dependencies are:
- `streamlit>=1.28.0` - Web framework
- `plotly>=5.17.0` - Interactive visualizations
- `pandas>=2.0.0` - Data handling

### 2. Configure Environment

Ensure your `.env` file has the required API keys:

```env
GROQ_API_KEY=your_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_TEMPERATURE=0.1
GROQ_MAX_TOKENS=2048
```

### 3. Run the Dashboard

```bash
streamlit run app.py
```

The dashboard will open automatically at `http://localhost:8501`

## Features

### 📝 Single Task Evaluation
- Select any task from HumanEval (0-163)
- Run evaluation and view real-time results
- View metrics, solution code, test cases, and comparisons

### 📊 Batch Evaluation
- Evaluate multiple tasks in one run
- View aggregated metrics (pass@k, overall pass rate, etc.)
- Download results as CSV
- Filter and analyze individual task results

### 📈 Metrics Displayed

#### Correctness
- **Pass@1**: Binary pass/fail for single attempt
- **Test Pass Rate**: Percentage of tests passed
- **Tests Passed**: Count of passed/total tests
- **Status**: Overall pass/fail indicator

#### Explainability
- **Confidence Level**: LLM's self-assessment
- **Line of Thought**: Explanation of approach
- **Has Test Cases**: Whether LLM generated tests

#### Batch Metrics
- **Overall Pass Rate**: Across all tasks
- **Pass@k**: For k=[1, 5, 10]
- **Average Test Pass Rate**: Mean across tasks

## UI Structure

```
ui/
├── __init__.py          # Package initialization
├── config.py            # Metric definitions (add new metrics here)
├── components.py        # Reusable UI components (add new components here)

app.py                   # Main Streamlit app (add new pages here)
IMPLEMENTATION.md        # Detailed guide for extending the UI
```

## Navigation

### Sidebar
- **⚙️ Configuration**: Initialize the evaluator
- **📍 Navigation**: Switch between views
- **📊 Status**: Current evaluator and task status

### Main Pages
1. **Single Task Evaluation**: Evaluate individual tasks
2. **Batch Evaluation**: Run multiple tasks and view aggregated metrics
3. **About**: Documentation and help

## Extending the Dashboard

See [IMPLEMENTATION.md](IMPLEMENTATION.md) for detailed instructions on:

### Adding New Metrics

```python
# In ui/config.py
MetricConfig(
    key="my_metric",
    label="My Metric",
    category=MetricCategory.CORRECTNESS,
    metric_type=MetricType.PERCENTAGE,
    description="Description of my metric",
    icon="🎯",
    extractor=lambda result: result.get('my_metric')
)
```

### Creating Custom Components

```python
# In ui/components.py
def render_my_component(result: Dict[str, Any]):
    """Render my custom component."""
    st.subheader("My Component")
    st.write(result.get('my_data'))
```

### Adding New Evaluators

1. Create evaluator in `evaluators/`
2. Integrate with `EvaluationRunner`
3. Add metrics to `ui/config.py`
4. Create component in `ui/components.py`
5. Add to dashboard in `app.py`

See [IMPLEMENTATION.md](IMPLEMENTATION.md) for complete examples.

## Tips

### Performance
- Use batch evaluation for analyzing multiple tasks
- Results are cached in session state
- Clear results if memory becomes an issue

### Debugging
- Check browser console for errors
- Check terminal for Streamlit logs
- Use `st.write()` to debug data structures

### Customization
- Modify `ui/config.py` to change metric displays
- Edit `ui/components.py` to customize layouts
- Create `.streamlit/config.toml` for custom themes

## Common Operations

### Run Single Evaluation
1. Click "🚀 Initialize Evaluator" in sidebar
2. Select task ID (0-163)
3. Click "▶️ Run Evaluation"
4. View results in tabs

### Run Batch Evaluation
1. Navigate to "Batch Evaluation"
2. Set start and end task IDs
3. Click "▶️ Run Batch Evaluation"
4. View aggregated metrics and table
5. Download CSV if needed

### Compare Tasks
1. Run single evaluation for Task A
2. Note the results
3. Run evaluation for Task B
4. Compare manually

*Tip: Future enhancement could add a comparison view*

## Troubleshooting

### Evaluator Won't Initialize
- Check `.env` file has valid API key
- Ensure dependencies are installed
- Check terminal for error messages

### Evaluation Fails
- Verify task ID is valid (0-163)
- Check API rate limits
- Review error message in UI

### UI Not Updating
- Click "Rerun" in top-right corner
- Clear browser cache
- Restart Streamlit server

### Charts Not Displaying
- Ensure plotly is installed: `pip install plotly`
- Check browser console for errors
- Try different browser

## Architecture

### Data Flow

```
User Input → EvaluationRunner → LLM API
                ↓
          Generate Solution
                ↓
          Run Evaluators (Correctness, Explainability, etc.)
                ↓
          Format Results
                ↓
          UI Components → Streamlit Display
```

### Session State

The app uses `st.session_state` to persist:
- `runner`: EvaluationRunner instance
- `current_result`: Latest single evaluation result
- `batch_results`: List of batch evaluation results
- `aggregated_metrics`: Batch aggregated metrics
- `task_id`: Current task ID

### Component Hierarchy

```
app.py (Main App)
  ├── Sidebar (Navigation & Config)
  ├── Single Task Page
  │   ├── Task Selector Component
  │   ├── Metrics Tab
  │   │   ├── Correctness Section
  │   │   ├── LLM Test Correctness Section
  │   │   └── Explainability Section
  │   ├── Solution Tab
  │   ├── Tests Tab
  │   └── Comparison Tab
  └── Batch Evaluation Page
      ├── Batch Controls
      ├── Aggregated Metrics Component
      └── Results Table Component
```

## Best Practices

1. **Always initialize evaluator** before running evaluations
2. **Use batch evaluation** for analyzing multiple tasks efficiently
3. **Download results** before clearing session state
4. **Check error messages** in expandable sections
5. **Review IMPLEMENTATION.md** before making changes

## Examples

### Example 1: Quick Single Task Evaluation

```python
# In Python console or notebook
from evaluation_runner import EvaluationRunner

runner = EvaluationRunner()
result = runner.generate_solution(task_id=0)
print(result['correctness_result'])
```

### Example 2: Batch Evaluation Script

```python
runner = EvaluationRunner()
results = runner.run_batch_evaluation(start_id=0, end_id=10)

# Results include aggregated metrics printed to console
```

## Deployment

### Local Development
```bash
streamlit run app.py
```

### Production (Streamlit Cloud)
1. Push code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Deploy your repository
4. Add secrets for API keys

### Docker
```bash
docker build -t eval-dashboard .
docker run -p 8501:8501 eval-dashboard
```

## Support

- 📖 **Full Documentation**: See [IMPLEMENTATION.md](IMPLEMENTATION.md)
- 🐛 **Issues**: Report bugs in the repository
- 💡 **Feature Requests**: Open an issue with your idea
- 📚 **Streamlit Docs**: [docs.streamlit.io](https://docs.streamlit.io)

## License

Same as parent project.

---

**Built with ❤️ using Streamlit**
