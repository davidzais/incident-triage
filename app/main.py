from fastapi import FastAPI, HTTPException, status
from models.incident import Incident
from models.providers.alert_manager import Payload
from db.db_service import record_incident
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)


api = FastAPI()

@api.post("/webhooks/alertmanager/", status_code=status.HTTP_202_ACCEPTED)
async def alert_manager(payload: Payload ) -> list[Incident]:  
    incidents: list[Incident] = payload.to_incidents()
   
    try:
        for incident in incidents:
            await record_incident(incident)
       
    except Exception:
        logger.exception("failed to record incidents")
        raise


    return incidents