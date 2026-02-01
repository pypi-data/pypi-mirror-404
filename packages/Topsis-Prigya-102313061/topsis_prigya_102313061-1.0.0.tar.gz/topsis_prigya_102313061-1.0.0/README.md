# TOPSIS Python Package

This project implements the **TOPSIS (Technique for Order Preference by Similarity to Ideal Solution)** method as a command line tool.

TOPSIS is a multi-criteria decision making technique used to rank alternatives based on their distance from an ideal best and ideal worst solution.

---

## Installation

```bash
pip install Topsis-Prigya-102313061
```

---

## Input File Format

The input must be a CSV file with:

- First column: Names of alternatives
- Remaining columns: Numeric criteria values

### Example Input CSV

```text
Fund Name,Return,Risk,Expense Ratio,Assets
Fund A,12.5,8.2,0.45,150
Fund B,10.2,6.5,0.30,200
Fund C,14.1,9.1,0.55,180
Fund D,9.8,5.9,0.25,220
```

### Meaning of Criteria

- Return → Higher is better (+)
- Risk → Lower is better (-)
- Expense Ratio → Lower is better (-)
- Assets → Higher is better (+)

---

## Command Line Usage

```bash
topsis data.csv "1,1,1,1" "+,-,-,+" output.csv
```

---

## Output

The output CSV file will contain two additional columns:

- **Topsis Score**
- **Rank**

---

## Requirements

- Python 3.6+
- pandas
- numpy

---

## Author

Prigya Goyal
