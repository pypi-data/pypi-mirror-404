def getSimple(df,n=1000)
    df = df.sample(n=n, replace=True, random_state=42)
    return df
