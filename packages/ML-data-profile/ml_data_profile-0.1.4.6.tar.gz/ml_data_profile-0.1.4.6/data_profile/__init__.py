import pandas as pd 
import numpy as np  
import colorama
from colorama import Fore
from data_profile.exception.exception import CustomPacakgeException
from data_profile.logging.logger import logging
import sys
import matplotlib.pyplot as plt
import seaborn as sns
import math
from scipy.stats import chi2_contingency




class DataReader:
    """
    DataCharting is a utility class for performing univariate data visualization
    on numerical and categorical features of a pandas DataFrame.

    It supports flexible chart types, automatic feature segregation, optional
    target exclusion, and configurable subplot layouts.

    Parameters
    ----------
    data : pandas.DataFrame
        Input dataset containing numerical and categorical columns.

    columns : int, default=3
        Number of subplot columns to be used while rendering charts.

    y : str or None, default=None
        Target column name to be excluded from feature visualization.

    figsize : tuple of int, default=(10, 10)
        Figure size for the generated plots.

    drop_cols : list, default=[None]
        List of column names to be excluded from visualization.

    cat_col_chart : str, default="countplot"
        Chart type to be used for categorical variables.
        Supported options typically include:
        - "countplot"
        - "barplot"
        

    num_col_chart : str, default="histplot"
        Chart type to be used for numerical variables.
        Supported options typically include:
        - "histplot"
        - "kdeplot"
        - "boxplot"
        - "violinplot"
       

    Attributes
    ----------
    data : pandas.DataFrame
        Stored input dataset.

    y : str or None
        Target variable excluded from analysis.

    figsize : tuple
        Figure size used for plotting.

    columns : int
        Number of columns in subplot grid.

    drop_cols : list
        Columns to be excluded from visualization.

    cat_col_chart : str
        Select chart type for categorical features.

    num_col_chart : str
        Select chart type for numerical features.
    """

    def __init__(self,data:pd.DataFrame,columns:int=3,y=None,figsize=(10,10),drop_cols:list=[None],cat_col_chart="countplot",num_col_chart="histplot"):
        self.data=data
        self.y=y
        self.figsize=figsize
        self.columns=columns
        self.drop_cols=drop_cols
        self.cat_col_chart=cat_col_chart
        self.num_col_chart=num_col_chart

    def data_summary(self):
        try:
            logging.info("Data summary started")
            summ_df=pd.DataFrame(
                [
                    [col,
                    self.data[col].dtype,
                    self.data[col].isna().sum(),
                    100*self.data[col].isna().sum()/len(self.data[col]),
                    self.data[col].nunique(),
                    self.data[col].unique()[:4],
                    ]
                    for col in self.data.columns
                ],
                columns=[
                    "Column",
                    "Data Type",
                    "Null Count",
                    "Null Percentage",
                    "Unique Count",
                    "Unique Values",    
                ]
            )
            print(f"Total Number of Columns: {len(self.data.columns)}\nTotal Number of Rows: {len(self.data)}")
            return summ_df

        except Exception as e:
            raise CustomPacakgeException(e,sys) 

    def data_charting(self):
        try:
            logging.info("Data charting started")

            # Identify categorical and numeric columns
            cat_columns = [col for col in self.data.columns if self.data[col].dtype == "object"]
            num_columns = [col for col in self.data.columns if self.data[col].dtype != "object"]

            # Remove target variable from both lists (if present)
            if self.y is not None:
                if self.y in cat_columns:
                    cat_columns.remove(self.y)
                if self.y in num_columns:
                    num_columns.remove(self.y)
            
            if self.drop_cols is not None:
                cat_columns=[col for col in cat_columns if col not in self.drop_cols]
                num_columns=[col for col in num_columns if col not in self.drop_cols]

            # -------------------------------
            # Plot numeric columns
            # -------------------------------
            if len(num_columns) > 0:
                plt.figure(figsize=self.figsize)
                plt.suptitle("Univariate Analysis – Numerical Columns",
                            fontsize=20, fontweight="bold", alpha=0.8, y=1.02)

                nrows = math.ceil(len(num_columns) / self.columns)

                for i, col in enumerate(num_columns):
                    plt.subplot(nrows, self.columns, i + 1)

                    if self.num_col_chart == "histplot":
                        sns.histplot(self.data[col],bins=30)
                    elif self.num_col_chart == "kdeplot":
                        sns.kdeplot(self.data[col])
                    elif self.num_col_chart == "boxplot":
                        sns.boxplot(self.data[col])
                    elif self.num_col_chart == "violinplot":
                        sns.violinplot(self.data[col])
                    plt.xlabel(col)

                plt.tight_layout()
                plt.show()
            else:
                logging.info("No numerical columns available for charting.")

            # -------------------------------
            # Plot categorical columns
            # -------------------------------
            if len(cat_columns) > 0:
                plt.figure(figsize=self.figsize)
                plt.suptitle("Univariate Analysis – Categorical Columns",
                            fontsize=20, fontweight="bold", alpha=0.8, y=1.02)

                nrows = math.ceil(len(cat_columns) / self.columns)

                for i, col in enumerate(cat_columns):
                    plt.subplot(nrows, self.columns, i + 1)

                    if self.cat_col_chart == "countplot":
                        sns.countplot(x=self.data[col])
                    elif self.cat_col_chart == "barplot":
                        sns.barplot(x=self.data[col])
        
                    plt.xlabel(col)
                    plt.xticks(rotation=45)

                plt.tight_layout()
                plt.show()
            else:
                logging.info("No categorical columns available for charting.")

        except Exception as e:
            raise CustomPacakgeException(e, sys)

    def stats_summary(self):
        try:
            logging.info("Data charting started")

            # Identify categorical and numeric columns
            num_columns = [col for col in self.data.columns if self.data[col].dtype != "object"]

            ds=self.data[num_columns].describe()
            plt.figure(figsize=self.figsize)
            plt.suptitle("Correlation Matrix of Numerical Columns",
                        fontsize=20, fontweight="bold", alpha=0.8, y=1.02)
            sns.heatmap(self.data[num_columns].corr(),annot=True,cmap="coolwarm")
            plt.tight_layout()
            plt.show()
            return ds
            
            

        except Exception as e:
            raise CustomPacakgeException(e, sys)







            
            
            