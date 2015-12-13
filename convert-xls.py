import glob

import pandas as pd

files = glob.glob('data/*/*.xls')

for fname in files:
    with open(fname, 'r') as fh:
        data = fh.read()
        fname_csv = fname.replace('xls', 'csv')
        print(fname, '->', fname_csv)
        pd.read_html(data)[0].to_csv(fname_csv, index=False, header=False)
