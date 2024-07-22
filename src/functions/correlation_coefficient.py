import numpy as np 
import pandas as pd

import warnings
warnings.filterwarnings("ignore")

def get_top_correlations_blog(df, threshold):
    """
    df: the dataframe to get correlations from
    threshold: the maximum and minimum value to include for correlations. For eg, if this is 0.4, only pairs haveing a correlation coefficient greater than 0.4 or less than -0.4 will be included in the results. 
    """
    orig_corr = df.corr()
    c = orig_corr.abs()

    so = c.unstack()

    i=0
    pairs=set()
    result = pd.DataFrame()
    for index, value in so.sort_values(ascending=False).items():
        # Exclude duplicates and self-correlations
        if value > threshold \
        and index[0] != index[1] \
        and (index[0], index[1]) not in pairs \
        and (index[1], index[0]) not in pairs:
            
            result.loc[i, ['Feature1', 'Feature2', 'Correlation Coefficient>'+str(threshold)]] =\
                [index[0], index[1], orig_corr.loc[(index[0], index[1])]]
            pairs.add((index[0], index[1]))
            i+=1
    
    result.iloc[:,2]=result.iloc[:,2].apply(lambda x: round(x, 3))
    return result#.reset_index(drop=True).set_index(['Variable 1', 'Variable 2'])