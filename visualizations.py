import plotly.express as px
from data import df_pasiva

#  Creacion de grafico de estrategia pasiva
pasiva_chart = px.line(df_pasiva, x=df_pasiva.index, y="Capital")  # Grafica de lineas
pasiva_chart.update_xaxes(title_text='Fecha')  # Cambiar x label
# Cambiar titulo y Formato
pasiva_chart.update_layout(title=f"Evolución del Valor de la Cartera Estrategia Pasiva", title_x=0.5)
pasiva_chart.update_traces(line_color='Black')
pasiva_chart.show()