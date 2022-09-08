# Importar datos
from data import df, precios, rendimientos

# Importar funciones necesarias
from functions import Inversion_Pasiva
from functions import Sharpe_Optimization
from functions import Inversion_Activa
from functions import Summary

# Importar grafica de pesos
from visualizations import weights_chart

# Definir clase de inversion pasiva
capital = 1000000
pasiva = Inversion_Pasiva(df=df, prices=precios, rends=rendimientos, capital=capital,
                          start_date="2021-01-29", end_date="29-07-2022")

# Simular inversion pasiva
comision = 0.00125
df_pasiva = pasiva.simulation(comision=comision)

# Iniciar inversion activa
# Obtener Sharpe Optimo
w_RS = Sharpe_Optimization(rf=.0429).Sharpe_with_prices(precios=precios,
                                                        df=df,
                                                        start_date="2020-01-01",
                                                        end_date="2021-01-31")
# Dibujar pesos optimos
weights_chart(optimal_weights=w_RS)

# Con los pesos óptimos, definir clase de Inversion Activa
activa = Inversion_Activa(df=df, weights=w_RS, prices=precios, capital=capital, start_date="2021-01-01")
# Simular Inversion Activa
df_activa, df_operaciones = activa.simulation(comision=0.00125)

# Calcular medidas de desempeño en base a dfs de estrategias
df_medidas = Summary(df_1=df_pasiva, df_2=df_activa, col_names=["Pasiva", "Activa"], rf_anual=0.0429)




