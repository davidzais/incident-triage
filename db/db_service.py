from models.incident import Incident, AlertState
from sqlalchemy import select, func
from db.database import get_session_maker
from db.tables import IncidentORM, Status
from sqlalchemy.dialects.postgresql import insert

async def record_incident(incident: Incident) -> None:
    session_maker = get_session_maker()
    async with session_maker() as session:
        async with session.begin():  
            # doing it this way creates an atomic upsert operation, which prevents a possible race condition if calling to get the item first            
            # The upsert operation will insert a new record if the fingerprint does not exist, or update the existing record if it does. 
            # The times_seen field is incremented on update, and last_seen is updated to the current timestamp. 
            stmt = insert(IncidentORM).values( fingerprint = incident.fingerprint,
                         severity = incident.severity,
                         service = incident.service,
                         title = incident.title,
                         status = incident.status,
                         last_seen = func.now(),                        
                         progress_status = Status.OPEN if incident.status == AlertState.FIRING else Status.CLOSED )
            upsert = stmt.on_conflict_do_update(index_elements=["fingerprint"], 
                                            set_= { 
                                                    "severity": stmt.excluded.severity,
                                                    "service" : stmt.excluded.service,
                                                    "title" : stmt.excluded.title,
                                                    "status" : stmt.excluded.status,
                                                    "times_seen": IncidentORM.times_seen + 1,
                                                    "last_seen": func.now(),
                                                    "progress_status" :Status.OPEN if incident.status == AlertState.FIRING else Status.CLOSED
                                                }
                                            )                
            await session.execute(upsert)  
                       
              
                                   


async def get_incident_by_fingerprint(session, fingerprint: str) -> IncidentORM | None:
    stmt = select(IncidentORM).where(IncidentORM.fingerprint == fingerprint)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()
       