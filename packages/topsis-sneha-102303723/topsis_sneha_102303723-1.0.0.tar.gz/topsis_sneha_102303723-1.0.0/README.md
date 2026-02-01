# Topsis-Sneha-102303723

This Python package implements the TOPSIS (Technique for Order Preference by Similarity to Ideal Solution) method, a multi-criteria decision-making technique used to rank alternatives based on their distance from an ideal best and ideal worst solution.

---

## Installation

Install the package from PyPI using pip:

pip install Topsis-Sneha-102303723

---

## Usage

The package provides a command-line interface (CLI).

### Command format

topsis <input_file> <weights> <impacts> <output_file>

### Example

topsis data.csv "2,1,3,1,2" "+,-,+,+,-" result.csv

---

## Input File Format

- The input file must be a CSV file.
- The file must contain at least 3 columns.
- The first column is treated as an identifier (name/label).
- All columns from the second column to the last column must contain numeric values only.

---

## Weights and Impacts

- Weights must be numeric and separated by commas.
- Impacts must be either + (benefit) or - (cost) and separated by commas.
- The number of weights and impacts must be equal to the number of criteria columns.

---

## Output

- The output is a CSV file.
- Two additional columns are added:
  - Topsis Score
  - Rank
- Higher Topsis score indicates a better rank.

---

## Error Handling

The program validates:
- Correct number of command-line arguments
- File existence
- Numeric values in criteria columns
- Correct number of weights and impacts
- Valid impact symbols (+ or -)

---

## Author

Sneha
