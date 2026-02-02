from typing import Annotated
from fastapi import Depends
from functools import lru_cache
import logging
from google.cloud import firestore


logger = logging.getLogger(__name__)

@lru_cache()
def get_db() -> firestore.Client:
    """
    !!! THIS IS JUST AN EXAMPLE !!!
    Dependency function to inject the Firestore client.
    !!! Each service implementing this should override this function with their own Firebase initialization. !!!
    """
    logger.info("Base get_db dependency called - this should be overridden by the implementing service")
    return firestore.Client()

# Base type for dependency injection that services will implement
FirestoreDBClient = Annotated[firestore.Client, Depends(get_db)]
