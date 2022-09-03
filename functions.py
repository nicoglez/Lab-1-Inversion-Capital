import os
import pandas as pd
from datetime import datetime
import numpy as np
import pandas_datareader.data as web
from typing import Optional, List

# Funcion que elimina simbolos raros
def delete_symbols(string: str) -> str:
    return "".join([i for i in string.replace(".", "-") if i != "*"]) + ".MX"

# Funcion que agrega un dash - a un string en funcion de un indice dado
def insert_dash(string: str, index: int) -> str:
    return string[:index] + '-' + string[index:]

# Funcion que convierte en float una lista de strings, quita las comas para no tener problemas
def float_converter(data: pd.DataFrame) -> np.array:
    return np.array([float("".join([k for k in i if k != ","])) for i in data])

# Funcion que baja informacion de csv's de files
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
    incomplete_stocks = ["SITES1A-1.MX"]
    for i in range(len(df)):
        # Si tienen un na, agregarlos a lista de incompletos
        if True if sum(np.isnan(df.values[i])) else False:
            ticker = list(df.index)[i]
            incomplete_stocks.append(ticker)
    # Quitar stocks sin informacion
    df.drop(incomplete_stocks, inplace=True)

    return df

# Función que obtiene el valor de las columnas de un df y regresa una lista con las mismas
def get_cols(df: pd.DataFrame) -> List:
    return list(df.columns)

# Función para descargar precios de cierre:
def get_adj_closes(tickers: str, start_date: str = None, end_date: Optional[str] = None, freq: str = 'd'):
    # Bajar solo un dato si end_date no se da
    end_date = end_date if end_date else start_date or None
    # Bajar cierre de precio ajustado
    closes = web.YahooDailyReader(symbols=tickers, start=start_date, end=end_date, interval=freq).read()['Adj Close']
    # Poner indice de forma ascendente
    closes.sort_index(inplace=True)
    return closes

# Funcion que baja la informacion historica del portafolio
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


class inversion_pasiva:

    # Inicializar variables in
    def __init__(self, df: pd.DataFrame, precios: pd.DataFrame, rends: pd.DataFrame,
                 capital: float, start_date: str, end_date: str):
        self.data = df
        self.cap = capital
        self.start = start_date
        self.end = end_date
        self.prices = precios
        self.rends = rends

    # Funcion para obtener cash en t=0
    def Cash(self, money_or_weight: Optional[bool] = False) -> float:
        data = self.data  # obtener data
        # Cash es el complemento de las ponderaciones para alcanzar el 100%
        cash = (1 - sum(data.iloc[:, 0])) if money_or_weight else (1 - sum(data.iloc[:, 0])) * self.cap
        return cash

    # Obtener pesos de activos, ya sea con cash o sin cash
    def weights(self, with_Cash: Optional[bool] = False) -> pd.DataFrame:
        # los pesos son los pesos en nuestro excel en t=0
        w = self.data.iloc[:, 0]
        if with_Cash:
            w["Cash"] = self.Cash(True)
        return w

    # Simulacion de estrategia pasiva
    def simulation(self, comision: Optional[float] = 0) -> pd.DataFrame:
        # Obtener posicion: Pesos por el capital inicial
        posicion_pasiva = self.weights() * self.cap
        # Los precios en t=0 (precio al que compramos)
        precios_iniciales = self.prices.iloc[0, :].values
        # El numero de acciones a comprar es nuestra posicion entre los precios iniciaes
        num_acciones_pasiva = np.floor(posicion_pasiva.values / precios_iniciales)
        # Obtener portafolio inicial y sumarle comision
        portafolio_pasivo_inicial = (num_acciones_pasiva * list(precios_iniciales) * (1 + comision))
        # Lo que falta para nuestro capital lo tomamos como cash
        cash = self.cap - sum(portafolio_pasivo_inicial)

        # Obtener rendimientos historicos de acciones y hacer una productoria cumulativa para simular estrategia
        portafolio_historico_pasivo = pd.DataFrame(self.rends).dropna().T + 1
        portafolio_historico_pasivo.iloc[:, 0] *= portafolio_pasivo_inicial
        # Cambiar formato
        pd.options.display.float_format = '{:,.4f}'.format
        # Crear df con portafolio pasivo
        portafolio_pasivo = pd.DataFrame()
        # Juntar con capital en t= 0
        initial_value = pd.Series({datetime.strptime(posicion_pasiva.name, "%Y-%m-%d"): self.cap})
        dates_list = get_cols(self.data)
        # Sumar por columnas el valor de posicion en cada accion para obtener valor del portafolio en t=n
        portafolio_pasivo['Capital'] = initial_value.append(portafolio_historico_pasivo.cumprod(axis=1).sum(axis=0))
        portafolio_pasivo = portafolio_pasivo[portafolio_pasivo.index.isin(dates_list)]
        # Obtener rendimientos
        portafolio_pasivo['Rend'] = portafolio_pasivo['Capital'].pct_change().fillna(0)
        # Obtener rendimientos acumulados
        portafolio_pasivo['Rend Acum'] = ((portafolio_pasivo["Rend"] + 1).cumprod() - 1).fillna(0)

        return portafolio_pasivo
