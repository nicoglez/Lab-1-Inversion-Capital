import pandas as pd
import plotly.express as px

def weights_chart(optimal_weights: dict):
    # Ordenar pesos de mayor a menor
    dic = dict()
    for i in list(dict(sorted(optimal_weights.items(), key=lambda item: item[1])))[::-1]:
        dic.update({i: optimal_weights.get(i)})

    data_frame = pd.DataFrame()
    data_frame["Ticker"] = dic.keys()
    data_frame["Peso"] = dic.values()

    # Plottear pesos en barras
    weights_bar_chart = px.bar(data_frame, x="Ticker", y="Peso")
    weights_bar_chart.update_layout(
        title="Distribución Pesos de Portafolio Eficiente",
        xaxis_title="Ticker",
        yaxis_title="Peso",
        font=dict(
            size=15,
            color="Black"
        )
    )

    return weights_bar_chart
