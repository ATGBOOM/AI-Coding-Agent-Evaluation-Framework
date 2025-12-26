# LLM Coding Agent Evaluation Framework

An evaluation framework for assessing LLM coding agents using the HumanEval benchmark across three key dimensions: correctness, explainability, and design adherence.

## Overview

This framework evaluates LLM-generated code solutions against:

1. **Correctness** - pass@1 metric against HumanEval test cases
2. **Explainability** - confidence levels and explanation quality
3. **Design Adherence** - compliance with 6 software design principles

## Tech Stack

- **Python 3.10+**
- **Groq API** (free tier)
- **LangChain** (optional)
- **HuggingFace Datasets** (HumanEval)
- **pandas** for data analysis
- **ast** module for code parsing

## Project Structure

```
eval-framework/
├── main.py                      # Entry point
├── config.py                    # Configuration settings
├── prompts/
│   └── evaluation_prompt.py     # Structured prompt templates
├── evaluators/
│   ├── correctness.py          # pass@1 evaluation
│   ├── explainability.py       # Confidence & explanation scoring
│   └── design.py               # Design principles checker
├── utils/
│   ├── llm_client.py           # Groq API client
│   ├── parser.py               # Code & response parsing
│   └── sandbox.py              # Safe code execution
├── data/
│   └── results.csv             # Evaluation results
└── notebooks/
    └── analysis.ipynb          # Results analysis
```

## Evaluation Dimensions

### 1. Correctness
- Executes generated code against HumanEval test cases
- Calculates pass@1 metric
- Captures execution errors and failures

### 2. Explainability
Evaluates structured response format:
- **Confidence**: High/Medium/Low
- **Approach**: Explanation of solution strategy
- **Tests**: Generated test cases
- **Solution**: Implementation

Scores based on:
- Confidence level provided
- Presence of approach explanation
- Quality of explanation
- Test cases included

### 3. Design Adherence

Checks 6 design principles:

1. **Descriptive Naming** - Clear variable/function names
2. **Single Responsibility** - Functions do one thing
3. **Small Functions** - Functions < 15 lines
4. **TDD** - Tests written
5. **Logging Ready** - No print statements
6. **Edge Cases Handled** - Input validation and error handling

## Setup

### Prerequisites

- Python 3.10 or higher
- Groq API key (free tier)

### Installation

1. Clone the repository:
```bash
cd eval-framework
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
export GROQ_API_KEY="your-api-key-here"
```

Or create a `.env` file:
```
GROQ_API_KEY=your-api-key-here
```

## Usage

### Run Evaluation

```bash
# Evaluate all HumanEval problems
python main.py

# Evaluate specific number of problems
python main.py --num-samples 10

# Specify output path
python main.py --output data/my_results.csv

# Generate report
python main.py --report
```

### Analyze Results

Open the Jupyter notebook for analysis:

```bash
jupyter notebook notebooks/analysis.ipynb
```

## Configuration

Edit `config.py` to customize:

- **Groq API settings**: model, temperature, max tokens
- **Evaluation thresholds**: pass@k, max function lines
- **Design principles**: customize or add principles
- **Sandbox settings**: timeout, memory limits, allowed imports

## Output Format

Results are saved to CSV with columns:

- `task_id` - HumanEval task identifier
- `problem_name` - Problem name
- `correctness_passed` - Pass/fail boolean
- `num_tests_passed` - Tests passed
- `num_tests_total` - Total tests
- `confidence_level` - High/Medium/Low
- `has_approach` - Explanation present
- `approach_quality` - Quality score (0-1)
- `has_tests` - Tests provided
- `explainability_score` - Overall score (0-1)
- `descriptive_naming` - Principle check
- `single_responsibility` - Principle check
- `small_functions` - Principle check
- `tdd` - Principle check
- `logging_ready` - Principle check
- `edge_cases_handled` - Principle check
- `design_score` - Overall design score (0-1)
- `overall_score` - Combined score
- `execution_time_ms` - Execution time
- `response_tokens` - Token count
- `errors` - Error messages

## Development Status

**Current Status**: Scaffolding complete, implementation pending

### TODO

- [ ] Implement LLM client with Groq API
- [ ] Implement prompt template system
- [ ] Implement response parsing
- [ ] Implement correctness evaluator
- [ ] Implement explainability evaluator
- [ ] Implement design evaluator
- [ ] Implement sandbox execution
- [ ] Implement main evaluation pipeline
- [ ] Add analysis visualizations to notebook
- [ ] Add comprehensive tests
- [ ] Add error handling and logging

## License

MIT License

## Contributing

Contributions welcome! Please open an issue or PR.
# events-app
