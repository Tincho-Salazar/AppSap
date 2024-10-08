# from waitress import serve
from flask import Flask, render_template, request,jsonify
from config import db_config
import pyodbc

app = Flask(__name__)

# Configuración de la conexión a SQL Server
def connect_to_sql_server():
    conn_str = (
    f"DRIVER={{ODBC Driver 18 for SQL Server}};"
    f"SERVER={db_config['server']};"
    f"DATABASE={db_config['database']};"
    f"UID={db_config['username']};"
    f"PWD={db_config['password']};"  # Agrega punto y coma (;) al final de cada parámetro
    "Encrypt=yes;"                   # Sin f-string, ya que no depende de variables
    "TrustServerCertificate=yes;"    # Sin f-string, se concatena como literal
    )

    try:
        return pyodbc.connect(conn_str)
    except pyodbc.Error as ex:
        print(f"Error de conexión: {ex}")
        return None

# Función para obtener los productos
def obtener_productos(selected_empresa, ocultar_sin_stock):
    conn = connect_to_sql_server()
    if conn:
        query = """
            SELECT DISTINCT T4.GRUPO, T4.ESPECIFICO, T4.DESCRIPCION, T1.MATNR, T1.MAKTX,
            CAST(T5.LABST AS numeric(36,2)) AS STOCK
            FROM prd.MAKT AS T1
            INNER JOIN prd.MARA AS T2 ON T1.MANDT = T2.MANDT AND T1.MATNR = T2.MATNR
            INNER JOIN prd.MBEW AS T3 ON T1.MANDT = T3.MANDT AND T1.MATNR = T3.MATNR
            INNER JOIN prd.MARD AS T5 ON T1.MANDT = T5.MANDT AND T1.MATNR = T5.MATNR
            LEFT JOIN prd.ZLMATDESCR AS T4 ON T1.MANDT = T4.MANDT AND T1.MATNR = T4.MATNR
            WHERE T1.MANDT = 500 AND T2.MTART = 'ERSA' AND T3.BWKEY = ?
        """
        # Agregar condición para ocultar productos sin stock
        if ocultar_sin_stock:
            query += " AND T5.LABST > 0"

        cursor = conn.cursor()
        cursor.execute(query, selected_empresa)
        productos = cursor.fetchall()

        # Obtener los nombres de las columnas
        columnas = [column[0] for column in cursor.description]
        productos_list = [dict(zip(columnas, row)) for row in productos]

        cursor.close()
        conn.close()

        return productos_list
    else:
        return []

# Ruta principal que renderiza el template index.html y muestra los datos
@app.route('/', methods=['GET', 'POST'])
def index():
    selected_empresa = request.form.get('empresaSelect', 'BP01')  # Valor por defecto
    ocultar_sin_stock = 'ocultarSinStock' in request.form  # Verificar si el checkbox está marcado
    productos = obtener_productos(selected_empresa, ocultar_sin_stock)
    return render_template('index.html', productos=productos, selected_empresa=selected_empresa, ocultar_sin_stock=ocultar_sin_stock)

# Ruta para actualizar productos según selección
@app.route('/actualizar', methods=['POST'])
def actualizar():
    selected_empresa = request.form.get('empresaSelect', 'BP01')  # Valor por defecto
    ocultar_sin_stock = request.form.get('ocultarSinStock') == '1'  # Convertir a booleano
    productos = obtener_productos(selected_empresa, ocultar_sin_stock)
    return jsonify({'productos': [dict(producto) for producto in productos]})
if __name__ == '__main__':
    # serve(app, host='0.0.0.0', port=5055)
    app.run(debug=True)
