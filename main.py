import json

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import subprocess
import sys
import os
import subprocess
import sys
import requests

from pydantic import BaseModel

app = FastAPI()

_TODOS = {}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
                                                                         
def uploadFile(path):
  fileName = os.path.basename(path)
  return subprocess.Popen(
    f"scp -o StrictHostKeyChecking=no -P 22 {path} ubuntu@129.146.110.132:{fileName}", 
    shell=True, 
    stdout=sys.stdout, 
    stderr=subprocess.PIPE
  ).communicate()

@app.get("/")
async def hello_world():
  return "hello, welcome to chatgpt plugin template! Go to chat.openai.com and paste the url"

# @app.get("/connect")
# async def connectGPU():
#   """
#   Connects to a GPU machine and returns the output of the command.
#   """
#   return "Connection Success"

# class Command(BaseModel):
#   command: str
  
# @app.post("/run-command")
# async def run_command(command: Command):
#   """
#   Runs a command on the remote GPU machine. The input is a JSON object with a single key, "command", which is the command to run.
  
#   Returns the output, as well as an "err" key which is the stderr output. You can ignore the "err" output most of the time.
  
#   (if command is uploading to s3, use aws cli & upload to the bucket "mirror-uploads" with public read access and return full url to user)
#   """
#   # req = await request.json()
#   command = command.command
#   print("Running:", command)
#   result, err = runCommand(command)
#   # result = result.decode('utf-8')
#   # err = err.decode('utf-8')
#   print("Result:\n", result)
#   response = {
#     "result": result,
#     "err": err
#   }
#   return JSONResponse(content=response, status_code=200)


control_models = {
  "canny": "control_canny-fp16 [e3fe7712]",
  "depth": "control_depth-fp16 [400750f6]",
  "hed": "control_hed-fp16 [13fee50b]",
  "laplace": "control_laplace-fp16 [8f2576c7]",
  "mlsd": "control_mlsd-fp16 [e3705cfa]",
  "normal": "control_normal-fp16 [63f96f7c]",
  "openpose": "control_openpose-fp16 [9ca67cc5]",
  "scribble": "control_scribble-fp16 [c508311e]",
  "seg": "control_seg-fp16 [b9c1cc12]"
}


class PhotoSetupRequest(BaseModel):
  imageSrc: str

@app.post("/photo-setup")
async def editPhoto(settings: PhotoSetupRequest):
  """
  To setup photo editing, takes a link to a photo for setup. Returns the same image link which should be shown in markdown: ![Photo](url). Ask the user for a prompt describing the image they want.
  """
  # Takes a link to a photo and returns a list of prompts that can be used to edit the photo.
  # """
  return JSONResponse(content=settings.imageSrc, status_code=200)


class PhotoEditRequest(BaseModel):
  imageSrc: str
  prompt: str
  
@app.post("/edit-photo")
async def editPhoto(settings: PhotoEditRequest):
  """
  Takes a photo and edits it to match the prompt. Returns urls that should be shown in markdown: ![Edited Photo](url). Display all the images. Don't add extra text, just display the markdown image.
  """

  # return JSONResponse(content="https://mirror-uploads.s3.us-west-2.amazonaws.com/c72a0507-dfc2-4226-88c1-4fd0b45fa88b.png", status_code=200)
  
  payload = {
    "settings": {
      "img2img": False,
      "prompt": settings.prompt,
      "negative_prompt": "low quality, fake, painting, greyscale, night, beard, deformed, out of frame",
      "steps": 15,
      "batch_size": 2,
      "cfg_scale": 15,
      "sampler_index": "DDIM",
      "width": 1024,
      "height": 768,
      
      # "width": 768,
      # "height": 576,
      # "denoising_strength": 0.9,
      "input_image_src": settings.imageSrc,
      "controlnet": [
        {
        "model": control_models["canny"],
        "module": "canny",
        "weight": 0.75,
        "processor_res": 768,
        "threshold_a": 30,
        "threshold_b": 60,
        },
        {
          "model": control_models["laplace"],
          "module": "none",
          "weight": 0.25,
          "processor_res": 768,
        },
      ]
    }
  }
  print('Sending request to model server...', payload)
  # Send the POST request and handle the response
  response = requests.post('http://localhost:3001/api/model/txt2img-sync', json=payload)

  if response.status_code == 200:
      # Request was successful
      # print("Response:", response.text)
      print("Response:", response.json())
      data = response.json()
      
      res = {
        "image_urls": data['urls'],
      }
      
      # resText = f"image: {data['urls'][0]}"

      return JSONResponse(content=res, status_code=200)
  else:
      # Request failed
      print("Request failed with status code:", response.status_code)
    
  return JSONResponse(content='yo', status_code=200)


@app.get("/logo.png")
async def plugin_logo():
  return FileResponse('camera.jpeg')


@app.get("/.well-known/ai-plugin.json")
async def plugin_manifest(request: Request):
  host = request.headers['host']
  with open("ai-plugin.json") as f:
    text = f.read().replace("PLUGIN_HOSTNAME", f"https://{host}")
  return JSONResponse(content=json.loads(text))


if __name__ == "__main__":
  import uvicorn
  uvicorn.run(app, host="localhost", port=3000)
