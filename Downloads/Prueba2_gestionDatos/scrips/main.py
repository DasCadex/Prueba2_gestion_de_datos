import os
import sys
import logging
from datetime import datetime

# apunta a la raíz del proyecto
os.chdir(os.path.dirname(os.path.abspath(__file__)) + "/..")
sys.path.insert(0, os.getcwd())  # ← agrega la raíz al path de Python

os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/main.log"),
        logging.StreamHandler()
    ]
)

if __name__ == "__main__":
    inicio = datetime.now()

    logging.info("╔══════════════════════════════════════╗")
    logging.info("║   INICIO PIPELINE - ECOMMERCE        ║")
    logging.info("╚══════════════════════════════════════╝")

    logging.info(">>> ETAPA 1: INGESTA")
    try:
        from scrips.ingesta import ejecutar_ingesta
        ejecutar_ingesta()
        logging.info("✓ Ingesta completada")
    except Exception as e:
        logging.error(f"✗ Error en ingesta: {e}")
        raise

    logging.info(">>> ETAPA 2: LIMPIEZA")
    try:
        from scrips.limpieza import ejecutar_limpieza
        ejecutar_limpieza()
        logging.info("✓ Limpieza completada")
    except Exception as e:
        logging.error(f"✗ Error en limpieza: {e}")
        raise

    logging.info(">>> ETAPA 3: VALIDACIÓN")
    try:
        from scrips.validacion import ejecutar_validacion
        ejecutar_validacion()
        logging.info("✓ Validación completada")
    except Exception as e:
        logging.error(f"✗ Error en validación: {e}")
        raise

    logging.info(">>> ETAPA 4: CARGA A BASE DE DATOS")
    try:
        from scrips.carga_datos import ejecutar_carga
        ejecutar_carga()
        logging.info("✓ Carga completada")
    except Exception as e:
        logging.error(f"✗ Error en carga: {e}")
        raise

    logging.info(f"Tiempo total: {datetime.now() - inicio}")
    logging.info("╔══════════════════════════════════════╗")
    logging.info("║   PIPELINE COMPLETADO CON ÉXITO ✓    ║")
    logging.info("╚══════════════════════════════════════╝")