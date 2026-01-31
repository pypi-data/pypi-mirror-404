import os, shutil, win32com.client, importlib
import nbformat
from nbconvert.preprocessors import ExecutePreprocessor
from pathlib import Path

################################################################################################################################
################################################################################################################################
################################################# Limpia el Caché ##############################################################
################################################################################################################################
################################################################################################################################
def limpiarCache():
    # Rutas posibles de caché
    paths = [
        os.path.join(os.environ["LOCALAPPDATA"], "Temp", "gen_py"),
        os.path.join(os.path.dirname(win32com.__file__), "gen_py"),
    ]

    for path in paths:
        if os.path.exists(path):
            print(f"Eliminando caché: {path}")
            shutil.rmtree(path, ignore_errors=True)
        else:
            print(f"No existe: {path}")

    # Forzar limpieza interna del gencache
    try:
        win32com.client.gencache.is_readonly = False
        win32com.client.gencache.Rebuild()
        print("🔄 Caché reconstruida.")
    except Exception as e:
        print("⚠️ No se pudo reconstruir automáticamente:", e)

################################################################################################################################
################################################################################################################################
################################################# Ejecuta un ipynb desde otro codigo ###########################################
################################################################################################################################
################################################################################################################################
def ejecutar_notebook(ruta_notebook):
    """
    Ejecuta un notebook Jupyter (.ipynb) en la ruta proporcionada.
    """
    try:
        # Cargar el notebook
        with open(ruta_notebook, 'r', encoding='utf-8') as f:
            notebook = nbformat.read(f, as_version=4)
        
        # Preprocesador para ejecutar el notebook
        ep = ExecutePreprocessor(timeout=600, kernel_name='python3')
        
        # Ejecutar el notebook
        ep.preprocess(notebook, {'metadata': {'path': Path(ruta_notebook).parent}})
        print(f"Notebook ejecutado correctamente: {ruta_notebook}")
    except Exception as e:
        print(f"Error al ejecutar {ruta_notebook}: {e}")
