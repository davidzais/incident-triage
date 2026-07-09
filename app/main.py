from fastapi import Depends, FastAPI, status
from db.database import get_session
from models.incident import Incident, IncidentRead
from models.providers.alert_manager import Payload
from db.db_service import record_incident, get_incidents
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)


api = FastAPI()

@api.get("/incidents", status_code=status.HTTP_200_OK, response_model=list[IncidentRead])
async def get_all_open_incidents(session = Depends(get_session)) -> list[IncidentRead]:
    return await get_incidents(session)

@api.post("/webhooks/alertmanager/", status_code=status.HTTP_202_ACCEPTED)
async def alert_manager(payload: Payload , session = Depends(get_session) ) -> list[Incident]:  
    incidents: list[Incident] = payload.to_incidents()   
    try:
        async with session.begin(): 
            for incident in incidents:           
                await record_incident(session=session, incident=incident)       
    except Exception:
        logger.exception("failed to record incidents")
        raise
    return incidents