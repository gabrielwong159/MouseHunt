from fastapi import FastAPI, Response
from captcha_solver import solve_captcha

app = FastAPI()


@app.get('/')
async def main(url: str):
    return Response(content=solve_captcha(url), media_type='text/plain')
