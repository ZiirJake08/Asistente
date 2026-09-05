import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from google import genai
from google.genai import types
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request as GoogleRequest
from googleapiclient.discovery import build
import google.oauth2.credentials

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

historial: list[dict] = []

# --- Autorización con Google (Gmail personal) ---
# Ojo: esto se guarda en memoria. Si Render reinicia el servidor,
# hay que volver a autorizar dando clic al link de /auth/google/login.
credenciales_google: dict = {}

GOOGLE_CLIENT_CONFIG = {
    "web": {
        "client_id": os.environ["GOOGLE_CLIENT_ID"],
        "client_secret": os.environ["GOOGLE_CLIENT_SECRET"],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": [os.environ["GOOGLE_REDIRECT_URI"]],
    }
}
GOOGLE_SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def crear_flow_google():
    return Flow.from_client_config(
        GOOGLE_CLIENT_CONFIG,
        scopes=GOOGLE_SCOPES,
        redirect_uri=os.environ["GOOGLE_REDIRECT_URI"],
    )


@app.get("/auth/google/login")
def google_login():
    flow = crear_flow_google()
    url_autorizacion, _ = flow.authorization_url(
        access_type="offline", prompt="consent"
    )
    return RedirectResponse(url_autorizacion)


@app.get("/auth/google/callback")
def google_callback(code: str):
    flow = crear_flow_google()
    flow.fetch_token(code=code)
    creds = flow.credentials
    credenciales_google["personal"] = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": creds.scopes,
    }
    return {"ok": True, "mensaje": "Gmail personal conectado. Ya puedes cerrar esta pestaña."}


def obtener_credenciales_google(cuenta: str = "personal"):
    datos = credenciales_google.get(cuenta)
    if not datos:
        return None
    creds = google.oauth2.credentials.Credentials(**datos)
    if creds.expired and creds.refresh_token:
        creds.refresh(GoogleRequest())
    return creds


def leer_ultimos_correos_gmail(max_resultados: int = 5) -> str:
    creds = obtener_credenciales_google("personal")
    if not creds:
        return "El correo personal (Gmail) todavía no está conectado. Pídele al usuario que entre a /auth/google/login"

    servicio = build("gmail", "v1", credentials=creds)
    resultado = servicio.users().messages().list(
        userId="me", maxResults=max_resultados, labelIds=["INBOX"]
    ).execute()
    mensajes = resultado.get("messages", [])

    resumen = []
    for m in mensajes:
        detalle = servicio.users().messages().get(
            userId="me", id=m["id"], format="metadata",
            metadataHeaders=["Subject", "From"],
        ).execute()
        headers = {h["name"]: h["value"] for h in detalle["payload"]["headers"]}
        resumen.append(
            f"De: {headers.get('From', '?')} | Asunto: {headers.get('Subject', '(sin asunto)')}"
        )

    return "\n".join(resumen) if resumen else "No hay correos en la bandeja."


# --- Herramienta que Ziir puede usar ---
HERRAMIENTAS = types.Tool(function_declarations=[
    types.FunctionDeclaration(
        name="leer_correos_personales",
        description="Lee los últimos correos de la bandeja de entrada del Gmail personal del usuario.",
        parameters={
            "type": "object",
            "properties": {
                "cantidad": {"type": "integer", "description": "Cuántos correos leer, por defecto 5"}
            },
        },
    )
])

SYSTEM_PROMPT = (
    "Eres Ziir, un asistente personal de productividad. "
    "Responde en español, corto y directo. "
    "Ayudas con correo, agenda y notas del usuario. "
    "Cuando el usuario pregunte por su correo personal/Gmail, usa la herramienta leer_correos_personales."
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
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            tools=[HERRAMIENTAS],
        ),
    )

    parte = respuesta.candidates[0].content.parts[0]

    if parte.function_call and parte.function_call.name == "leer_correos_personales":
        cantidad = parte.function_call.args.get("cantidad", 5)
        resultado_funcion = leer_ultimos_correos_gmail(cantidad)

        contenidos.append(respuesta.candidates[0].content)
        contenidos.append(
            types.Content(
                role="user",
                parts=[types.Part(function_response=types.FunctionResponse(
                    name="leer_correos_personales",
                    response={"resultado": resultado_funcion},
                ))],
            )
        )

        respuesta = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=contenidos,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT, tools=[HERRAMIENTAS]
            ),
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
