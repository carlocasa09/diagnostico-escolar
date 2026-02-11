import streamlit as st
import pandas as pd
import json
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from groq import Groq

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Sistema de Diagnóstico Pedagógico", page_icon="🎓", layout="centered")

# --- ESTILOS CSS PERSONALIZADOS (LETRAS MÁS OSCURAS Y LEGIBLES) ---
st.markdown("""
    <style>
    .main {
        background-color: #f0f2f6;
    }
    .block-container {
        padding-top: 2rem;
        max-width: 800px;
    }
    .header-container {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        padding: 30px;
        border-radius: 20px;
        color: white;
        text-align: center;
        margin-bottom: 30px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }
    /* Tarjeta de pregunta con texto bien oscuro */
    .question-card {
        background-color: white;
        padding: 30px;
        border-radius: 15px;
        border-left: 10px solid #1e3a8a;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 25px;
    }
    .question-card h3 {
        color: #111827 !important; /* Negro casi puro */
        font-weight: 800 !important;
        line-height: 1.4;
    }
    /* Estilo para las opciones del Radio Button */
    .stRadio div[role="radiogroup"] label {
        color: #111827 !important; /* Letras de opciones negras */
        font-weight: 600 !important;
        font-size: 1.1rem !important;
    }
    .stButton>button {
        width: 100%;
        border-radius: 12px;
        height: 3.5em;
        background-color: #1e3a8a;
        color: white;
        font-weight: bold;
        border: none;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #1d4ed8;
        transform: translateY(-2px);
    }
    </style>
    """, unsafe_allow_html=True)

# --- CONFIGURACIÓN DE SEGURIDAD (SECRETS) ---
try:
    GROQ_API_KEY = st.secrets["GROQ_KEY"]
    MI_PASSWORD = st.secrets["EMAIL_KEY"]
except:
    st.error("⚠️ Error de configuración: No se encontraron las claves en los Secrets de Streamlit.")
    st.stop()

client = Groq(api_key=GROQ_API_KEY)
MODELO_IA = "llama-3.1-8b-instant"
MI_CORREO = "carlocasa09@gmail.com" 

# --- 2. FUNCIÓN PARA ENVIAR CORREO ---
def enviar_informe_docente(nombre_alumno, analisis_pedagogico, reporte_tabla):
    msg = MIMEMultipart()
    msg['From'] = MI_CORREO
    msg['To'] = MI_CORREO
    msg['Subject'] = f"📊 INFORME TÉCNICO: {nombre_alumno}"

    cuerpo = f"""
    INFORME DE EVALUACIÓN PEDAGÓGICA
    ---------------------------------
    Estudiante: {nombre_alumno}
    Materia: {st.session_state.datos_alumno.get('mat', 'N/A')}
    Fecha: {time.strftime("%d/%m/%Y")}
    
    ANÁLISIS DEL ESPECIALISTA:
    {analisis_pedagogico}
    
    DETALLE DE RESPUESTAS:
    {reporte_tabla.to_string(index=False)}
    
    Puntaje: {st.session_state.puntos}/100
    """
    msg.attach(MIMEText(cuerpo, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(MI_CORREO, MI_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Error al enviar el correo: {e}")
        return False

# --- 3. ESTADO DE SESIÓN ---
keys = ['paso_global', 'puntos', 'lote_preguntas', 'indice_lote', 'finalizado', 
        'reporte', 'datos_alumno', 'empezar', 'respondido', 'correo_enviado']
for key in keys:
    if key not in st.session_state:
        if key == 'paso_global': st.session_state[key] = 1
        elif key in ['puntos', 'indice_lote']: st.session_state[key] = 0
        elif key in ['lote_preguntas', 'reporte']: st.session_state[key] = []
        elif key in ['finalizado', 'empezar', 'respondido', 'correo_enviado']: st.session_state[key] = False
        else: st.session_state[key] = {}

# --- 4. CARGA DE PREGUNTAS (GROQ) ---
def cargar_lote_diagnostico(materia, grado, tema):
    prompt = (f"Genera 5 preguntas de selección múltiple sobre {tema} para {grado} en {materia}. "
              "Responde ÚNICAMENTE JSON: {\"preguntas\": [{\"p\":\"?\",\"a\":\"\",\"b\":\"\",\"c\":\"\",\"d\":\"\",\"r\":\"LETRA\",\"nivel\":\"\"}]}")
    try:
        completion = client.chat.completions.create(model=MODELO_IA, messages=[{"role": "user", "content": prompt}], response_format={"type": "json_object"})
        return json.loads(completion.choices[0].message.content).get("preguntas", [])
    except: return None

# --- 5. INTERFAZ DE REGISTRO ---
if not st.session_state.empezar:
    st.markdown("""
        <div class="header-container">
            <h1>🔬 Aula Virtual de Diagnóstico</h1>
            <p>Evaluación de Ciencias e Ingeniería</p>
        </div>
    """, unsafe_allow_html=True)
    
    with st.container():
        st.info("👋 Ingresa tus datos para comenzar.")
        with st.form("registro"):
            nom = st.text_input("Nombre y Apellido del Estudiante:")
            col1, col2 = st.columns(2)
            gra = col1.selectbox("Grado:", ["7mo Grado", "8vo Grado", "9no Grado", "4to Año", "5to Año"])
            mat = col2.selectbox("Materia:", ["Matemáticas", "Química", "Física"])
            tema = st.text_input("Tema de la evaluación (Ej: MCU - Movimiento Circular):")
            
            if st.form_submit_button("Iniciar Evaluación 🚀"):
                if nom and tema:
                    st.session_state.datos_alumno = {"nom": nom, "gra": gra, "mat": mat, "tem": tema}
                    st.session_state.empezar = True
                    st.rerun()
                else:
                    st.warning("⚠️ Completa todos los campos.")

# --- 6. PANTALLA DE EXAMEN ---
elif st.session_state.empezar and not st.session_state.finalizado:
    if not st.session_state.lote_preguntas:
        with st.spinner("✨ Generando preguntas..."):
            nuevo = cargar_lote_diagnostico(st.session_state.datos_alumno['mat'], st.session_state.datos_alumno['gra'], st.session_state.datos_alumno['tem'])
            if nuevo: st.session_state.lote_preguntas = nuevo; st.session_state.indice_lote = 0; st.rerun()

    if st.session_state.lote_preguntas:
        st.progress(st.session_state.paso_global / 10)
        st.write(f"**Pregunta {st.session_state.paso_global} de 10**")

        preg = st.session_state.lote_preguntas[st.session_state.indice_lote]
        
        st.markdown(f"""
            <div class="question-card">
                <h3>{preg['p']}</h3>
            </div>
        """, unsafe_allow_html=True)
        
        ans = st.radio("Selecciona tu respuesta:", ["A", "B", "C", "D"], 
                       format_func=lambda x: f"{x}) {preg[x.lower()]}",
                       key=f"radio_{st.session_state.paso_global}")
        
        if not st.session_state.respondido:
            if st.button("Confirmar Respuesta ✅"):
                es_correcta = (ans == preg['r'])
                st.session_state.reporte.append({
                    "Pregunta": preg['p'], 
                    "Resultado": "✅" if es_correcta else "❌"
                })
                if es_correcta: st.session_state.puntos += 10
                st.session_state.respondido = True; st.rerun()
        else:
            st.success("¡Respuesta guardada!")
            if st.button("Siguiente Pregunta ➡️"):
                st.session_state.paso_global += 1
                st.session_state.indice_lote += 1
                st.session_state.respondido = False
                if st.session_state.indice_lote >= 5: st.session_state.lote_preguntas = []
                if st.session_state.paso_global > 10: st.session_state.finalizado = True
                st.rerun()

# --- 7. PANTALLA FINAL ---
else:
    st.balloons()
    st.markdown('<div class="header-container"><h1>🎉 ¡Terminamos!</h1></div>', unsafe_allow_html=True)
    st.write(f"### Gracias, {st.session_state.datos_alumno['nom']}.")
    
    if not st.session_state.correo_enviado:
        with st.spinner("📨 Enviando reporte al profesor..."):
            df_reporte = pd.DataFrame(st.session_state.reporte)
            prompt_final = f"Analiza estos resultados: {st.session_state.reporte}. Alumno de {st.session_state.datos_alumno['gra']}."
            analisis = client.chat.completions.create(model=MODELO_IA, messages=[{"role": "user", "content": prompt_final}]).choices[0].message.content
            
            if enviar_informe_docente(st.session_state.datos_alumno['nom'], analisis, df_reporte):
                st.session_state.correo_enviado = True
                st.toast("Reporte enviado con éxito.")

    if st.button("Reiniciar Sistema 🔄"):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()
