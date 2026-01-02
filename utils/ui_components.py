import streamlit as st
import base64
import os

def get_base64(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def inject_custom_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        html, body, [class*="css"]  {
            font-family: 'Inter', Arial, sans-serif;
        }

        .stApp {
            background-color: #DBE0EF;
            margin: 0;
            padding: 0.5rem;
        }

        @media (min-width: 768px) {
            .stApp {
                margin: 1rem;
                padding: 1rem;
            }
        }
        
        /* Sidebar styling */
        section[data-testid="stSidebar"] {
            background-color: #FFFFFF;
            color: black;
        }
        section[data-testid="stSidebar"] hr {
            border-color: #1E3A8A;
        }
        section[data-testid="stSidebar"] h1, 
        section[data-testid="stSidebar"] h2, 
        section[data-testid="stSidebar"] h3,
        section[data-testid="stSidebar"] .stMarkdown p {
            color: black !important;
        }

        /* Header Principal Personalizado */
        .main-header {
            background-color: #FFFFFF;
            padding: 1rem;
            border-radius: 20px;
            box-shadow: 0 4px 6px -1px rgba(255, 255, 255, 0.1);
            margin-bottom: 1.5rem;
            border-right: 6px solid #1E3A8A;
            border-left: 6px solid #1E3A8A;
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
            gap: 1rem;
        }

        @media (min-width: 768px) {
            .main-header {
                padding: 1.5rem;
                border-radius: 120px;
                flex-direction: row;
                text-align: left;
                gap: 1.5rem;
            }
        }

        .main-header-info {
            flex-grow: 1;
            width: 100%;
        }
        .main-header h1 {
            color: #1E3A8A;
            margin: 0;
            font-size: 2rem;
            font-weight: 700;
        }
        .main-header p {
            color: #64748B;
            margin: 0.5rem 0 0 0;
        }

        /* Tabs Styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 10px;
            background-color: transparent;
        }
        .stTabs [data-baseweb="tab"] {
            height: 10px;
            background-color: #FFFFFF;
            border-radius: 8px 8px 0 0;
            gap: 1px;
            padding-top: 5px;
            padding-bottom: 5px;
            border: 1px solid #E2E8F0;
            transition: all 0.2s ease;
            height: 50px;
            width: 100%;
        }
        .stTabs [aria-selected="true"] {
            background-color: #1E3A8A !important;
            color: white !important;
            border-color: #1E3A8A !important;
        }

        /* Section titles */
        h1, h2, h3 {
            color: #8D9AA2 !important;
            font-weight: 400;
            letter-spacing: -0.025em;
        }
        
        /* File Uploaders - Estilo Botón Profesional */
        section[data-testid="stSidebar"] [data-testid="stFileUploader"] {
            background-color: #FFFFFF;
            border: 2px solid #E2E8F0;
            border-radius: 12px;
            padding: 1.25rem;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
            cursor: pointer;
        }
        
        section[data-testid="stSidebar"] [data-testid="stFileUploader"]:hover {
            border-color: #1E3A8A;
            box-shadow: 0 10px 15px -3px rgba(30, 58, 138, 0.1);
            transform: translateY(-2px);
        }
        
        /* Ocultar el texto de Drag & Drop y hacerlo más compacto */
        section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {
            padding: 0;
            background: transparent;
            border: none;
        }
        
        section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] > div:first-child {
            display: none; /* Oculta el icono nube y texto drag/drop */
        }

        /* Estilizar el botón "Browse files" real */
        section[data-testid="stSidebar"] [data-testid="stFileUploader"] button {
            background-color: #1E3A8A !important;
            color: white !important;
            width: 100%;
            border-radius: 8px !important;
            border: none !important;
            padding: 0.5rem 1rem !important;
            font-weight: 600 !important;
            text-transform: uppercase;
            letter-spacing: 0.025em;
            font-size: 0.8rem;
        }

        section[data-testid="stSidebar"] [data-testid="stFileUploader"] button:hover {
            background-color: #3B82F6 !important;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }

        /* Asegurar visibilidad de etiquetas */
        section[data-testid="stSidebar"] [data-testid="stFileUploader"] label {
            color: #1E3A8A !important;
            font-weight: 700 !important;
            margin-bottom: 0.75rem !important;
            font-size: 0.9rem !important;
        }

        /* Estilo para el límite de tamaño */
        section[data-testid="stSidebar"] [data-testid="stFileUploader"] small {
            color: #64748B !important;
            display: block;
            margin-top: 0.5rem;
            text-align: center;
        }
        
        /* Tables and Cards */
        div[data-testid="stDataFrame"] {
            background-color: #FFFFFF;
            padding: 0.5rem;
            border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
            border: 1px solid #E2E8F0;
        }

        /* Buttons */
        button[kind="primary"] {
            background-color: #14D9E4 !important;
            border-radius: 8px !important;
            font-weight: 400 !important;
        }
    </style>
    """, unsafe_allow_html=True)

def render_header():
    logo_base64 = ""
    if os.path.exists("Logo.png"):
        logo_base64 = get_base64("Logo.png")
    
    st.markdown(f"""
    <div class="main-header">
        <div class="logo-container">
            {"<img src='data:image/png;base64," + logo_base64 + "' width='70'>" if logo_base64 else ""}
        </div>
        <div class="main-header-info">
            <p>Sube tus archivos PDF para extraer, procesar y comparar datos de importación automáticamente. 
               <br><span style="font-size:0.8rem; color:#94a3b8;">v2.9.2 (UI Update)</span>
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)
