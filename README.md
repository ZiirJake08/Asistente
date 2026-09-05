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

## 3. Subirlo a internet (para que funcione desde el iPhone)

Cuando quieras que tu iPhone también le hable a este backend, lo subimos a un
servicio como Railway o Render (tienen plan gratis). Avísame cuando lleguemos
a este paso y lo hacemos juntos.

## Siguiente paso

Este backend todavía no lee tu correo ni tu calendario de verdad — solo conversa.
El siguiente paso es agregarle "tools" (herramientas) para que pueda leer y escribir
en Gmail/Calendar reales.
