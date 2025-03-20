from dash import Dash
from frontend.layout import layout
from frontend.callbacks import register_callbacks

# @Author: Asta Omarsdottir
# @Email: asta.omarsdottir@gmail.com
# @Date: 2024-12-01
# @Last Modified by:   undefined
# @Last Modified time: 2024-12-01
# @Description: Main entry point of the application


# ***************************************************************************************

app = Dash(__name__, suppress_callback_exceptions=True)
app.title = "Oceanus Vessel-Cargo Analysis"

# Ställ in layout
app.layout = layout

# Registrera callbacks
register_callbacks(app)

if __name__ == "__main__":
    app.run_server(debug=True)
