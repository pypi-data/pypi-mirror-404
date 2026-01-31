import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os
from html2image import Html2Image
from PIL import Image
from PIL import ImageChops


################################################################################################################################
################################################################################################################################
########################################## Generacion de graficos de Barras y Lineas ###########################################
################################################################################################################################
################################################################################################################################

def graficoBarrasYLineas(meses, InfoBarras=None, InfoLineas=None,
                                 coloresBarras=["#19BDE6", "#152C47", "#BACF00"],
                                 titulo="", ruta_salida="grafico.png", mostrar_tabla=True,
                                 ancho_figura=14, alto_figura=6, labelLineas="Resultado Real",
                                 colorLinea="#A461AB", AnchoGrafica=0.8, desplazamientoLeyenda=-0.25,
                                 BarrasPorcentaje=False, LineasPorcentaje=False,
                                 cantidadDecimBarras="0", cantidadDecimLineas="0"):

    x = np.arange(len(meses))
    fig, ax1 = plt.subplots(figsize=(ancho_figura, alto_figura))

    # Decidir si deben compartir eje (cuando ambos tienen mismo tipo: ambos % o ambos absolutos)
    share_axis = (BarrasPorcentaje == LineasPorcentaje)

    # --- METAS (barras) ---
    handles1, labels1 = [], []
    if InfoBarras is not None and len(InfoBarras) > 0:
        width = AnchoGrafica / len(InfoBarras) if len(InfoBarras) > 0 else AnchoGrafica
        for i, (meta_name, valores_raw) in enumerate(InfoBarras.items()):
            # Asegurarse que sean floats
            valores = [float(v) for v in valores_raw]

            # Multiplicar por 100 para graficar si es porcentaje
            plot_vals = [v * 100 for v in valores] if BarrasPorcentaje else valores

            ax1.bar(
                x + (i - len(InfoBarras) / 2) * width + width / 2,
                plot_vals,
                width,
                label=meta_name,
                color=coloresBarras[i % len(coloresBarras)]
            )
        handles1, labels1 = ax1.get_legend_handles_labels()

    # --- RESULTADOS REALES (líneas) ---
    handles2, labels2 = [], []
    eje_leyenda = ax1  # por defecto

    if InfoLineas is not None and len(InfoLineas) > 0:
        # decidir ax2: si comparten eje -> ax2 = ax1; si no -> crear twin sólo si hace falta
        if share_axis:
            ax2 = ax1
        else:
            # si las lineas están en porcentaje pero las barras no, o viceversa, usar twin
            ax2 = ax1.twinx() if LineasPorcentaje else ax1

        if isinstance(InfoLineas, pd.DataFrame):
            num_lineas = InfoLineas.shape[1]
            labels = labelLineas if isinstance(labelLineas, list) else InfoLineas.columns.tolist()
            colores = colorLinea if isinstance(colorLinea, list) else [colorLinea] * num_lineas

            for i, col in enumerate(InfoLineas.columns):
                vals_raw = InfoLineas[col].astype(float).values
                vals = [float(v) for v in vals_raw]

                # Multiplicar por 100 si es porcentaje
                if LineasPorcentaje:
                    vals = [v * 100 for v in vals]

                ax2.plot(x, vals, marker="o", linewidth=2, color=colores[i % len(colores)], label=labels[i])

                # Etiquetas de los puntos
                max_val = max(vals) if len(vals) > 0 else 0.0
                for j, val in enumerate(vals):
                    ax2.text(
                        x[j], val + max_val * 0.03,
                        f"{val:.{cantidadDecimLineas}f}%" if LineasPorcentaje else f"{val:.{cantidadDecimLineas}f}",
                        ha="center", fontsize=10, color="white",
                        bbox=dict(facecolor=colores[i % len(colores)], edgecolor="none", boxstyle="round,pad=0.25")
                    )
            eje_leyenda = ax2

        else:
            # Caso 1 sola lista
            vals = [float(v) for v in InfoLineas]

            if LineasPorcentaje:
                vals = [v * 100 for v in vals]
            ax2.plot(x, vals, marker="o", linewidth=2, color=colorLinea,
                     label=labelLineas if isinstance(labelLineas, str) else labelLineas[0])

            max_val = max(vals) if len(vals) > 0 else 0.0
            for i, val in enumerate(vals):
                ax2.text(
                    x[i], val + max_val * 0.03,
                    f"{val:.{cantidadDecimLineas}f}%" if LineasPorcentaje else f"{val:.{cantidadDecimLineas}f}",
                    ha="center", fontsize=8, color="white",
                    bbox=dict(facecolor=colorLinea if isinstance(colorLinea, str) else colorLinea[0],
                              edgecolor="none", boxstyle="round,pad=0.25")
                )
            eje_leyenda = ax2

        # Combinar leyendas
        handles2, labels2 = eje_leyenda.get_legend_handles_labels()
        labels_final, handles_final = [], []
        for h, l in zip(handles1 + handles2, labels1 + labels2):
            if l not in labels_final:
                labels_final.append(l)
                handles_final.append(h)

        # --- TÍTULO ---
        plt.title(titulo, fontsize=13, pad=25)

    # --- LEYENDA ---
    handles_final, labels_final = [], []

    if 'handles1' in locals():
        handles_final += handles1
        labels_final += labels1
    if 'handles2' in locals():
        handles_final += handles2
        labels_final += labels2

    if handles_final:
        plt.legend(handles_final, labels_final,
                loc="upper center", bbox_to_anchor=(0.5, desplazamientoLeyenda),
                ncol=4, fontsize=8, frameon=False)


    # --- AJUSTAR ESCALAS ---
    # Si comparten eje (ambos % o ambos absolutos) forzar mismos límites
    if InfoLineas is not None:
        if share_axis:
            # obtener límites actuales (si ax2 es el mismo que ax1 esto es redundante pero seguro)
            try:
                # si existe ax2 y es distinto a ax1 (por seguridad), considerar ambos
                if 'ax2' in locals() and ax2 is not ax1:
                    min_y = min(ax1.get_ylim()[0], ax2.get_ylim()[0])
                    max_y = max(ax1.get_ylim()[1], ax2.get_ylim()[1])
                else:
                    min_y, max_y = ax1.get_ylim()
                ax1.set_ylim(min_y, max_y)
                if 'ax2' in locals() and ax2 is not ax1:
                    ax2.set_ylim(min_y, max_y)
            except Exception:
                pass  # si falla por algún motivo, no detener el plotting

    # --- QUITAR EJES ---
    ax1.axis("off")
    if 'ax2' in locals() and (ax2 is not ax1) and InfoLineas is not None and LineasPorcentaje:
        ax2.axis("off")

    # --- TABLA ---
    if mostrar_tabla and (InfoBarras is not None or InfoLineas is not None):
        tabla_data = []
        row_labels = []

        # Barras
        if InfoBarras is not None:
            for fila_raw in InfoBarras.values():
                fila = [float(v) for v in fila_raw]
                fila_formateada = [
                    f"{val * 100:,.{cantidadDecimBarras}f}%" if BarrasPorcentaje else f"{val:,.{cantidadDecimBarras}f}"
                    for val in fila
                ]
                tabla_data.append(fila_formateada)
            row_labels += list(InfoBarras.keys())

        # Líneas
        if InfoLineas is not None:
            if isinstance(InfoLineas, pd.DataFrame):
                for i, col in enumerate(InfoLineas.columns):
                    vals = InfoLineas[col].astype(float).values
                    if LineasPorcentaje:
                        vals = [v * 100 for v in vals]
                        fila_resultado = [f"{v:,.{cantidadDecimLineas}f}%" for v in vals]
                    else:
                        fila_resultado = [f"{v:,.{cantidadDecimLineas}f}" for v in vals]
                    tabla_data.append(fila_resultado)
                row_labels += (labelLineas if isinstance(labelLineas, list) else InfoLineas.columns.tolist())
            else:
                vals = [float(v) for v in InfoLineas]
                if LineasPorcentaje:
                    vals = [v * 100 for v in vals]
                    fila_resultado = [f"{v:,.{cantidadDecimLineas}f}%" for v in vals]
                else:
                    fila_resultado = [f"{v:,.{cantidadDecimLineas}f}" for v in vals]
                tabla_data.append(fila_resultado)
                row_labels.append(labelLineas if isinstance(labelLineas, str) else labelLineas[0])

        # Crear tabla
        tabla = plt.table(cellText=tabla_data, rowLabels=row_labels, colLabels=meses,
                          cellLoc="center", loc="bottom")
        tabla.auto_set_font_size(False)
        tabla.set_fontsize(10) # Mas tamaño
        tabla.scale(1, 1.5) #Ancho y alto 
        plt.subplots_adjust(left=0.05, bottom=0.30, top=0.80)

    # --- GUARDAR ---
    plt.tight_layout()
    plt.savefig(ruta_salida.replace(".png", ".svg"), format="svg", bbox_inches="tight")
    plt.close()



################################################################################################################################
################################################################################################################################
######################################################## Generacion de tablas  #################################################
################################################################################################################################
################################################################################################################################

def generar_tabla(
df,tendenciasPorColumna=None,mostrarFlechas=True,separador_miles=False,color_encabezado="#0a4d8c",color_texto_encabezado="#ffffff",
color_fondo="#ffffff",color_borde="#cccccc",ruta_imagen=None,ajusteColumnas=0,ajusteTexto=0,anchoPrimeraColumna=160,
anchoOtrasColumnas=90,resaltarUltimaFila=True,negritaUltimaFila=True,colores_celdas=None  # 🆕 NUEVO
):
    df = df.copy()

    # 1) Tendencias
    tendencias_calculadas = {}
    if tendenciasPorColumna is not None:
        for col, modo in tendenciasPorColumna.items():
            if modo == "auto":
                tendencias_calculadas[col] = df[col].apply(
                    lambda x: "subió" if x > 0 else ("bajó" if x < 0 else "mantuvo")
                )
            elif isinstance(modo, list):
                tendencias_calculadas[col] = modo

    # 2) Formato de valores
    def aplicar_formato(valor, col):
        if pd.isna(valor):
            return ""
        if isinstance(valor, bool):
            return "<span style='color:green; font-weight:bold; font-size:18px;'>✅</span>" if valor else "<span style='color:red; font-weight:bold; font-size:18px;'>❌</span>"
        elif mostrarFlechas and col in tendencias_calculadas:
            idx = df.index[df[col] == valor][0]
            tendencia = tendencias_calculadas[col][idx]
            if tendencia == "subió":
                return f"<span style='color:green;'>▲ {valor:.1f}%</span>"
            elif tendencia == "bajó":
                return f"<span style='color:red;'>▼ {valor:.1f}%</span>"
            else:
                return f"<span style='color:gray;'>• {valor:.1f}%</span>"
        elif isinstance(valor, (int, float)) and "%" in col:
            return f"{valor:.1f}%"
        elif separador_miles and isinstance(valor, (int, float)):
            return (
                f"{valor:,.0f}".replace(",", ".")
                if abs(valor) >= 1000
                else (f"{valor:.1f}" if valor != int(valor) else f"{int(valor)}")
            )
        elif isinstance(valor, (int, float)):
            return f"{valor:.1f}"
        else:
            return valor

    for col in df.columns:
        df[col] = df[col].apply(lambda x: aplicar_formato(x, col))

    # 3) Estilos base
    font_size_base = 14 + ajusteTexto
    ultima_fila_bg = "#f2f2f2" if resaltarUltimaFila else color_fondo
    ultima_fila_fw = "bold" if negritaUltimaFila else "normal"

    estilos = f"""
    <style>
        html, body {{
            margin: 0;
            padding: 0;
            background: transparent;
        }}
        .tabla-tiv {{
            border-collapse: collapse;
            font-family: Arial, sans-serif;
            font-size: {font_size_base}px;
            color: #000000;
            background-color: {color_fondo};
            table-layout: fixed;
            margin: 0;
        }}
        .tabla-tiv th, .tabla-tiv td {{
            border: 1px solid {color_borde};
            padding: 6px;
            text-align: center;
            vertical-align: middle;
            word-wrap: break-word;
            box-sizing: border-box;
        }}
        .tabla-tiv th {{
            background-color: {color_encabezado};
            color: {color_texto_encabezado};
            font-weight: bold;
        }}
        .tabla-tiv tr:last-child td {{
            background-color: {ultima_fila_bg};
            font-weight: {ultima_fila_fw};
        }}
        .tabla-tiv th:first-child, .tabla-tiv td:first-child {{
            width: {anchoPrimeraColumna + ajusteColumnas}px;
            text-align: left;
            padding-left: 10px;
        }}
        .tabla-tiv th:not(:first-child), .tabla-tiv td:not(:first-child) {{
            width: {anchoOtrasColumnas + ajusteColumnas}px;
        }}
    </style>
    """

    html_tabla = estilos + df.to_html(index=False, escape=False, classes="tabla-tiv")

    # 🎨 NUEVO: Colores por celda (acepta lista o DataFrame)
    if colores_celdas is not None:

        if isinstance(colores_celdas, pd.DataFrame):
            matriz = colores_celdas.values.tolist()
        else:
            matriz = colores_celdas

        filas, columnas = df.shape

        if len(matriz) != filas or any(len(fila) != columnas for fila in matriz):
            raise ValueError("colores_celdas debe tener exactamente las mismas dimensiones que df")

        estilos_celdas = "<style>\n"
        for i in range(filas):
            for j in range(columnas):
                color = matriz[i][j]
                if color:
                    estilos_celdas += f"""
                    .tabla-tiv tbody tr:nth-child({i+1}) td:nth-child({j+1}) {{
                        background-color: {color} !important;
                    }}
                    """
        estilos_celdas += "</style>\n"

        html_tabla = estilos_celdas + html_tabla

    # 4) Captura imagen
    if ruta_imagen:
        os.makedirs(os.path.dirname(ruta_imagen), exist_ok=True)
        hti = Html2Image(output_path=os.path.dirname(ruta_imagen))
        hti.browser.flags = [
            "--hide-scrollbars",
            "--no-sandbox",
            "--disable-gpu",
            "--force-device-scale-factor=1"
        ]
        hti.screenshot(
            html_str=html_tabla,
            save_as=os.path.basename(ruta_imagen)
        )

    return html_tabla


################################################################################################################################
################################################################################################################################
################################################# Recortar los bordes blancos  #################################################
################################################################################################################################
################################################################################################################################

def recortar_espacios_blancos(ruta_entrada, ruta_salida=None):
    img = Image.open(ruta_entrada)
    # Convertir la imagen a modo que permita detectar el fondo
    img_sin_alpha = img.convert("RGB")
    # Crear una imagen en blanco del mismo tamaño
    fondo = Image.new("RGB", img_sin_alpha.size, (255, 255, 255))
    # Calcular diferencia
    diff = Image.eval(ImageChops.difference(img_sin_alpha, fondo), lambda x: 255 if x else 0)
    bbox = diff.getbbox()  # Encuentra el área sin blanco
    if bbox:
        img_recortada = img.crop(bbox)
        if ruta_salida:
            img_recortada.save(ruta_salida)
        return img_recortada
    return img


################################################################################################################################
################################################################################################################################
######################################################### Girar una imagen  ####################################################
################################################################################################################################
################################################################################################################################

def rotar_imagen_python(ruta_imagen, grados, ruta_salida=None):
    """
    Rota una imagen directamente en Python usando PIL.
    Retorna la ruta de la imagen rotada.
    """
    try:
        img = Image.open(ruta_imagen)
        img_rotada = img.rotate(grados, expand=True)  # expand evita recortes

        if ruta_salida is None:
            # genera nombre temporal
            ruta_salida = ruta_imagen.replace(".", f"_rotada_{grados}.")

        img_rotada.save(ruta_salida)
        return ruta_salida

    except Exception as e:
        print(f"Error rotando la imagen: {e}")
        return ruta_imagen
