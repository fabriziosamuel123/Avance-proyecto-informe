
# ==============================================================
# SEMÁFOROS INTELIGENTES - CÓDIGO COMPLETO PARA GOOGLE COLAB
# Proyecto académico - Ingeniería Civil (UTP)
# ==============================================================
# INSTRUCCIONES:
# 1. Copia TODO este código en UNA sola celda de Google Colab.
# 2. Ejecuta la celda.
# 3. Cuando aparezca "Seleccionar archivos", sube tu video MP4.
# 4. El programa procesará el video, mostrará el resultado y lo descargará.
# ==============================================================

# -------------------- 1. LIBRERÍAS --------------------
import cv2
import numpy as np
import os
from IPython.display import display, Video
from google.colab import files
from google.colab.patches import cv2_imshow

print("OpenCV:", cv2.__version__)

# -------------------- 2. CARGAR VIDEO --------------------
print("\nSube el video MP4 que deseas analizar:")
uploaded = files.upload()

if not uploaded:
    raise ValueError("No se cargó ningún archivo.")

VIDEO_IN = next(iter(uploaded))

cap = cv2.VideoCapture(VIDEO_IN)

if not cap.isOpened():
    raise ValueError("No se pudo abrir el video.")

FPS = cap.get(cv2.CAP_PROP_FPS)
if FPS <= 0:
    FPS = 25.0

W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
N = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

print(f"\nVideo cargado correctamente:")
print(f"Resolución: {W} x {H}")
print(f"FPS: {FPS:.2f}")
print(f"Fotogramas: {N}")
print(f"Duración aproximada: {N/FPS:.2f} s")

ok, primer_frame = cap.read()
cap.release()

if not ok:
    raise ValueError("No se pudo leer el primer fotograma del video.")

# -------------------- 3. ZONAS DE DETECCIÓN --------------------
# Coordenadas normalizadas entre 0 y 1.
# Se pueden modificar si las zonas no coinciden con la intersección.
ZONAS = {
    "A": [(0.03, 0.41), (0.38, 0.31), (0.49, 0.41), (0.12, 0.55)],
    "B": [(0.43, 0.22), (0.83, 0.11), (0.97, 0.26), (0.56, 0.39)],
    "C": [(0.04, 0.59), (0.37, 0.49), (0.56, 0.62), (0.16, 0.78)],
    "D": [(0.51, 0.50), (0.93, 0.38), (0.99, 0.53), (0.66, 0.68)]
}

COLORES = {
    "A": (250, 190, 50),
    "B": (90, 210, 250),
    "C": (210, 110, 250),
    "D": (80, 230, 120)
}

def pts_norm(poligono):
    return np.array(
        [(int(x * W), int(y * H)) for x, y in poligono],
        dtype=np.int32
    )

# -------------------- 4. MOSTRAR ZONAS --------------------
vista = primer_frame.copy()

for nombre, poligono in ZONAS.items():
    pts = pts_norm(poligono)
    cv2.polylines(vista, [pts], True, COLORES[nombre], 3)
    x, y = pts[0]
    cv2.putText(
        vista,
        nombre,
        (x, max(30, y - 8)),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        COLORES[nombre],
        3
    )

print("\nVista previa de las cuatro zonas de detección:")
ancho_vista = min(700, W)
alto_vista = int(H * ancho_vista / W)
cv2_imshow(cv2.resize(vista, (ancho_vista, alto_vista)))

# -------------------- 5. TIEMPOS DEL SEMÁFORO --------------------
# Tiempos DEMOSTRATIVOS.
# No representan tiempos normativos para uso real.
VERDE_MIN = 1.5
VERDE_MAX = 3.0
AMARILLO = 0.5
ROJO_TOTAL = 0.25

# -------------------- 6. CONTROLADOR SEMAFÓRICO --------------------
class Controlador:
    def __init__(self):
        self.grupo = "AC"
        self.estado = "VERDE"
        self.inicio = 0.0
        self.proximo = "BD"
        self.verde_obj = VERDE_MIN

    def actualizar(self, tiempo, demanda):
        demanda_ac = demanda["A"] + demanda["C"]
        demanda_bd = demanda["B"] + demanda["D"]

        dt = tiempo - self.inicio

        if self.estado == "VERDE":
            if self.grupo == "AC":
                propia = demanda_ac
                contraria = demanda_bd
            else:
                propia = demanda_bd
                contraria = demanda_ac

            total = propia + contraria

            if total > 0:
                proporcion = propia / total
                self.verde_obj = VERDE_MIN + (VERDE_MAX - VERDE_MIN) * proporcion
            else:
                self.verde_obj = VERDE_MIN

            self.verde_obj = max(VERDE_MIN, min(VERDE_MAX, self.verde_obj))

            if dt >= self.verde_obj:
                self.estado = "AMARILLO"
                self.inicio = tiempo
                self.proximo = "BD" if self.grupo == "AC" else "AC"

        elif self.estado == "AMARILLO":
            if dt >= AMARILLO:
                self.estado = "ROJO_TOTAL"
                self.inicio = tiempo

        elif self.estado == "ROJO_TOTAL":
            if dt >= ROJO_TOTAL:
                self.grupo = self.proximo
                self.estado = "VERDE"
                self.inicio = tiempo

        return self.luces()

    def luces(self):
        salida = {}

        for zona in ZONAS:
            pertenece = zona in self.grupo

            if pertenece and self.estado == "VERDE":
                vehicular = "VERDE"
            elif pertenece and self.estado == "AMARILLO":
                vehicular = "AMARILLO"
            else:
                vehicular = "ROJO"

            # Simulación peatonal:
            # verde únicamente cuando el vehículo está en rojo
            # y no existe transición.
            if vehicular == "ROJO" and self.estado == "VERDE":
                peatonal = "VERDE"
            else:
                peatonal = "ROJO"

            salida[zona] = (vehicular, peatonal)

        return salida

# -------------------- 7. PRUEBA DE SEGURIDAD LÓGICA --------------------
control_prueba = Controlador()

for i in range(500):
    estados = control_prueba.actualizar(
        i / 25.0,
        {"A": 1, "B": 2, "C": 1, "D": 2}
    )

    # A y B nunca deben estar verdes simultáneamente.
    assert not (
        estados["A"][0] == "VERDE" and
        estados["B"][0] == "VERDE"
    )

    # Una misma zona no debe tener vehículo y peatón verdes a la vez.
    for veh, peat in estados.values():
        assert not (veh == "VERDE" and peat == "VERDE")

print("\nPrueba lógica del controlador: CORRECTA")

# -------------------- 8. CONFIGURAR VIDEO DE SALIDA --------------------
VIDEO_OUT = "resultado_semaforos_inteligentes.mp4"

cap = cv2.VideoCapture(VIDEO_IN)

PANEL = 340

fourcc = cv2.VideoWriter_fourcc(*"mp4v")

out = cv2.VideoWriter(
    VIDEO_OUT,
    fourcc,
    FPS,
    (W + PANEL, H)
)

if not out.isOpened():
    raise RuntimeError("No se pudo crear el video de salida.")

# -------------------- 9. DETECTOR DE MOVIMIENTO --------------------
detector_fondo = cv2.createBackgroundSubtractorMOG2(
    history=90,
    varThreshold=40,
    detectShadows=False
)

mascaras = {}

for zona, poligono in ZONAS.items():
    mascara = np.zeros((H, W), dtype=np.uint8)
    cv2.fillPoly(
        mascara,
        [pts_norm(poligono)],
        255
    )
    mascaras[zona] = mascara

kernel = cv2.getStructuringElement(
    cv2.MORPH_ELLIPSE,
    (3, 3)
)

controlador = Controlador()

suavizado = {
    "A": 0.0,
    "B": 0.0,
    "C": 0.0,
    "D": 0.0
}

COLORES_LUZ = {
    "VERDE": (70, 210, 80),
    "AMARILLO": (0, 210, 255),
    "ROJO": (70, 70, 235)
}

historial = []
frame_id = 0

# -------------------- 10. PROCESAR VIDEO --------------------
print("\nProcesando video...")

while True:

    ok, frame = cap.read()

    if not ok:
        break

    # ----- Detección de movimiento -----
    fg = detector_fondo.apply(frame)

    _, fg = cv2.threshold(
        fg,
        220,
        255,
        cv2.THRESH_BINARY
    )

    fg = cv2.morphologyEx(
        fg,
        cv2.MORPH_OPEN,
        kernel,
        iterations=1
    )

    fg = cv2.morphologyEx(
        fg,
        cv2.MORPH_CLOSE,
        kernel,
        iterations=2
    )

    # Ignorar primeros cuadros mientras aprende el fondo.
    cuadros_entrenamiento = min(
        12,
        max(3, int(FPS * 0.4))
    )

    deteccion_valida = frame_id >= cuadros_entrenamiento

    detectados = {}

    # ----- Analizar cada zona -----
    for zona, mascara in mascaras.items():

        region = cv2.bitwise_and(
            fg,
            mascara
        )

        contornos, _ = cv2.findContours(
            region,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        cajas = []

        for contorno in contornos:

            area = cv2.contourArea(contorno)

            if 110 <= area <= 18000:

                x, y, w, h = cv2.boundingRect(contorno)

                if w >= 8 and h >= 8:
                    cajas.append((x, y, w, h))

        cantidad = len(cajas) if deteccion_valida else 0

        # Suavizado temporal para evitar cambios bruscos.
        suavizado[zona] = (
            0.72 * suavizado[zona] +
            0.28 * cantidad
        )

        detectados[zona] = round(
            suavizado[zona],
            1
        )

        # Dibujar cajas detectadas.
        if deteccion_valida:
            for x, y, w, h in cajas:
                cv2.rectangle(
                    frame,
                    (x, y),
                    (x + w, y + h),
                    COLORES[zona],
                    2
                )

        # Dibujar polígono de zona.
        cv2.polylines(
            frame,
            [pts_norm(ZONAS[zona])],
            True,
            COLORES[zona],
            2
        )

        # Etiqueta de zona.
        p = pts_norm(ZONAS[zona])[0]

        cv2.putText(
            frame,
            f"Zona {zona}",
            (int(p[0]), max(25, int(p[1]) - 6)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            COLORES[zona],
            2
        )

    # ----- Control semafórico -----
    tiempo = frame_id / FPS

    luces = controlador.actualizar(
        tiempo,
        detectados
    )

    # -------------------- 11. PANEL LATERAL --------------------
    panel = np.full(
        (H, PANEL, 3),
        (35, 39, 47),
        dtype=np.uint8
    )

    cv2.putText(
        panel,
        "CONTROL INTELIGENTE",
        (12, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.62,
        (255, 255, 255),
        2
    )

    cv2.putText(
        panel,
        f"Tiempo: {tiempo:.1f} s",
        (12, 72),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (220, 220, 220),
        1
    )

    cv2.putText(
        panel,
        f"Grupo activo: {controlador.grupo}",
        (12, 102),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (220, 220, 220),
        1
    )

    cv2.putText(
        panel,
        f"Estado: {controlador.estado}",
        (12, 132),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (220, 220, 220),
        1
    )

    # Mostrar accesos.
    separacion = max(105, int((H - 220) / 4))

    for j, zona in enumerate(["A", "B", "C", "D"]):

        y0 = 175 + j * separacion

        cv2.putText(
            panel,
            f"Acceso {zona}: {detectados[zona]:.1f}",
            (12, y0),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.60,
            COLORES[zona],
            2
        )

        vehicular, peatonal = luces[zona]

        # Luz vehicular
        cv2.circle(
            panel,
            (28, y0 + 32),
            11,
            COLORES_LUZ[vehicular],
            -1
        )

        cv2.putText(
            panel,
            f"Vehiculo: {vehicular}",
            (50, y0 + 39),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.50,
            (245, 245, 245),
            1
        )

        # Luz peatonal
        cv2.circle(
            panel,
            (28, y0 + 63),
            11,
            COLORES_LUZ[peatonal],
            -1
        )

        cv2.putText(
            panel,
            f"Peaton: {peatonal}",
            (50, y0 + 70),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.50,
            (245, 245, 245),
            1
        )

    cv2.putText(
        panel,
        "SIMULACION ACADEMICA",
        (12, H - 42),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.46,
        (190, 190, 255),
        1
    )

    cv2.putText(
        panel,
        "NO USAR EN CONTROL REAL",
        (12, H - 20),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.43,
        (190, 190, 255),
        1
    )

    # Unir video + panel.
    frame_final = np.hstack([
        frame,
        panel
    ])

    out.write(frame_final)

    historial.append({
        "tiempo": tiempo,
        "A": detectados["A"],
        "B": detectados["B"],
        "C": detectados["C"],
        "D": detectados["D"],
        "grupo": controlador.grupo,
        "estado": controlador.estado
    })

    frame_id += 1

# -------------------- 12. CERRAR ARCHIVOS --------------------
cap.release()
out.release()

if frame_id == 0:
    raise RuntimeError("El video no produjo ningún fotograma.")

print("\nProceso terminado correctamente.")
print("Fotogramas procesados:", frame_id)
print("Archivo creado:", VIDEO_OUT)
print("Tamaño:", round(os.path.getsize(VIDEO_OUT) / (1024 * 1024), 2), "MB")

# -------------------- 13. MOSTRAR VIDEO --------------------
print("\nResultado:")
display(
    Video(
        VIDEO_OUT,
        embed=True,
        width=800
    )
)

# -------------------- 14. DESCARGAR RESULTADO --------------------
print("\nDescargando video procesado...")
files.download(VIDEO_OUT)
