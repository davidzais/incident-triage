from fastapi import FastAPI, status
from models.incident import Incident
from models.providers.alert_manager import Payload


api = FastAPI()

@api.post("/webhooks/alertmanager/", status_code=status.HTTP_202_ACCEPTED)
async def alert_manager(payload: Payload ) -> list[Incident]:  
    incidents: list[Incident] = payload.to_incidents()
   
    return incidents