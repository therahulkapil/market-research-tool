from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
from testapp.api.gen_addition import router as addition_router
from testapp.api.gen_subtraction import router as subtraction_router
from testapp.api.gen_multiplication import router as multiplication_router
from testapp.api.gen_division import router as division_router

app = FastAPI()
app.include_router(addition_router) 
app.include_router(subtraction_router)
app.include_router(multiplication_router)
app.include_router(division_router)



# include_router = [
#     addition_router,
#     subtraction_router,
#     multiplication_router,
#     division_router
# ]
# for router in include_router:
    # app.include_router(addition_router)
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],          
# )
@app.get("/")
async def root():
    return {"message": "Hello World"}