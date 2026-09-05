import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai
from google.genai import types

app = FastAPI()

# Permite que tu página (frontend) le hable a este backend.
# Cuando tengas el dominio real de tu página, cámbialo aquí en vez de "*".
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

# Memoria simple en RAM. Se reinicia si el servidor se reinicia.
# Más adelante la cambiamos por una base de datos si quieres que persista.
historial: list[dict] = []

SYSTEM_PROMPT = (
    "Eres Ziir, un asistente personal de productividad. "
    "Responde en español, corto y directo. "
    "Ayudas con correo, agenda y notas del usuario."
)


class MensajeEntrada(BaseModel):
    mensaje: str


@app.post("/chat")
def chat(entrada: MensajeEntrada):
    historial.append({"role": "user", "content": entrada.mensaje})

    contenidos = [
        types.Content(
            role="model" if turno["role"] == "assistant" else "user",
            parts=[types.Part(text=turno["content"])],
        )
        for turno in historial
    ]

    respuesta = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=contenidos,
        config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
    )

    texto_respuesta = respuesta.text

    historial.append({"role": "assistant", "content": texto_respuesta})

    return {"respuesta": texto_respuesta}


@app.get("/historial")
def obtener_historial():
    return {"historial": historial}


@app.post("/reiniciar")
def reiniciar():
    historial.clear()
    return {"ok": True}
