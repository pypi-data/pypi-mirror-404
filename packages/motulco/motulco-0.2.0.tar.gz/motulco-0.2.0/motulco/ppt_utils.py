
import os
import shutil
from PIL import Image
import pandas as pd


################################################################################################################################
################################################################################################################################
################################################# Abre una diapositiva existente ###############################################
################################################################################################################################
################################################################################################################################
def abrirPresentacion(RutaPpt):
    # --- 1️⃣ Limpiar la caché COM dañada ---
    gen_py_path = os.path.join(os.environ["LOCALAPPDATA"], "Temp", "gen_py")
    if os.path.exists(gen_py_path):
        try:
            shutil.rmtree(gen_py_path, ignore_errors=True)
        except Exception as e:
            print(f"No se pudo eliminar la caché gen_py: {e}")

    # --- 2️⃣ Regenerar caché de COM ---
    import win32com.client.gencache
    win32com.client.gencache.is_readonly = False
    try:
        win32com.client.gencache.Rebuild()
    except Exception:
        pass  # A veces da advertencias inofensivas

    # --- 3️⃣ Crear o usar instancia de PowerPoint ---
    try:
        ppt_app = win32com.client.GetActiveObject("PowerPoint.Application")
    except Exception:
        ppt_app = win32com.client.Dispatch("PowerPoint.Application")

    ppt_app.Visible = True

    # --- 4️⃣ Abrir la presentación plantilla ---
    pres_src = ppt_app.Presentations.Open(RutaPpt)

    return ppt_app, pres_src

################################################################################################################################
################################################################################################################################
################################################# Crea un libro de ppt en blanco ###############################################
################################################################################################################################
################################################################################################################################
def CrearPresentacion(pptDestino):
    import time
    import win32com.client as win32

    try:
        ppt_app = win32.gencache.EnsureDispatch("PowerPoint.Application")
    except Exception:
        # Si falla, limpia la caché y usa Dispatch
        import os, shutil
        gen_py_path = os.path.join(os.environ["LOCALAPPDATA"], "Temp", "gen_py")
        shutil.rmtree(gen_py_path, ignore_errors=True)
        ppt_app = win32.Dispatch("PowerPoint.Application")

    ppt_app.Visible = True
    pres_dst = ppt_app.Presentations.Add()
    pres_dst.SaveAs(pptDestino)
    time.sleep(1)
    return ppt_app, pres_dst

################################################################################################################################
################################################################################################################################
################################################# Copia diapositivas entre ppt's ###############################################
################################################################################################################################
################################################################################################################################
def copiarDiaposPosicion(pres_src, pres_dst, posicionesCopiar):
    # ✅ Ajustar tamaño de página igual al origen
    pres_dst.PageSetup.SlideWidth = pres_src.PageSetup.SlideWidth
    pres_dst.PageSetup.SlideHeight = pres_src.PageSetup.SlideHeight

    for pos in posicionesCopiar:
        pres_src.Slides(pos + 1).Copy()  # Copiar (recordar que es base 1)
        pres_dst.Slides.Paste()  # Pegar manteniendo formato

    #pres_dst.Save()  # ✅ Guardar cambios

################################################################################################################################
################################################################################################################################
######################################################## Guarda una presentacion ###############################################
################################################################################################################################
################################################################################################################################
def guardarPpt(pres_dst):
    pres_dst.Save()


################################################################################################################################
################################################################################################################################
#################################### Obtienene la ultima posicion Vertical de la ppt ###########################################
################################################################################################################################
################################################################################################################################
def getNextY(slide, padding=5):
    """ Calcula la siguiente posición disponible en Y dentro de una diapositiva """
    max_y = 0
    for shape in slide.Shapes:
        bottom = shape.Top + shape.Height
        if bottom > max_y:
            max_y = bottom
    return max_y + padding

################################################################################################################################
################################################################################################################################
########################################## Obtienene la cantidad de slides en la ppt ###########################################
################################################################################################################################
################################################################################################################################
def obtenerDiapositivaMaxima(presentacion):
    try:
        return presentacion.Slides.Count
    except:
        return None



################################################################################################################################
################################################################################################################################
################################################# Agregar Elemento (shape) a una ppt ###########################################
################################################################################################################################
################################################################################################################################
def agregarElemento(pres_dst, pres_src, num_slide, tipo, contenido, x=50, y="auto",
                     ancho=300, alto=100, font_size=20,
                     font_name="Arial", bold=False, italic=False,
                     color=(0, 0, 0), align="left",
                     crop_top=0, crop_bottom=0, crop_left=0, crop_right=0,
                     auto_crop=False, mantener_relacion=True, mantener_relacion_base="ancho",
                     paddingSet=5, rotacion=0):
    """
    Inserta texto o imagen en una diapositiva de PowerPoint.
    Ahora incluye rotación para imágenes vía rotacion=grados.
    """
    puntosACentimetros=28.3465
    slide = pres_dst.Slides(num_slide)
    slide_width = pres_dst.PageSetup.SlideWidth
    slide_height = pres_dst.PageSetup.SlideHeight

    # ======== Calcular Y inicial ========
    if y == "auto":
        y = getNextY(slide, paddingSet) - crop_top * puntosACentimetros * 6

    # ======== Auto crop ========
    if auto_crop:
        crop_top = 0.05
        crop_bottom = 0.05
        crop_left = 0.03
        crop_right = 0.03

    # ======== Mantener relación si es imagen ========
    if tipo == "imagen" and mantener_relacion:
        try:
            with Image.open(contenido) as img:
                width_orig, height_orig = img.size
                aspect_ratio = width_orig / height_orig

            if mantener_relacion_base == "ancho":
                # Ajustar alto usando el ancho como referencia
                alto = ancho / aspect_ratio

            elif mantener_relacion_base == "alto":
                # Ajustar ancho usando el alto como referencia
                ancho = alto * aspect_ratio

            else:
                print(f"⚠️ Opción inválida en mantener_relacion_base: {mantener_relacion_base}")

        except Exception as e:
            print(f"⚠️ No se pudo calcular proporción de imagen: {e}")


    # ======== Calcular alto visible ========
    alto_visible = alto * (1 - crop_top - crop_bottom)

    # ======== Verificar si cabe ========
    if y + alto_visible > slide_height:
        copiarDiaposPosicion(pres_src, pres_dst, [0])
        num_slide += 1
        slide = pres_dst.Slides(num_slide)
        y = getNextY(slide, paddingSet) - crop_top * puntosACentimetros * 6

    # ======== Convertir color HEX a RGB ========
    if isinstance(color, str):
        color = hex_to_rgb(color)

    # ======== TEXTO / TÍTULO ========
    if tipo in ["texto", "titulo"]:
        textbox = slide.Shapes.AddTextbox(1, x if x != "center" else 50, y, ancho, alto)
        text_range = textbox.TextFrame.TextRange
        text_range.Text = contenido
        text_range.Font.Name = font_name
        text_range.Font.Size = font_size
        text_range.Font.Bold = -1 if bold else 0
        text_range.Font.Italic = -1 if italic else 0
        text_range.Font.Color.RGB = color[0] + (color[1] << 8) + (color[2] << 16)

        if align == "center":
            textbox.TextFrame.TextRange.ParagraphFormat.Alignment = 2
        elif align == "right":
            textbox.TextFrame.TextRange.ParagraphFormat.Alignment = 3
        elif align == "justify":
            textbox.TextFrame.TextRange.ParagraphFormat.Alignment = 4
        else:
            textbox.TextFrame.TextRange.ParagraphFormat.Alignment = 1

        if tipo == "titulo":
            text_range.Font.Bold = -1

            # ⭐ Aplicar rotación a texto
        try:
            textbox.Rotation = float(rotacion)
        except:
            print(f"⚠️ No se pudo aplicar rotación a texto: {rotacion}")

        return textbox

    # ======== IMAGEN ========
    elif tipo == "imagen":
        shape = slide.Shapes.AddPicture(
            contenido, LinkToFile=False, SaveWithDocument=True,
            Left=0, Top=y, Width=ancho, Height=alto
        )

        shape.LockAspectRatio = mantener_relacion

        # --- Aplicar recortes ---
        shape.PictureFormat.CropTop = crop_top * shape.Height
        shape.PictureFormat.CropBottom = crop_bottom * shape.Height
        shape.PictureFormat.CropLeft = crop_left * shape.Width
        shape.PictureFormat.CropRight = crop_right * shape.Width

        # --- Centrar horizontalmente ---
        if isinstance(x, str) and x.lower() in ["center", "x_center"]:
            ancho_real = shape.Width
            shape.Left = (slide_width - ancho_real) / 2
        else:
            shape.Left = x

        # --- ⭐ APLICAR ROTACIÓN ⭐ ---
        try:
            shape.Rotation = float(rotacion)
        except:
            print(f"⚠️ No se pudo aplicar rotación: {rotacion}")

        return shape


################################################################################################################################
################################################################################################################################
################################################# Agregar Elemento (shape) a una ppt ###########################################
################################################################################################################################
################################################################################################################################
def AgregarElementoConindicador(Indicador, tipo,df_Control,PresDest,PresSrc,contenidoAdicional):
    puntosACentimetros=28.3465
    if df_Control.at[Indicador, 'INSERTAR SLIDE']:
        copiarDiaposPosicion(PresSrc, PresDest, [0])
    
    if contenidoAdicional =="" and tipo != "imagen": 
        contenidoFinal=df_Control.at[Indicador, 'CONTENIDO'] 
    elif contenidoAdicional !="" and tipo != "imagen":
        if pd.isna(df_Control.at[Indicador, 'CONTENIDO']) or str(df_Control.at[Indicador, 'CONTENIDO']).strip().lower() in ["nan", "none", ""]:
            contenidoFinal=f"{contenidoAdicional}"
        else:
            contenidoFinal=df_Control.at[Indicador, 'CONTENIDO'] + f" {contenidoAdicional}" 
            
    if tipo == "imagen":
        agregarElemento(pres_dst=PresDest,pres_src=PresSrc,num_slide = PresDest.Slides.Count ,tipo= df_Control.at[Indicador, 'TIPO'],
                          contenido=os.path.abspath(df_Control.at[Indicador, 'CONTENIDO']) ,x=convertirPuntosACentimetros(df_Control.at[Indicador, 'POSICION X']),
                            y=convertirPuntosACentimetros(df_Control.at[Indicador, 'POSICION Y']) ,ancho=df_Control.at[Indicador, 'ANCHO'] * puntosACentimetros,
                            alto=df_Control.at[Indicador, 'ALTO'] * puntosACentimetros ,font_size=df_Control.at[Indicador, 'TAMANIO FUENTE'],
                            font_name=df_Control.at[Indicador, 'TIPO FUENTE'] ,bold=df_Control.at[Indicador, 'NEGRITA'], italic=df_Control.at[Indicador, 'CURSIVA']
                            ,color=df_Control.at[Indicador, 'COLOR'], align=df_Control.at[Indicador, 'ALINEACION'] ,crop_top=df_Control.at[Indicador, 'CORTE SUPERIOR']
                            ,crop_bottom=df_Control.at[Indicador, 'CORTE INFERIOR'] ,crop_left=df_Control.at[Indicador, 'CORTE IZQUIERDA'],
                            crop_right=df_Control.at[Indicador, 'CORTE DERECHA'] ,auto_crop=df_Control.at[Indicador, 'AUTO CORTE']
                            ,mantener_relacion=df_Control.at[Indicador, 'RELACION ASPECTO'],paddingSet=df_Control.at[Indicador, 'PADDING'],
                            rotacion=df_Control.at[Indicador, 'ROTACION'],mantener_relacion_base=df_Control.at[Indicador, 'BASE RELACION ASPECTO'])
    else:
        agregarElemento(pres_dst=PresDest,pres_src=PresSrc,num_slide = PresDest.Slides.Count ,tipo= df_Control.at[Indicador, 'TIPO'],
                         contenido=contenidoFinal ,x=convertirPuntosACentimetros(df_Control.at[Indicador, 'POSICION X']), y=convertirPuntosACentimetros(df_Control.at[Indicador, 'POSICION Y']),
                         ancho=df_Control.at[Indicador, 'ANCHO'] * puntosACentimetros, alto=df_Control.at[Indicador, 'ALTO'] * puntosACentimetros,
                         font_size=df_Control.at[Indicador, 'TAMANIO FUENTE'], font_name=df_Control.at[Indicador, 'TIPO FUENTE'] ,bold=df_Control.at[Indicador, 'NEGRITA'],
                         italic=df_Control.at[Indicador, 'CURSIVA'] ,color=df_Control.at[Indicador, 'COLOR'], align=df_Control.at[Indicador, 'ALINEACION'],
                         crop_top=df_Control.at[Indicador, 'CORTE SUPERIOR'], crop_bottom=df_Control.at[Indicador, 'CORTE INFERIOR'],
                         crop_left=df_Control.at[Indicador, 'CORTE IZQUIERDA'], crop_right=df_Control.at[Indicador, 'CORTE DERECHA'],
                         auto_crop=df_Control.at[Indicador, 'AUTO CORTE'], mantener_relacion=df_Control.at[Indicador, 'RELACION ASPECTO'],
                         paddingSet=df_Control.at[Indicador, 'PADDING'],rotacion=df_Control.at[Indicador, 'ROTACION'])

################################################################################################################################
################################################################################################################################
################################################# Convierte de puntos a centimetros ############################################
################################################################################################################################
################################################################################################################################
def convertirPuntosACentimetros(value):
    puntosACentimetros=28.3465
    try:
        return (float(value) * puntosACentimetros)
    except (ValueError, TypeError):
        return str(value)
    
################################################################################################################################
################################################################################################################################
####################################################### Convierte de HEX a RGB #################################################
################################################################################################################################
################################################################################################################################
def hex_to_rgb(hex_color):
    """Convierte color hex (#RRGGBB) a tupla RGB (R,G,B)"""
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))