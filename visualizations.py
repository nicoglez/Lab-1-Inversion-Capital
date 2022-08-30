import plotly.express as px
from data import df_pasiva

#  Creacion de grafico de estrategia pasiva
pasiva_chart = px.line(df_pasiva, x=df_pasiva.index, y="Capital")  # Grafica de lineas
pasiva_chart.update_xaxes(title_text='Fecha')  # Cambiar x label
# Str con subtitulo
subtitle = f" Valor inicial Portafolio: {df_pasiva.iloc[0, 0]} ; Valor Final Portafolio: {round(df_pasiva.iloc[-1, 0],2)}"
subtitle = subtitle + f" ; Rend Acumulado Efectivo: {round((df_pasiva.iloc[-1, 0] / df_pasiva.iloc[0, 0] - 1) * 100 , 2)}% "
#  Cambiar Titulo y Formato
pasiva_chart.update_layout(title=f"Valor de la Cartera Estrategia Pasiva <br><sup>{subtitle}</sup>", title_x=0.5)
pasiva_chart.update_traces(line_color='Black')
