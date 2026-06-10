from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from anthropic import Anthropic
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI(
    title="AI Product Description API",
    description="Genera descripciones de productos con IA",
    version="1.0.0"
)

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

VALID_KEYS: dict[str, str] = {
    "test-free-key": "free",
    "test-basic-key": "basic",
    "test-pro-key": "pro",
}

class ProductRequest(BaseModel):
    product_name: str
    features: list[str]
    platform: str = "general"
    language: str = "es"

class ProductResponse(BaseModel):
    product_name: str
    platform: str
    description: str
    plan: str

@app.get("/")
def health_check():
    return {"status": "ok", "api": "AI Product Description API", "version": "1.0.0", "docs": "/docs"}

@app.post("/describe", response_model=ProductResponse)
def describe_product(request: ProductRequest, x_api_key: str = Header(...)):
    if x_api_key not in VALID_KEYS:
        raise HTTPException(status_code=401, detail="API key invalida.")
    plan = VALID_KEYS[x_api_key]
    platform_hints = {
        "mercadolibre": "Optimizada para MercadoLibre: destaca envio, garantia y condicion.",
        "shopify": "Optimizada para Shopify: tono moderno, beneficios y llamado a la accion.",
        "general": "Descripcion general: clara, atractiva y persuasiva.",
    }
    hint = platform_hints.get(request.platform, platform_hints["general"])
    features_text = "\n".join(f"- {f}" for f in request.features)
    prompt = f"""Sos un experto en copywriting para e-commerce.
Genera una descripcion de producto atractiva en idioma '{request.language}'.
{hint}
Producto: {request.product_name}
Caracteristicas:
{features_text}
La descripcion debe tener entre 80 y 150 palabras. Solo devuelve la descripcion."""
    message = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}]
    )
    description = message.content[0].text.strip()
    return ProductResponse(product_name=request.product_name, platform=request.platform, description=description, plan=plan)

@app.get("/platforms")
def list_platforms():
    return {"platforms": ["mercadolibre", "shopify", "general"]}

@app.get("/plan-info")
def plan_info():
    return {"plans": {"free": {"price": "$0/mes", "requests_per_hour": 10}, "basic": {"price": "$9.99/mes", "requests_per_hour": 100}, "pro": {"price": "$29.99/mes", "requests_per_hour": 1000}}}
