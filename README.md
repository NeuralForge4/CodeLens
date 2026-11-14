# CodeLens — AI Code Bug Detection \& Code Quality Analyzer

CodeLens is a Flask-based web application that analyzes Python source code to identify potential bugs, coding issues, and code-quality problems.

It combines traditional static analysis techniques with a lightweight machine-learning classifier.

## 1\. Features

* **Python syntax checking:** Identifies syntax errors using Python's AST parser.
* **AST-based analysis:** Detects selected risky patterns, including bare `except` blocks, `eval()` and `exec()` usage, unused imports, and functions with too many parameters.
* **Ruff linting:** Identifies Python coding-style issues and common programming mistakes.
* **Radon complexity analysis:** Measures cyclomatic complexity.
* **ML-based defect scoring:** Uses TF-IDF character n-gram features and Logistic Regression to classify code as potentially defective or non-defective.
* **Code upload:** Upload Python `.py` files or paste code directly into the editor.
* **Analyze New Code:** Clears the editor and previous analysis results.
* **Copy Result:** Copies the analysis report.
* **Download Report:** Downloads the analysis as a `.txt` file.

**Important:** Uploaded or pasted Python code is analyzed as text. The application does not execute the submitted code. The heuristic risk indicator is rule-based, and the ML defect score is a classifier score, not a calibrated probability.

## 2\. Technologies Used

|Component|Technology|
|-|-|
|Backend|Python, Flask|
|Frontend|HTML, CSS, JavaScript|
|Syntax and structure analysis|Python AST|
|Linting|Ruff|
|Complexity analysis|Radon|
|Machine learning|Scikit-learn|
|Feature extraction|TF-IDF|
|Classification algorithm|Logistic Regression|
|Model storage|Joblib|

## 3\. Requirements

* Python 3.10 or newer, subject to dependency compatibility.
* pip package manager.
* Internet connection for installing dependencies.

## 4\. Create a Virtual Environment

### Windows PowerShell

```powershell
python -m venv .venv
.venv\\Scripts\\Activate.ps1
```

### macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 5\. Install Dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If a dependency is missing, install it in the activated virtual environment.

## 6\. Prepare the Training Dataset

The ML classifier requires a labeled CSV dataset.

Create the file:

`dataset/training\_data.csv`

The CSV must contain two columns:

```csv
code,label
"def add(a, b): return a + b",0
"def divide(a, b): return a / 0",1
```

Labels:

* `0` = Non-defective code
* `1` = Defective code

The examples above demonstrate the CSV format only. They are not sufficient to train a reliable classifier.

Use a larger, reviewed dataset with meaningful labels for better evaluation.

## 7\. Train the ML Classifier

Run the following command from the project directory:

```powershell
python train\_model.py --csv dataset/training\_data.csv
```

The training script:

1. Reads the labeled CSV dataset.
2. Extracts character n-gram features using TF-IDF.
3. Trains a Logistic Regression classifier.
4. Evaluates the model using a test split.
5. Displays classification metrics.
6. Saves the trained model.

The trained model is saved at:

`artifacts/defect\_classifier.joblib`

**Note:** A small dataset may produce unreliable evaluation results. The initial 10-example dataset is only useful for testing whether the training pipeline works. Do not present its metrics as evidence of reliable defect detection.

The classifier learns patterns from labeled examples. It does not understand code in the same way as a large language model.

## 8\. Run the Application

Start the Flask application:

```powershell
python app.py
```

Open this address in your browser:

http://127.0.0.1:5000

You can now:

1. Paste Python code into the editor or upload a `.py` file.
2. Click **Analyze Code**.
3. Review the analysis results.
4. Copy the report using **Copy Result**.
5. Download a text report using **Download Report**.
6. Click **Analyze New Code** to start another analysis.

The static-analysis features work independently of the trained ML classifier. If no model is available, the ML defect score may be unavailable.

## 9\. How the Analyzer Works

CodeLens uses two main analysis approaches.

### A. Static Analysis

* Python AST checks inspect code structure and selected risky patterns.
* Ruff identifies linting issues.
* Radon measures cyclomatic complexity.
* A rule-based heuristic calculates a risk indicator from selected findings.

### B. Machine Learning

The ML component uses:

* **TF-IDF:** Converts source-code character n-grams into numerical features.
* **Logistic Regression:** Learns to classify code samples using labeled training data.

The model returns a defect-class score. This score is not a calibrated probability and should not be treated as a guarantee that code contains a bug.

## 10\. Project Structure

```text
ai\_code\_quality\_analyzer/
│
├── app.py
├── analyzer.py
├── train\_model.py
├── requirements.txt
├── README.md
│
├── dataset/
│   └── training\_data.csv
│
├── artifacts/
│   └── defect\_classifier.joblib
│
├── templates/
│   └── index.html
│
└── static/
    ├── style.css
    └── app.js
```

The `artifacts` directory and trained model are created after successful model training.

## 11\. Suggested Demonstration Cases

Try analyzing these examples during your project demonstration:

1. A clean Python function.
2. Code containing an unused import.
3. A bare `except:` block.
4. Code using `eval()` or `exec()`.
5. A function with many branches.
6. Code containing a syntax error.
7. Code with a potential division-by-zero issue.

## 12\. Limitations

* The analyzer currently focuses on Python source code.
* Static analysis cannot detect every possible bug.
* The ML classifier depends on the quality and size of its training dataset.
* A small or unbalanced dataset can lead to poor classification performance.
* The ML score is not a calibrated probability.
* The application does not execute submitted source code.
* Findings should be reviewed by a developer before making code changes.

## 13\. Future Improvements

* Train and evaluate the classifier using a larger labeled defect-detection dataset.
* Add more AST-based checks.
* Support additional programming languages.
* Improve the user interface and report formatting.
* Add user accounts and analysis history.
* Evaluate model performance using larger independent test datasets.

## 14\. Team Contributions

For a team of two or three members, responsibilities can be divided as follows:

* **Member 1:** Dataset preparation, ML model training, and evaluation.
* **Member 2:** Python AST analysis, Ruff, Radon, and Flask backend.
* **Member 3:** Frontend development, integration testing, documentation, and presentation.

\---

**Project Name:** CodeLens — AI Code Bug Detection \& Code Quality Analyzer

**Project Type:** College Mini Project

**Technology:** Python, Flask, JavaScript, Static Analysis, Machine Learning

