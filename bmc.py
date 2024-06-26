import urllib3
import serial
import time
import redfish
import requests


# Suppress the warning for unverified HTTPS requests
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Creates a serial connection with the bmc, waits for it to initalize, writes the command, and prints the command line response

def set_ip(bmc_ip, bmc_user, bmc_pass):
    ser = serial.Serial('/dev/ttyUSB0', 115200)
    user = f"{bmc_user}\n"
    passw = f"{bmc_pass}\n"

    try:
        time.sleep(2)
        # login
        ser.write(user.encode('utf-8'))
        time.sleep(2)
        ser.write(passw.encode('utf-8'))
        time.sleep(5)
        # Sending the command to set the IP
        command = f"ifconfig eth0 up {bmc_ip}\n"
        ser.write(command.encode('utf-8'))

        # Reading the prompt after login 
        ser.read_until(b'# ')

        # Reading the response from the command
        response = ser.read_until(b'\n')
        print(response)
    finally:
        ser.close()


# Updates the BMC using the redfish library
    
def bmc_update(bmc_user, bmc_pass, bmc_ip, fw_path):
    redfish_client = redfish.redfish_client(base_url=f"https://{bmc_ip}", username=bmc_user, password=bmc_pass)
    try:
        redfish_client.login()

        # Retrieve the Update Service
        update_service = redfish_client.get("/redfish/v1/UpdateService")
        if update_service.status != 200:
            print("Failed to find the update service.")
            exit()

        update_service_url = update_service.dict["@odata.id"]

        # Read firmware file content
        with open(fw_path, 'rb') as firmware_file:
            firmware_content = firmware_file.read()

        # Firmware update
        response = redfish_client.post(f"{update_service_url}/update", body=firmware_content, headers={"Content-Type": "application/octet-stream"})
        if response.status == (200 or 202):
            print(response.text)
        else:
            print("Failed to initiate firmware update. Response code:", response.status)
    except Exception as e:
        print("Error occurred:", e)
    finally:
        redfish_client.logout()
    
            
def reset_ip(bmc_user, bmc_pass, bmc_ip):
    url = f"https://{bmc_ip}/redfish/v1/Managers/bmc/Actions/Manager.ResetToDefaults"
    headers = {"Content-Type": "application/json"}
    payload = {
        "ResetToDefaultsType": "ResetAll"
    }
    try:
        response = requests.post(url, json=payload, headers=headers, auth=(bmc_user, bmc_pass), verify=False)
        if response.status_code == 200:
            print("BMC reset to factory defaults successfully.")
        else:
            print("Failed to reset BMC. Response code:", response.status_code)
            print(response.json())
    except Exception as e:
        print("Error occurred:", e)
