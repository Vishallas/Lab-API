# Sim-Lab API

Sim-Lab API is made with flask, this api will manage a Elastic Cloud Compute resources for this lab.

## How to use

Create a .env file for the environment variables and place it in the root of this app.

Also place the private file in the root of this app.

### End-Points

| EndPoints | Details |
| --------- | ------- |
| `/start_lab` | Use this endpoint to initiate the boot process of the lab. |
| `/stop_lab` | Use this endpoint to initiate shutdown process of the lab. ex. /stop_lab?lab_id=i-0429bfa260ba71cbb |
| `/lab_state` | Use this endpoint to check the status of the boot process. ex. /lab_state?lab_id=i-0429bfa260ba71cbb |
| `/lab_cred` | Use this endpoint to get the credientials of the lab. ex. /lab_cred?lab_id=i-0429bfa260ba71cbb |

### Usage

Check the `status` key of the response for `/stop_lab`, `/la_state` and `/lab_cred`.
