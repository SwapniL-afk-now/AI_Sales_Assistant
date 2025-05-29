# app/main.py
from fastapi import FastAPI, HTTPException, status
from app.api.v1.endpoints import call_router
from app.core.config import settings, logger
from app.services.llm_service import get_llm_service # LLMService import might not be directly needed here if only using get_llm_service
from app.services.tts_service import get_tts_service
from app.services.stt_service import get_stt_service
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application startup...")
    logger.info(f"App Title: {settings.APP_TITLE}, Version: {settings.APP_VERSION}")
    
    llm_service = get_llm_service() 
    if not llm_service: # Should ideally not happen if get_llm_service returns an instance
         logger.critical("LLM Service object could not be created by get_llm_service().")
    elif not llm_service.is_ready(): 
        logger.warning(f"LLM Service initialized but NOT READY (Mode: {llm_service.llm_mode}). LOCAL LLM FAILED TO LOAD. Check startup logs for detailed errors.")
    else:
        logger.info(f"LLM Service (local mode) successfully initialized and ready.")
    
    get_tts_service() 
    get_stt_service() 
    logger.info("TTS and STT services initialization attempted.")
    
    yield
    
    logger.info("Application shutdown...")

app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    lifespan=lifespan
)

app.include_router(call_router.router, prefix="/api/v1/sales", tags=["Sales Agent Calls"])

@app.get("/health", tags=["Health Check"], status_code=status.HTTP_200_OK)
async def health_check():
    llm_ok = False
    llm_service_status_detail = "local_llm_initialization_failed"
    
    # Use recreate_instance=False to get the existing instance
    llm_service = get_llm_service(recreate_instance=False) 
    if llm_service:
        if llm_service.is_ready(): 
            llm_ok = True
            llm_service_status_detail = f"local_llm_ready (mode: {llm_service.llm_mode})"
        # No other modes to check for llm_service.llm_mode
    else: 
        llm_service_status_detail = "llm_service_not_instantiated_by_get_llm_service" # Should be rare
            
    return {
        "status": "ok" if llm_ok else "issues_present", # Overall status reflects LLM readiness
        "app_title": settings.APP_TITLE,
        "app_version": settings.APP_VERSION,
        "llm_service_status": "ok" if llm_ok else "critical_issue",
        "llm_service_details": llm_service_status_detail
    }

@app.get("/", tags=["Root"], include_in_schema=False)
async def read_root():
    return {"message": f"Welcome to the {settings.APP_TITLE} API. See /docs for details."}