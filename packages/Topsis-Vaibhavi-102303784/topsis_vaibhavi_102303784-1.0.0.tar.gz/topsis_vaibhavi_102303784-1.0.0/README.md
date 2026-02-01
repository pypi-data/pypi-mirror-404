# TOPSIS-YourName-RollNumber

**TOPSIS (Technique for Order Preference by Similarity to Ideal Solution)** - A Python package for multi-criteria decision analysis.

## 📋 Description

TOPSIS is a multi-criteria decision-making method that helps rank alternatives based on their similarity to the ideal solution. This package provides an easy-to-use implementation of the TOPSIS algorithm with comprehensive error handling and validation.

## 🎯 Features

- ✅ Complete TOPSIS algorithm implementation
- ✅ Command-line interface
- ✅ Comprehensive input validation
- ✅ Detailed error messages
- ✅ CSV input/output support
- ✅ Easy to use and integrate

## 📦 Installation

### From PyPI

```bash
pip install Topsis-YourName-RollNumber
```

### From Source

```bash
git clone https://github.com/yourusername/Topsis-YourName-RollNumber.git
cd Topsis-YourName-RollNumber
pip install -e .
```

## 🚀 Usage

### Command Line

```bash
python -m Topsis-YourName-RollNumber <InputFile> <Weights> <Impacts> <OutputFile>
```

### Example

```bash
python -m Topsis-YourName-RollNumber data.xlsx "1,1,1,2" "+,+,-,+" output.xlsx
```

### As a Python Module

```python
from Topsis_YourName_RollNumber import topsis_analysis

# Perform TOPSIS analysis
result_df = topsis_analysis(
    input_file='data.xlsx',
    weights='1,1,1,2',
    impacts='+,+,-,+',
    output_file='output.xlsx'
)

print(result_df)
```

## 📊 Input Format

### Excel File Requirements (.xlsx)

1. **Minimum 3 columns**: First column for alternatives (names), remaining columns for numeric criteria
2. **First column**: Alternative names (non-numeric)
3. **Remaining columns**: Numeric values only

### Example Input File (data.xlsx)

| Fund Name | P1   | P2   | P3  | P4   | P5    |
|-----------|------|------|-----|------|-------|
| M1        | 0.84 | 0.71 | 6.7 | 42.1 | 12.59 |
| M2        | 0.91 | 0.83 | 7.0 | 31.7 | 10.11 |
| M3        | 0.79 | 0.62 | 4.8 | 46.7 | 13.23 |
| M4        | 0.78 | 0.61 | 6.4 | 42.4 | 12.55 |
| M5        | 0.94 | 0.88 | 3.6 | 62.2 | 16.91 |

### Parameters

- **Weights**: Comma-separated numeric values (e.g., `"1,1,1,2"`)
- **Impacts**: Comma-separated `+` or `-` signs (e.g., `"+,+,-,+"`)
  - `+` : Benefit criterion (higher is better)
  - `-` : Cost criterion (lower is better)

## 📤 Output Format

The output Excel file contains all input columns plus:
- **Topsis Score**: Performance score (0-1, higher is better)
- **Rank**: Ranking (1 = best alternative)

### Example Output

| Fund Name | P1   | P2   | P3  | P4   | P5    | Topsis Score | Rank |
|-----------|------|------|-----|------|-------|--------------|------|
| M5        | 0.94 | 0.88 | 3.6 | 62.2 | 16.91 | 0.6890       | 1    |
| M8        | 0.93 | 0.87 | 5.5 | 53.3 | 15.07 | 0.6123       | 2    |
| ...       | ...  | ...  | ... | ...  | ...   | ...          | ...  |

## ⚠️ Error Handling

The package validates:
- ✅ Correct number of arguments
- ✅ File existence
- ✅ Excel format (.xlsx)
- ✅ Minimum 3 columns
- ✅ Numeric values in criteria columns
- ✅ Matching number of weights and criteria
- ✅ Matching number of impacts and criteria
- ✅ Valid impact signs (+ or -)
- ✅ Proper comma separation

## 🧮 TOPSIS Algorithm Steps

1. **Normalize** the decision matrix
2. **Apply weights** to normalized matrix
3. **Identify** ideal best and ideal worst solutions
4. **Calculate** Euclidean distances from ideal solutions
5. **Compute** TOPSIS score
6. **Rank** alternatives

## 📚 Mathematical Formula

**TOPSIS Score:**

$$P_i = \frac{S_i^-}{S_i^+ + S_i^-}$$

Where:
- $S_i^+$ = Distance from ideal best
- $S_i^-$ = Distance from ideal worst

## 🛠️ Requirements

- Python >= 3.7
- pandas >= 1.0.0
- numpy >= 1.18.0
- openpyxl >= 3.0.0

## 📄 License

MIT License

## 👤 Author

**Your Name**
- Roll Number: Your Roll Number
- Email: your.email@example.com
- GitHub: [@yourusername](https://github.com/yourusername)

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!

## 📝 Changelog

### Version 1.0.0 (Initial Release)
- Complete TOPSIS implementation
- CLI interface
- Comprehensive validation
- PyPI package

---

Made with ❤️ for Multi-Criteria Decision Making
