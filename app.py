import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from PIL import Image
from gTTS import gTTS
from audio_recorder_streamlit import audio_recorder
import io
import os

# --- Configurare Pagină ---
st.set_page_config(page_title="Profesor Virtual AI", page_icon="🎓")

st.title("🎓 Profesorul Tău Virtual")
st.markdown("""
Salut! Sunt aici să te ajut cu temele. 
Poți să îmi încarci o poză cu exercițiul, un PDF sau să îmi pui o întrebare vocală!
""")

# --- Sidebar pentru API Key ---
with st.sidebar:
    st.header("Setări")
    api_key = st.text_input("Introdu Google API Key", type="password")
    st.info("Obține cheia gratuit de la [Google AI Studio](https://aistudio.google.com/).")

# --- Funcții Utilitare ---

def get_gemini_response(prompt, content_list, api_key):
    """Trimite datele către Gemini și primește răspunsul"""
    genai.configure(api_key=api_key)
    # Folosim Gemini 1.5 Flash pentru viteză și multimodalitate
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # Prompt de sistem pentru a defini persona profesorului
    system_prompt = """
    Ești un profesor virtual prietenos și răbdător pentru elevi.
    Sarcina ta este să ajuți elevul să înțeleagă tema, NU să îi dai răspunsul direct.
    1. Explică conceptele pas cu pas.
    2. Dacă elevul trimite o poză cu un exercițiu, rezolvă-l explicând fiecare pas, dar încurajează elevul să încerce singur.
    3. Folosește un limbaj simplu, adaptat pentru elevi.
    4. Răspunde în limba română.
    """
    
    full_request = [system_prompt, prompt] + content_list
    response = model.generate_content(full_request)
    return response.text

def text_to_speech(text):
    """Transformă textul în audio"""
    tts = gTTS(text=text, lang='ro')
    audio_buffer = io.BytesIO()
    tts.write_to_fp(audio_buffer)
    audio_buffer.seek(0)
    return audio_buffer

def read_pdf(file):
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

# --- Interfața Principală ---

if api_key:
    # 1. Încărcare Fișiere (Imagini sau PDF)
    uploaded_file = st.file_uploader("Încarcă tema (Poză sau PDF)", type=["jpg", "jpeg", "png", "pdf"])
    
    content_input = [] # Lista cu ce trimitem la AI
    
    if uploaded_file:
        if uploaded_file.type == "application/pdf":
            # Extragem textul din PDF
            pdf_text = read_pdf(uploaded_file)
            content_input.append(f"Conținutul PDF-ului este: {pdf_text}")
            st.success("PDF încărcat și citit!")
        else:
            # Procesăm imaginea
            image = Image.open(uploaded_file)
            st.image(image, caption="Tema încărcată", use_column_width=True)
            content_input.append(image)
            st.success("Imagine încărcată!")

    # 2. Intrare Vocală sau Text
    st.write("---")
    st.subheader("Întreabă profesorul")
    
    # Opțiune text
    user_question = st.text_input("Scrie întrebarea ta aici:")
    
    # Opțiune audio (microfon)
    st.write("Sau înregistrează întrebarea:")
    audio_bytes = audio_recorder(text="Apasă pentru a vorbi", icon_size="2x", neutral_color="#6c757d", recording_color="#dc3545")
    
    submit_btn = st.button("Trimite la Profesor")

    if submit_btn or (audio_bytes and not user_question): # Declanșăm dacă apasă buton sau termină înregistrarea
        
        prompt_text = user_question
        
        # Dacă există audio, trebuie să îl transcriem sau să îl trimitem (Gemini 1.5 suportă audio direct, dar e mai simplu text-to-text pentru logică aici)
        # Pentru simplitate în acest demo gratuit, vom considera audio input ca un semnal de procesare
        # Notă: Gemini 1.5 poate asculta direct audio, dar necesită salvarea fișierului. 
        # Aici ne bazăm pe textul scris SAU presupunem că utilizatorul a încărcat fișierul și vrea explicații generale dacă nu scrie nimic.
        
        if audio_bytes:
             st.audio(audio_bytes, format="audio/wav")
             # Într-o versiune avansată, am trimite audio_bytes la Gemini. 
             # Aici vom trimite un mesaj generic dacă e doar audio fără text, 
             # sau putem folosi o librărie speech-to-text (dar complică deploy-ul gratuit).
             # Vom adăuga o instrucțiune specială pentru Gemini să asculte audio dacă am putea trimite blob-ul direct.
             # WORKAROUND SIMPLU: 
             st.info("Se procesează... (Momentan inputul audio direct către Gemini necesită o configurare mai complexă a fișierelor temporare, așa că voi analiza fișierul încărcat mai sus).")
             if not prompt_text:
                 prompt_text = "Te rog explică-mi ce este în fișierul atașat sau ajută-mă cu tema."

        if not prompt_text and not content_input:
            st.warning("Te rog încarcă un fișier sau scrie o întrebare.")
        else:
            with st.spinner("Profesorul gândește..."):
                try:
                    # Trimitem la Gemini
                    response_text = get_gemini_response(prompt_text, content_input, api_key)
                    
                    # Afișăm răspunsul text
                    st.markdown("### Răspunsul Profesorului:")
                    st.write(response_text)
                    
                    # Generăm Audio (Profesorul vorbește)
                    audio_response = text_to_speech(response_text)
                    st.audio(audio_response, format='audio/mp3')
                    
                except Exception as e:
                    st.error(f"A apărut o eroare: {e}")

else:
    st.warning("Te rog introdu cheia API în meniul din stânga pentru a începe.")
