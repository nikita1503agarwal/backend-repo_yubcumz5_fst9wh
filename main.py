import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

from database import create_document, get_documents, db
from schemas import CleaningInquiry

app = FastAPI(title="Limpieza Zurich API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "API de Empresa de Limpieza en Zúrich"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response

# Lead creation endpoint
@app.post("/api/inquiries", status_code=201)
def create_inquiry(inquiry: CleaningInquiry):
    try:
        inserted_id = create_document("cleaninginquiry", inquiry)
        return {"id": inserted_id, "message": "Solicitud recibida. ¡Gracias!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# List recent inquiries (limited)
@app.get("/api/inquiries", response_model=List[dict])
def list_inquiries(limit: int = 20):
    try:
        docs = get_documents("cleaninginquiry", {}, limit)
        # Convert ObjectId to string if present
        for d in docs:
            if "_id" in d:
                d["id"] = str(d.pop("_id"))
        return docs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Expose schemas to the platform if needed
class SchemaResponse(BaseModel):
    name: str
    fields: dict

@app.get("/schema")
def get_schema():
    # Provide a simple description of collections
    return {
        "cleaninginquiry": {
            "name": "cleaninginquiry",
            "fields": CleaningInquiry.model_json_schema()
        }
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
