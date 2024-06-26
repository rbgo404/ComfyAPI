import time
import json
from urllib import request, parse
import requests
from tqdm import tqdm
import os
import asyncio
import base64
from PIL import Image
from io import BytesIO
import re
from subprocess import Popen, PIPE, STDOUT
import asyncio
from main import my_fun
import threading

__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__))
)


async def run_my_fun_async():
    # Use the current event loop
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, my_fun)

def run_my_fun_in_background():
    # Create a new thread to run the async function
    my_fun_thread = threading.Thread(target=lambda: asyncio.run(run_my_fun_async()), daemon=True)
    
    # Start the thread
    my_fun_thread.start()

def log_subprocess_output(pipe):
    for line in iter(pipe.readline, b''): # b'\n'-separated lines
        print(f"[SERVER] {line}", flush=True)

class InferlessPythonModel:
    @staticmethod
    def convert_image_to_base64(image_path):
        with Image.open(image_path) as image:
            buffered = BytesIO()
            image.save(buffered, format="PNG")
            return base64.b64encode(buffered.getvalue()).decode()

    @staticmethod
    def process_single_image(image_path):
        try:
            base64_image = InferlessPythonModel.convert_image_to_base64(image_path)
            # os.remove(image_path)  # Delete the image after conversion
            return base64_image
        except Exception as e:
            print(f"Error processing {image_path}: {e}")
            return None

    @staticmethod
    def get_final_image_name(directory):
        pattern = re.compile(r"ComfyUI_(\d+)_\.png$")
        max_number = 0

        print("*******************************", flush=True)
        for filename in os.listdir(directory):
            print("FileName: ", filename, flush=True)
            match = pattern.match(filename)
            if match:
                number = int(match.group(1))
                max_number = max(max_number, number)

        print(f"Max number: {max_number}", flush=True)
        return f"ComfyUI_{max_number:05d}_.png"

    def initialize(self):
        run_my_fun_in_background()
    def infer(self, inputs):
        try:
            print("Infer Started", flush=True)
            workflow = inputs["workflow"] # For more workflow add the workflow json file in the workflows directory
            positive_token = inputs["positive_token"]
            negative_token = inputs["negative_token"]
            workflow_file_name = f"{workflow}.json"

            prompt = json.loads(
                open(f"{__location__}/workflows/{workflow_file_name}").read()
                .replace("$$POSITIVE_TOKEN$$", positive_token)
                .replace("$$NEGATIVE_TOKEN$$", negative_token)
            )
            
            p = {"prompt": prompt}

            data = json.dumps(p).encode("utf-8")
            print("Prompt Encoding Happened", flush=True)
            print(f"Data {data}", flush=True)
            req = request.Request("http://127.0.0.1:8188/prompt", data=data)
            request.urlopen(req)
            print("Prompt Request Sent", flush=True)

            task_completed = False
            while task_completed != True:
                print("Checking Queue", flush=True)
                response = requests.get("http://127.0.0.1:8188/queue")
                if response.json()["queue_running"] == []:
                    task_completed = True
                    print("Task Completed", flush=True)

            print("Queue Completed", flush=True)
            final_image_name = InferlessPythonModel.get_final_image_name(
                "/var/nfs-mount/Passion-ComfyUI-Volumes/output"
            )
            image_path = f"/var/nfs-mount/Passion-ComfyUI-Volumes/output/{final_image_name}"
            base64_image = InferlessPythonModel.process_single_image(image_path)

            return {"generated_image": base64_image}
        except Exception as e:
            print(f"Error processing: {e}. Error Type: {type(e).__name__}, Arguments: {e.args}", flush=True)
            # return None
            return {"error": e}

    def finalize(self):
        print("Finalizing", flush=True)
        #self.process.terminate()
#if __name__ == "__main__":
#     model = InferlessPythonModel()
#     model.initialize()
#     time.sleep(10)
#     ab = model.infer({"workflow": "txt_2_img","positive_token": "masterpiece image of a smart dog wearing a coat and tie and glasses","negative_token":'low resolution'})
#     print(ab)
#     model.finalize()
