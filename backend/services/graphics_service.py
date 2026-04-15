import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import pandas as pd
import io
import base64

def fig_to_base64(fig):
        buf = io.BytesIO()
        fig.savefig(buf, format='png')
        buf.seek(0)
        img_str = base64.b64encode(buf.getvalue()).decode()
        return f'data:image/png;base64,{img_str}'

def create_forecast_plots(forecast_result, target_column):
    df = pd.DataFrame(forecast_result)
    df['date'] = pd.to_datetime(df['date'].apply(lambda x: datetime.strptime(str(x).split()[0], '%Y/%m' if '/' in str(x) else '%Y-%m-%d')))
    forecast_size = df['lower_quantile'].notna().sum()
    size_for_second = min(forecast_size * 9, len(df))
    
    
    
    # Historical plot
    fig1, ax1 = plt.subplots(figsize=(10, 6))
    plt.ion()
    historical_data = df[df['lower_quantile'].isna()]
    ax1.plot(historical_data['date'], historical_data[target_column], 'b-', label='Historical')
    ax1.set_title(f'Historical {target_column}')
    ax1.set_xlabel('Date')
    ax1.set_ylabel(target_column)
    ax1.grid(True)
    ax1.legend()
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    plt.xticks(rotation=45)
    plt.tight_layout()
    historical_base64 = fig_to_base64(fig1)
    plt.close(fig1)
    plt.ioff()
    # Forecast plot
    fig2, ax2 = plt.subplots(figsize=(12, 6))
    plt.ion()
    recent_data = df.iloc[-size_for_second:]
    
    historical_mask = recent_data['lower_quantile'].isna()
    ax2.plot(recent_data[historical_mask]['date'], 
             recent_data[historical_mask][target_column], 
             'b-', label='Historical')
    
    forecast_mask = ~historical_mask
    ax2.plot(recent_data[forecast_mask]['date'],
             recent_data[forecast_mask][target_column],
             'r--', label='Forecast')
    ax2.fill_between(recent_data[forecast_mask]['date'],
                     recent_data[forecast_mask]['lower_quantile'],
                     recent_data[forecast_mask]['upper_quantile'],
                     color='r', alpha=0.2, label='Confidence Interval')
    
    ax2.set_title(f'Historical and Forecast {target_column}')
    ax2.set_xlabel('Date')
    ax2.set_ylabel(target_column)
    ax2.grid(True)
    ax2.legend()
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    plt.xticks(rotation=45)
    plt.tight_layout()
    forecast_base64 = fig_to_base64(fig2)
    plt.close(fig2)
    plt.ioff()
    return {
        'historical_plot': historical_base64,
        'forecast_plot': forecast_base64
    }


def plot_dataframe(df, numeric_column=None):
    plt.ion()
    
    try:
        if numeric_column is None:
            numeric_columns = df.select_dtypes(include=['float64', 'int64']).columns
            numeric_column = numeric_columns[0]
            
        fig, ax = plt.subplots(figsize=(10, 6))
        df.plot(x='date', y=numeric_column, ax=ax)
        
        ax.set_title(f'Time Series: {numeric_column}')
        ax.set_xlabel('Date')
        ax.set_ylabel(numeric_column)
        ax.grid(True)
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        buf = io.BytesIO()
        fig.savefig(buf, format='png')
        buf.seek(0)
        plot_base64 = fig_to_base64(fig)
        
        plt.close(fig)
        plt.ioff()
        
        return plot_base64
        
    except Exception as e:
        plt.ioff()
        raise e