import pandas as pd
import sqlalchemy
import logging
import os
from datetime import datetime

os.chdir(os.path.dirname(os.path.abspath(__file__)) + "/..")

os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/carga.log"),
        logging.StreamHandler()
    ]
)

#hacemos la conexion a la base de datos 
engine = sqlalchemy.create_engine(
    "mysql+mysqlconnector://admin:Forta165@localhost/ecommerce"
)
#creamos las tablas si no existen y limpiamos los datos antes de cargar los nuevos datos para evitar conflictos con los datos anteriores
def crear_tablas():
    with engine.begin() as conn:
        conn.execute(sqlalchemy.text("""
            CREATE TABLE IF NOT EXISTS clientes (
                cliente_id      VARCHAR(10)   PRIMARY KEY,
                nombre          VARCHAR(100),
                email           VARCHAR(100),
                telefono        VARCHAR(20),
                ciudad          VARCHAR(50),
                pais            VARCHAR(10),
                fecha_registro  DATE,
                edad            FLOAT,
                genero          VARCHAR(20),
                rango_etario    VARCHAR(20)
            )
        """))

        conn.execute(sqlalchemy.text("""
            CREATE TABLE IF NOT EXISTS productos (
                producto_id   VARCHAR(10)   PRIMARY KEY,
                nombre        VARCHAR(100),
                categoria     VARCHAR(50),
                precio        DECIMAL(10,2),
                stock         INT,
                peso_kg       DECIMAL(6,2),
                activo        VARCHAR(20),
                proveedor     VARCHAR(100),
                rango_precio  VARCHAR(20)
            )
        """))

        conn.execute(sqlalchemy.text("""
            CREATE TABLE IF NOT EXISTS pedidos (
                pedido_id        VARCHAR(10)   PRIMARY KEY,
                cliente_id       VARCHAR(10),
                producto_id      VARCHAR(10),
                fecha_pedido     DATE,
                cantidad         FLOAT,
                precio_unitario  DECIMAL(10,2),
                descuento_pct    FLOAT,
                total            DECIMAL(10,2),
                estado           VARCHAR(30),
                metodo_pago      VARCHAR(30),
                tiene_descuento  BOOLEAN,
                FOREIGN KEY (cliente_id)  REFERENCES clientes(cliente_id),
                FOREIGN KEY (producto_id) REFERENCES productos(producto_id)
            )
        """))

        conn.execute(sqlalchemy.text("""
            CREATE TABLE IF NOT EXISTS devoluciones (
                devolucion_id      VARCHAR(10)  PRIMARY KEY,
                pedido_id          VARCHAR(10),
                cliente_id         VARCHAR(10),
                fecha_devolucion   DATE,
                motivo             VARCHAR(150),
                estado_devolucion  VARCHAR(30),
                monto_reembolso    DECIMAL(10,2),
                fecha_reembolso    DATE,
                FOREIGN KEY (pedido_id)  REFERENCES pedidos(pedido_id),
                FOREIGN KEY (cliente_id) REFERENCES clientes(cliente_id)
            )
        """))

        logging.info("tablas creadas correctamente")

#limpiamos las tablas antes de cargar los nuevos datos para evitar conflictos con los datos anteriores
def limpiar_tablas():
    with engine.begin() as conn:
        # desactivamos FK para poder borrar sin conflictos
        conn.execute(sqlalchemy.text("SET FOREIGN_KEY_CHECKS = 0"))
        conn.execute(sqlalchemy.text("TRUNCATE TABLE devoluciones"))
        conn.execute(sqlalchemy.text("TRUNCATE TABLE pedidos"))
        conn.execute(sqlalchemy.text("TRUNCATE TABLE productos"))
        conn.execute(sqlalchemy.text("TRUNCATE TABLE clientes"))
        conn.execute(sqlalchemy.text("SET FOREIGN_KEY_CHECKS = 1"))
        logging.info("tablas limpiadas correctamente")

#definir las tablas y sus rutas para cargar los datos
TABLAS = [
    ("clientes",     "data/validados/clientes_validados.csv"),
    ("productos",    "data/validados/productos_validados.csv"),
    ("pedidos",      "data/validados/pedidos_validados.csv"),
    ("devoluciones", "data/validados/devoluciones_validados.csv"),
]

def cargar_tabla(nombre, ruta):
    if not os.path.exists(ruta):
        logging.error(f"no existe: {ruta}")
        return

    df = pd.read_csv(ruta)

    pk_map = {
        "clientes":     "cliente_id",
        "productos":    "producto_id",
        "pedidos":      "pedido_id",
        "devoluciones": "devolucion_id"
    }
    pk = pk_map.get(nombre)
    if pk and pk in df.columns:
        antes = len(df)
        df = df.drop_duplicates(subset=[pk], keep="first")
        logging.info(f"duplicados de {pk} eliminados: {antes - len(df)}")


    with engine.connect() as conn_check:
        if nombre == "pedidos":
            clientes_bd  = pd.read_sql("SELECT cliente_id FROM clientes",  conn_check)["cliente_id"].tolist()
            productos_bd = pd.read_sql("SELECT producto_id FROM productos", conn_check)["producto_id"].tolist()
            antes = len(df)
            df = df[df["cliente_id"].isin(clientes_bd) & df["producto_id"].isin(productos_bd)]
            logging.info(f"pedidos con FK inválida eliminados: {antes - len(df)}")

        if nombre == "devoluciones":
            pedidos_bd  = pd.read_sql("SELECT pedido_id FROM pedidos",   conn_check)["pedido_id"].tolist()
            clientes_bd = pd.read_sql("SELECT cliente_id FROM clientes", conn_check)["cliente_id"].tolist()
            antes = len(df)
            df = df[df["pedido_id"].isin(pedidos_bd) & df["cliente_id"].isin(clientes_bd)]
            logging.info(f"devoluciones con FK inválida eliminadas: {antes - len(df)}")

    for col in df.columns:
        if "fecha" in col:
            df[col] = pd.to_datetime(df[col], errors="coerce")
            df[col] = df[col].where(df[col].notna(), other=None)

    logging.info(f"cargando {nombre}: {len(df)} filas")

    with engine.begin() as conn:
        try:
            df.to_sql(nombre, conn, if_exists="append", index=False)
            logging.info(f"✓ commit exitoso: {nombre}")
        except Exception as e:
            logging.error(f"✗ rollback en {nombre}: {e}")
            raise


def verificar():
    logging.info("=== verificación SQL ===")
    with engine.connect() as conn:

        # conteo de registros por tabla
        for tabla in ["clientes", "productos", "pedidos", "devoluciones"]:
            total = conn.execute(
                sqlalchemy.text(f"SELECT COUNT(*) FROM {tabla}")
            ).scalar()
            logging.info(f"{tabla}: {total} registros cargados")

        # consulta JOIN para verificar relaciones entre tablas
        sql = """
            SELECT 
                p.pedido_id,
                c.nombre    AS cliente,
                pr.nombre   AS producto,
                p.total
            FROM pedidos p
            JOIN clientes  c  ON p.cliente_id  = c.cliente_id
            JOIN productos pr ON p.producto_id = pr.producto_id
            LIMIT 5
        """
        df_check = pd.read_sql(sqlalchemy.text(sql), conn)
        logging.info(f"muestra JOIN pedidos-clientes-productos:\n{df_check.to_string()}")

        # consulta devoluciones con cliente
        sql2 = """
            SELECT
                d.devolucion_id,
                c.nombre   AS cliente,
                d.motivo,
                d.monto_reembolso,
                d.estado_devolucion
            FROM devoluciones d
            JOIN clientes c ON d.cliente_id = c.cliente_id
            LIMIT 5
        """
        df_check2 = pd.read_sql(sqlalchemy.text(sql2), conn)
        logging.info(f"muestra JOIN devoluciones-clientes:\n{df_check2.to_string()}")


if __name__ == "__main__":
    logging.info("====== ETAPA 4: CARGA ======")
    inicio = datetime.now()

    crear_tablas()
    limpiar_tablas()

    for nombre, ruta in TABLAS:
        cargar_tabla(nombre, ruta)

    verificar()

    logging.info(f"tiempo total: {datetime.now() - inicio}")
    logging.info("====== FIN ETAPA 4 ======")

def ejecutar_carga():
    logging.info("====== ETAPA 4: CARGA ======")
    inicio = datetime.now()

    crear_tablas()
    limpiar_tablas()

    for nombre, ruta in TABLAS:
        cargar_tabla(nombre, ruta)

    verificar()

    logging.info(f"tiempo total: {datetime.now() - inicio}")
    logging.info("====== FIN ETAPA 4 ======")