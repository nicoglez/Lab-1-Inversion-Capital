# Importar datos
from data import df, precios, rendimientos

# Importar funciones
import functions

# Definir clase de inversion pasiva
capital = 1000000
start_date = "31-01-2020"
end_date = "29-07-2022"
pasiva = functions.inversion_pasiva(df, precios, rendimientos, capital, start_date, end_date)

# Simular inversion pasiva
comision = 0.00125
df_pasiva = pasiva.simulation(comision=comision)
