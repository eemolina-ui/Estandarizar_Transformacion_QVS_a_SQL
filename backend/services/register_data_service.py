import pandas as pd
import os

def register_contact_data(csv_file_path, data):
    if not os.path.exists(csv_file_path):
        df = pd.DataFrame(data, index=[0])
        df.to_csv(csv_file_path, index=False, header=True)
    else:
        df = pd.read_csv(csv_file_path, index_col=False)
        df2 = pd.DataFrame(data, index=[len(df)])
        df3 = pd.concat([df, df2], axis=0)
        df3.to_csv(csv_file_path, index=False, header=True)