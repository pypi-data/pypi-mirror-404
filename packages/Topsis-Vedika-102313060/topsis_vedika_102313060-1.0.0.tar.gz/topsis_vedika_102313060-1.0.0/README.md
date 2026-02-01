# Topsis-Vedika-102313060

A Python command-line tool that implements the TOPSIS (Technique for Order Preference by Similarity to Ideal Solution) method to rank alternatives using multiple criteria.

The program reads a CSV file, applies TOPSIS using given weights and impacts, and generates a ranked output CSV file.

---
## Installation

Install using pip:

pip install Topsis-Vedika-102313060

---
## Usage
Enter csv filename followed by .csv extentsion, then enter the weights vector with vector values separated by commas, followed by the impacts vector with comma separated signs (+,-)

topsis <input.csv> <weights> <impacts> <output.csv>

---
## Example

A CSV file containing fund performance data with multiple criteria.

Example format:

| Fund Name | P1 | P2 | P3 | P4 | P5 |
|------------|------|------|------|------|------|
| M1 | 0.9 | 0.81 | 3 | 36 | 10.18 |
| M2 | 0.82 | 0.67 | 4.3 | 50.1 | 13.97 |
| M3 | 0.79 | 0.62 | 5.3 | 38.7 | 11.35 |
| M4 | 0.87 | 0.76 | 5.8 | 47.5 | 13.73 |
| M5 | 0.72 | 0.52 | 5.8 | 40.2 | 11.81 |
| M6 | 0.95 | 0.90 | 4.4 | 60.3 | 16.64 |
| M7 | 0.82 | 0.67 | 4.8 | 48.7 | 13.75 |
| M8 | 0.62 | 0.38 | 5.4 | 40.2 | 11.65 |

weights vector:[1,1,1,1,1]
impacts vector:[+,+,+,+,+]

input command:
topsis data.csv "1,1,1,1,1" "+,+,+,+,+" result.csv

## Output

The generated result.csv file will include:

- Topsis Score
- Rank

Each fund will be ranked based on TOPSIS score.
Higher score indicates better rank.
