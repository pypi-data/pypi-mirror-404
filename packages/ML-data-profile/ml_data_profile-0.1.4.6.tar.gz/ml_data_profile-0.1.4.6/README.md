# data_profile

`data_profile` is a lightweight Python utility for quickly profiling tabular datasets (Pandas DataFrames).  
It helps you understand basic data quality and structure by summarising:

- Column names  
- Data types  
- Null (missing) counts  
- Null percentages  
- Number of unique values  
- Sample of unique values  

This is especially useful in **EDA (Exploratory Data Analysis)** and **data quality checks** before modelling.

---

## 🚀 Features

- Simple `DataReader` class that wraps a `pandas.DataFrame`
- One-call `data_summary()` method to generate a clean summary table
- Custom exception handling via `CustomPacakgeException`
- Logging support via `logging` from `data_profile.logging.logger`

---

## 📦 Installation

### Notebook

    !pip install ML-data-profile


🧩 Usage


1️⃣ Import and prepare your data

    import pandas as pd
    import data_profile
    from data_profile import DataReader
    

    # Example DataFrame
    df = pd.DataFrame({
        "age": [25, 30, 35, None],
        "gender": ["M", "F", "M", "F"],
        "income": [50000, 60000, None, 80000]
    })

    #Initialize DataReader
    data_reader = DataReader(df)
    
    #Generate summary
    summary = data_reader.data_summary()
    summary