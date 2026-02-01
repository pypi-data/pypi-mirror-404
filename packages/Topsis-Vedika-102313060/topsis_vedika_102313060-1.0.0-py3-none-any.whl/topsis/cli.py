import sys
import pandas as pd
import numpy as np


def error(msg):
    print("Error",msg)
    sys.exit(1)
def main():
        
    if len(sys.argv) != 5:
        error("Correct usage: python topsis.py input.csv weights impacts output.csv")

    input_file=sys.argv[1]
    weights=sys.argv[2]
    impacts=sys.argv[3]
    output_file=sys.argv[4]

    try:
        data=pd.read_csv(input_file)
    except FileNotFoundError:
        error("Input file not found")


    if data.shape[1]<3:
        error("Input file must contain at least 3 columns")


    decision=data.iloc[:,1:]

    try:
        decision=decision.astype(float)
    except:
        error("From 2nd column to last must contain numeric values only")


    if "," not in weights or "," not in impacts:
        error("Weights and impacts must be comma separated")

    try:
        wgt=list(map(float, weights.split(",")))
    except:
        error("Weights must be numeric")

    imp=impacts.split(",")

    count=decision.shape[1]

    if len(wgt)!=count:
        error("Number of weights must match number of criteria columns")

    if len(imp)!=count:
        error("Number of impacts must match number of criteria columns")

    if not all(i in ['+', '-'] for i in imp):
        error("Impacts must be + or - only")


    # ---------------- TOPSIS CALCULATION ----------------

    norm=decision/np.sqrt((decision**2).sum())

    weighted=norm*wgt

    best = []
    worst = []

    for i in range(count):
        if imp[i] =='+':
            best.append(weighted.iloc[:, i].max())
            worst.append(weighted.iloc[:, i].min())
        else:
            best.append(weighted.iloc[:, i].min())
            worst.append(weighted.iloc[:, i].max())

    best=np.array(best)
    worst=np.array(worst)

    d_best=np.sqrt(((weighted - best) ** 2).sum(axis=1))
    d_worst=np.sqrt(((weighted - worst) ** 2).sum(axis=1))

    score=d_worst/(d_best + d_worst)

    data["Topsis Score"]=score
    data["Rank"]=score.rank(ascending=False)

    data.to_csv(output_file, index=False)

    print("Success ", output_file)

if __name__ == "__main__":
    main()    
