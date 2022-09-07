import os
import pandas as pd
from datetime import datetime
import numpy as np
import pandas_datareader.data as web
from typing import Optional, List, Tuple


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
        stock = list(df.index)[stock_index]  # agarrar un ticker
        try:  # intentar bajar historicos
            precios_historicos[stock] = get_adj_closes(stock, start_date=start_date, end_date=end_date)
            stock_index += 1  # sumar uno si se bajo info
        except:  # intentar otra vez si no se pudo bajar informacion
            continue
    return pd.DataFrame(precios_historicos)


class Inversion_Pasiva:

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


# Clase que ayuda a optimizar Sharpe
class Sharpe_Optimization:

    def __init__(self, rf):
        self.rf = rf

    @staticmethod
    def max_ratio_Sharpe(tickers: np.array, mean: float, rf: float, cov: np.array) -> dict:
        # Hacemos 6,000 simulaciones por default
        n_sims = 6000

        # Definir vectores a llamar
        return_array = np.zeros(n_sims)
        vol_array = np.zeros(n_sims)
        sharpe_ratio = np.zeros(n_sims)
        n_weights = np.zeros([n_sims, len(tickers)])

        # Simular n veces los pesos y caracteristicas del portafolio
        for i in range(n_sims):
            rands = np.random.rand(len(tickers))
            w_temp = rands / sum(rands)
            n_weights[i, :] = w_temp
            return_array[i] = np.sum(np.dot(w_temp, mean.values))
            vol_array[i] = np.dot(w_temp, np.dot(cov, w_temp)) ** 0.5

            sharpe_ratio[i] = (return_array[i] - rf) / vol_array[i]

        # Obtener pesos que dieron mayor radio de sharpe
        optimal_weights = dict(zip(tickers, [y for y in list(n_weights[np.argmax(sharpe_ratio)])]))
        return optimal_weights

    def Sharpe_with_prices(self, precios: pd.DataFrame, df: pd.DataFrame,
                           start_date: Optional[str], end_date: Optional[str]) -> dict:
        rendimientos_log = np.log(precios / precios.shift()).dropna()
        rendimientos_log.reset_index(inplace=True)
        rendimientos_log = rendimientos_log[(rendimientos_log["Date"] >= start_date) &
                                            (rendimientos_log["Date"] <= end_date)]
        rendimientos_log.set_index("Date", inplace=True)
        # Obtener metricas
        mean_data_sharpe = rendimientos_log.mean() * 252
        cov_data_sharpe = rendimientos_log.cov() * 252
        rf = self.rf
        # Maximizar sharpe y regresar resultado
        return self.max_ratio_Sharpe(tickers=df.index.values, mean=mean_data_sharpe, rf=rf, cov=cov_data_sharpe)


# Clase de inversion activa
class Inversion_Activa:

    # Inicializar variables in
    def __init__(self, df: pd.DataFrame, weights: dict, prices: pd.DataFrame, capital: float, start_date: str):
        self.df = df
        self.weights = weights
        self.cap = capital
        self.start = start_date
        self.precios = prices

    # Simulacion de estrategia pasiva
    def simulation(self, comision: Optional[float] = 0) -> Tuple[pd.DataFrame, pd.DataFrame]:
        # Filtar df
        dates_list = get_cols(self.df)
        precios_activa = self.precios.reset_index()
        precios_activa = precios_activa[(precios_activa["Date"] >= self.start)]
        precios_activa.set_index("Date", inplace=True)
        precios_activa = precios_activa[precios_activa.index.isin(dates_list)]
        rendimientos_activa = precios_activa.pct_change().dropna()
        # Obtener posicion: Pesos por el capital inicial
        posicion_activa = [i * self.cap for i in self.weights.values()]
        # El numero de acciones a comprar es nuestra posicion entre los precios iniciaes
        num_acciones_activa = np.floor(posicion_activa/precios_activa.iloc[0, :])
        # Portafolio inicial
        portafolio_activo = (num_acciones_activa * list(precios_activa.iloc[0, :]) * (1 + comision)).fillna(0)
        # Obtener comision total inicial
        comision_total = sum(portafolio_activo - num_acciones_activa * list(precios_activa.iloc[0, :]))
        # Obtener cash
        cash = self.cap - sum(portafolio_activo)
        # Valor Inicial del Portafolio.
        V_port_activa = []
        V_port_activa.append([portafolio_activo.name, float(portafolio_activo.sum() + cash)])
        # Inicializar df de Operaciones
        Operaciones_data = []
        Operaciones_data.append([portafolio_activo.name, sum(num_acciones_activa), sum(num_acciones_activa),
                                 0, comision_total, comision_total])
        # Validador de cash
        cash_validator = lambda spend, available_cash: True if available_cash >= spend else False

        # SIMULAR ESTRATEGIA ACTIVA
        for n_date in range(1, len(rendimientos_activa)):

            bought_stocks_temp = 0
            selled_stocks_temp = 0
            comision_temp = 0
            precios_temp = precios_activa.iloc[n_date, :]
            rendimientos_temp = rendimientos_activa.iloc[n_date, :]

            for stock in range(len(precios_temp)):

                # Caso Comprar: Rendimientos con variacion mayor o igual a 5%
                if rendimientos_temp[stock] >= 0.05 and cash_validator(0, cash):
                    n_to_buy = np.floor(num_acciones_activa[stock] * 2.5 / 100)

                    if cash_validator(n_to_buy * precios_temp[stock] * (1 + comision), cash):

                        # Obtener cuanto cuestan acciones
                        comision_temp += n_to_buy * precios_temp[stock] * comision
                        spend = n_to_buy * precios_temp[stock] * (1 + comision)

                        # Actualizar portafolio
                        cash = cash - spend
                        num_acciones_activa[stock] = num_acciones_activa[stock] + n_to_buy
                        bought_stocks_temp += n_to_buy
                    else:
                        continue

                # Caso Vender: Rendimientos con variacion mayor o igual a -5%
                elif rendimientos_temp[stock] <= -0.05:
                    # Obtener cant de acciones a vender y cuanto cuestan
                    n_to_sell = np.ceil(num_acciones_activa[stock] * 2.5 / 100)
                    comision_temp += n_to_sell * precios_temp[stock] * comision
                    money = n_to_sell * precios_temp[stock] * (1 - comision)
                    # Actualizar portafolio
                    cash = cash + money
                    num_acciones_activa[stock] = num_acciones_activa[stock] - n_to_sell
                    selled_stocks_temp += n_to_sell

                # Caso no hacer nada: Rendimientos entre -5% y 5%
                else:
                    continue

            V_port_activa.append([precios_temp.name, float(sum(num_acciones_activa * precios_temp) + cash)])
            Operaciones_data.append(
                [precios_temp.name, sum(num_acciones_activa), bought_stocks_temp, selled_stocks_temp,
                 comision_temp, float(Operaciones_data[-1][5]) + comision_temp])

        # Cambiar display de df
        pd.options.display.float_format = '{:,.4f}'.format
        # Crear df de activas
        df_activa = pd.DataFrame(V_port_activa)
        df_activa.columns = ["Date", "Capital"]
        df_activa.set_index("Date", inplace=True)
        df_activa['Rend'] = df_activa['Capital'].pct_change().fillna(0)
        df_activa['Rend Acum'] = ((df_activa["Rend"] + 1).cumprod() - 1).fillna(0)
        # Crear df con operaciones
        df_operaciones = pd.DataFrame(Operaciones_data)
        df_operaciones.columns = ["Date", "Titulos Totales", "Titulos Compra", "Titulos Venta", "Comision",
                                  "Comision Acumulada"]
        df_operaciones.set_index("Date", inplace=True)

        return df_activa, df_operaciones


# Funcion que hace resumen financiero de dos estrategias
def Summary(df_1: pd.DataFrame, df_2: pd.DataFrame, col_names: List[str], rf_anual: float) -> pd.DataFrame:
    # Hacer mensual la rf
    rf = rf_anual / 12
    # Crear df
    df_medidas = pd.DataFrame()
    # Obtener Rend_Mensual
    df_medidas["Rend Mensual %"] = [(df_1.iloc[:, 1].mean()) * 100, (df_2.iloc[:, 1].mean()) * 100]
    df_medidas["Rend Acumulado Mensual %"] = [df_1.iloc[:, 2].mean() * 100, (df_2.iloc[:, 2].mean() * 100)]
    df_medidas["Volatilidad %"] = [df_1.iloc[:, 1].std() * 100, (df_2.iloc[:, 1].std() * 100)]
    # Obtener Ratio de Sharpe
    df_medidas["Ratio de Sharpe"] = [(df_1.iloc[:, 1].mean() - rf) / (df_1.iloc[:, 1].std()),
                                     (df_2.iloc[:, 1].mean() - rf) / (df_2.iloc[:, 1].std())]
    # Transponer y nombar df
    df_medidas = df_medidas.T
    df_medidas.columns = col_names

    return df_medidas
