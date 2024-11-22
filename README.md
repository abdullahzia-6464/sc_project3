# Instructions for Running

### Important notes:

- Project runs on localhost by default 
- To run on Raspberry Pis, our please set EARTH_IP and SATELLITES_IP in `src/config.py`. 
- Ground control and Ship will be run on one Pi while the satellite will run on the second Pi.
- Please be sure to run `visualise.py` (step 5). Our implementation relies on the visual more than logs to depict what is happening.

- Please run commands in separate terminal windows to see logs. Run all commands from the root directory of the project.



### (Optional) Use a Python venv:
```bash
python3 -m venv .venv
source .venv/bin/activate
```
- If using a venv, be sure to activate each time before running a script.

### 1. Install necessary packages using:
```bash
	pip3 install -r requirements.txt 
```

### 2. Run ground control:
```bash
	./run_ground_control.sh
```
### 3. Run satellites:
```bash
	./run_satellites.sh
```
### 4. Run ship:
```bash
	./run_ship.sh
```
### 5. Run visualise.py to see all nodes and package transmission (if running on pis, port forwarding needs to be configured):
- Runs on port `33069`
```bash
	python3 src/visualise.py
```
- Access the visualisation at  http://127.0.0.1:33069 by default.
- If running on one of the Pis, feel free to run on either Pi.
- Port forwarding will have to be configured first from the Pi to Macneill machine and then to your local machine. 
- The latest versions of Mozilla Firefox and Google Chrome have been tested to run the visualisation properly.

### 6. Feel free to stop a satellite to show our implementation's resilience to satellite failure:

- Identify the satellite's port you want to kill by clicking on the visual. Run the below script to kill it and you will see its any links with other devices disappear and no messages being routed through it.
```bash
	./stop_port.sh <port>
```
### 7. To stop all satellites and free up ports (Ctrl+C won't work for satellites):
```bash
	./stop_satellites.sh
```