# Backend de Ada (tu asistente)

## 1. Correrlo en tu PC

```
pip install -r requirements.txt
$env:GEMINI_API_KEY="tu-api-key-aqui"      (en Windows PowerShell)
uvicorn main:app --reload --port 8000
```

Consigues tu API key gratis en https://aistudio.google.com/apikey (solo necesitas una cuenta de Google, sin tarjeta).

El modelo usado (`gemini-2.5-flash-lite`) está dentro de la capa gratuita de Gemini.
Google va renovando sus modelos cada tanto — si en el futuro ves un error de "modelo no encontrado",
entra a https://aistudio.google.com/apikey y revisa qué modelos gratis están disponibles ese día.

Pruébalo abriendo en el navegador: http://localhost:8000/historial (debería devolver una lista vacía).

Para probar el chat sin frontend todavía, en otra terminal:
```
curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d "{\"mensaje\": \"hola\"}"
```

## 2. Conectar el frontend

El frontend (la página) le hace peticiones POST a `http://localhost:8000/chat` mientras
pruebas en tu PC. Cuando lo subas a internet, cambias esa URL por la del servidor real.

## 4. Subirlo a internet con Render (gratis)

**Paso 1 — Sube el código a GitHub**
1. Crea una cuenta en https://github.com si no tienes
2. Crea un repositorio nuevo (puede ser privado)
3. Sube ahí la carpeta completa del backend (`main.py`, `requirements.txt`)

**Paso 2 — Crea el servicio en Render**
1. Crea una cuenta en https://render.com (gratis, con tu cuenta de GitHub es lo más rápido)
2. Clic en "New +" → "Web Service"
3. Conecta tu repositorio de GitHub
4. Configura así:
   - **Build command**: `pip install -r requirements.txt`
   - **Start command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Instance type**: Free
5. En "Environment Variables", agrega `GEMINI_API_KEY` con tu key real
6. Clic en "Create Web Service"

Render te va a dar una URL pública, algo como `https://ziir-backend.onrender.com`.

**Paso 3 — Conecta el frontend**
En `index.html`, cambia:
```js
const BACKEND_URL = "http://localhost:8000";
```
por tu URL real de Render, por ejemplo:
```js
const BACKEND_URL = "https://ziir-backend.onrender.com";
```

**Aviso del plan gratis**: el servidor "duerme" tras ~15 min sin uso. La primera vez que Ziir lo reciba puede tardar 30-50 segundos en responder mientras despierta; después va normal.

## Siguiente paso

Este backend todavía no lee tu correo ni tu calendario de verdad — solo conversa.
El siguiente paso es agregarle "tools" (herramientas) para que pueda leer y escribir
en Gmail/Calendar reales.
