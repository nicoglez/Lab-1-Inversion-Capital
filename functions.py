import os
import pandas as pd
from datetime import datetime
import numpy as np
import pandas_datareader.data as web
from typing import List, Optional


def delete_symbols(string: str) -> str:
    # Funcion que elimina simbolos raros
    return "".join([i for i in string.replace(".", "-") if i != "*"]) + ".MX"

def insert_dash(string: str, index: int) -> str:
    # funcion que agrega un dash - a un string en funcion de un indice dado
    return string[:index] + '-' + string[index:]

def float_converter(data: pd.DataFrame) -> np.array:
    # funcion que convierte en float una lista de strings, quita las comas para no tener problemas
    return np.array([float("".join([k for k in i if k != ","])) for i in data])


def get_data(path: str) -> pd.DataFrame:
    try:
        files = os.listdir(path)
    except:
        print("Path no encontrado/incorrecto")
    df = pd.DataFrame()  # crear data frame
    # for para leer los n csv's del directorio dado
    for file in files:
        # Leer csvs
        data = pd.read_csv(path + "/" + file, skiprows=2)
        # Obtener fecha del csv
        date = "".join([date for date in file if date.isnumeric()])
        # Cambio de formato de fecha
        for i in [4, 7]:
            date = insert_dash(date, i)
            # Dividir peso entre 100 porque esta en %, para facilitar lectura
        df[date] = data["Peso (%)"] / 100
    # Eliminar simbolos raros del ticker
    df["Ticker"] = [delete_symbols(ticker) for ticker in data["Ticker"]]
    # Crear df
    df = df.set_index("Ticker")
    # Quitar Stocks sin informacion (SitesB-1 y SitesA-1 no tienen info)
    incomplete_stocks = ["SITESB-1.MX"]
    for i in range(len(df)):
        # Si tienen un na, agregarlos a lista de incompletos
        if True if sum(np.isnan(df.values[i])) else False:
            ticker = list(df.index)[i]
            incomplete_stocks.append(ticker)
    # Quitar stocks sin informacion
    df.drop(incomplete_stocks, inplace=True)
    return df

# Función para descargar precios de cierre:
def get_adj_closes(tickers: str, start_date: str = None, end_date: Optional[str] = None, freq: str = 'd'):
    # Bajar solo un dato si end_date no se da
    end_date = end_date if end_date else start_date or None
    # Bajar cierre de precio ajustado
    closes = web.YahooDailyReader(symbols=tickers, start=start_date, end=end_date, interval=freq).read()['Adj Close']
    # Poner indice de forma ascendente
    closes.sort_index(inplace=True)
    return closes


def portfolio_history(df: pd.DataFrame, start_date: str, end_date: str) -> pd.DataFrame:
    precios_historicos = {}
    stock_index = 0
    stocks_quantity = len(df.index)
    # Iterar sobre los tickers y repetir si hay error al bajar alguna informacion
    while len(precios_historicos.keys()) != stocks_quantity:
        stock = list(df.index)[stock_index] # agarrar un ticker
        try: # intentar bajar historicos
            precios_historicos[stock] = get_adj_closes(stock, start_date=start_date, end_date=end_date)
            stock_index += 1 # sumar uno si se bajo info
        except: # intentar otra vez si no se pudo bajar informacion
            continue
    return pd.DataFrame(precios_historicos)