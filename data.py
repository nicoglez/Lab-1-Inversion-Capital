import functions

# Bajar informacion de .csv's donde se encuentran las ponderaciones iniciales y los activos
path = 'files/2020_01_2022_07'
df = functions.get_data(path)

# Bajar precios y rendimientos
start_date = "31-01-2020"
end_date = "29-07-2022"
precios = functions.portfolio_history(df, start_date, end_date)  # Bajar precios
rendimientos = precios.pct_change().dropna()  # Obtener rendimientos
