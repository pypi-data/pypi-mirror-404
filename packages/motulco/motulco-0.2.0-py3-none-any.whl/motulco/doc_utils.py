import numpy as np
import pandas as pd
import os 
import shutil
from unidecode import unidecode


################################################################################################################################
################################################################################################################################
####################################### Borrar los archivos si existen en la carpeta ###########################################
################################################################################################################################
################################################################################################################################
def BorrrarArchivo(rutaArchivo):  
    if os.path.exists(rutaArchivo):# Verificar si el archivo ya existe
        os.remove(rutaArchivo)

################################################################################################################################
################################################################################################################################
################################# Mueve los archivos descargados a la carpeta que se requiere ##################################
################################################################################################################################
################################################################################################################################
def moverArchivo(RutaOrigen, RutaDestino):
    try:
        shutil.move(RutaOrigen, RutaDestino)
        print(f"El archivo '{RutaOrigen}' se ha movido correctamente a '{RutaDestino}'.")
    except Exception as e:
        print(f"No se pudo mover el archivo '{RutaOrigen}' a '{RutaDestino}': {e}")

################################################################################################################################
################################################################################################################################
############################################### Copia un archivo de un destino a otro ##########################################
################################################################################################################################
################################################################################################################################
def copiarArchivo(RutaOrigen, RutaDestino):
    try:
        shutil.copy2(RutaOrigen, RutaDestino)  # `copy2` copia metadatos (marca de tiempo) además del archivo
        print(f"El archivo '{RutaOrigen}' se ha copiado correctamente a '{RutaDestino}'.")
    except Exception as e:
        print(f"No se pudo copiar el archivo '{RutaOrigen}' a '{RutaDestino}': {e}")

################################################################################################################################
################################################################################################################################
###################################### Obtiene el archivo más reciente de una carpeta ##########################################
################################################################################################################################
################################################################################################################################
def obtenerArchivoMasReciente(rutaCarpeta, formato=".txt"):
    # Obtener la lista de archivos en la carpeta
    archivos_en_carpeta = [archivo for archivo in os.listdir(rutaCarpeta) if archivo.endswith(formato)]
    # Verificar si hay archivos en la carpeta
    if archivos_en_carpeta:
        # Obtener el archivo más reciente basado en la última modificación
        archivo_mas_reciente = max(archivos_en_carpeta,key=lambda x: os.path.getmtime(os.path.join(rutaCarpeta, x)))
        # Obtener la fecha de modificación del archivo más reciente
        fecha_modificacion = os.path.getmtime(os.path.join(rutaCarpeta, archivo_mas_reciente))
        # Retornar nombre y fecha
        return archivo_mas_reciente, fecha_modificacion
    else:
        return None, None

################################################################################################################################
################################################################################################################################
###################################### Retorna la ruta que exista del arreglo de rutas #########################################
################################################################################################################################
################################################################################################################################
def ExisteRuta(arregloDeRutas):
    carpeta_correcta = None
    for carpeta in arregloDeRutas:
        try:
            # Verifica si la ruta existe y es una carpeta
            if os.path.isdir(carpeta):
                print(f"La carpeta existe en: {carpeta}")
                carpeta_correcta = carpeta
                break  # Sale del ciclo si la carpeta existe
        except Exception as e:
            # Maneja otras posibles excepciones (e.g., problemas de permisos)
            print(f"Error al verificar la carpeta {carpeta}: {e}")
            continue
    if carpeta_correcta is None:
        print("La carpeta no se encontró en ninguna de las rutas proporcionadas.")
    else:
        # Aquí puedes continuar con el procesamiento usando la carpeta_correcta
        pass
    return carpeta_correcta

