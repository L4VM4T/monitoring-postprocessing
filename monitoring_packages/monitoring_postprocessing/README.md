The 'monitoring_postprocessing' package is a post-processing tool for qubit coherence and qubit frequency data collected using the SCQT monitoring routine that you will find at the end of the file.


- Structure of the package:
monitoring_postprocessing/
├── __init__.py  
├── api.py
├── io_utils.py
├── processing.py
├── plotting.py
├── convert_excel_to_csv.py
├── pyproject.toml
└── README.md

- Use example:

from monitoring_postprocessing.api import run_qubit_postprocessing

nas_path = "/mnt/nas_monitoring"

run_qubit_postprocessing(
    qpu_name="QPU-147",      # quantum processor
    qubit_name="q0",         # qubit to be analyzed
    dataset_root=nas_path,   # root path where the monitoring datasets are stored   
    max_values={             # (optional) dictionary used to define upper bounds for the plotted metrics (these limits are useful to improve visualization and exclude outliers)
        "T1": None,
        "T2*": 100,
        "T2E": None,
        "Qubit Frequency": None
    },
    bins=20                  # number of bins used for the histogram
)



- Installation:
For the users to be able to install the package without problems, they will need to have access to the same NAS directory. This requires a few steps:

1. Create a local folder to mount the NAS
sudo mkdir -p /mnt/nas_monitoring

OBS: Before mounting, you can check the conection by doing:
smbclient "//192.168.128.40/characterization/SCQT/monitoring" -U YOUR_USER
You will need to provide the password.

It is recommended to create a credential file /etc/cifs-credentials:
sudo nano /etc/cifs-credentials

with the following content:
username=YOUR_USER
password=YOUR_PASSWORD

secure permissions:
sudo chmod 600 /etc/cifs-credentials


2. Install the helper for CIFS (if it is not already installed)
sudo apt update
sudo apt install cifs-utils

3. Mount the NAS
Ex.
sudo mount -t cifs "//192.168.128.40/characterization/SCQT/monitoring" /mnt/nas_monitoring -o credentials=/etc/cifs-credentials,uid=$(id -u),gid=$(id -g),vers=3.0

If this step works, we are ready to automatize the process.

4. Validate the mount
Ex.
ls /mnt/nas_monitoring/QPU-147

5. Automatize the mount # Montaje NAS monitoring
If this step is not done, everytime the computer is restarted /mnt/nas_monitoring will be empty and the command moint should be executed again to access the NAS.

sudo nano /etc/fstab 

with the following content:
//192.168.128.40/characterization/SCQT/monitoring /mnt/nas_monitoring cifs credentials=/etc/cifs-credentials,uid=1000,gid=1000,vers=3.0


- SCQT monitoring routine: (it needs improvement)

qubit=q3 # CHANGE
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import csv
import gc 


T1 = 28e-6 # Estimation of T1, t2 and T2E for qubit - CHANGE this based on the results
ramsey_est = 36e-6
T2E_est = 39e-6

quantum_device.cfg_sched_repetitions(500) 
points = 30 
iterations=800 # CHANGE

with open('20251125_coherence_monitoring_log_q3.csv', mode='w', newline='') as file: # CHANGE (just the qubit number, not the format)
    writer = csv.writer(file)
    writer.writerow(['Iteration', 'Timestamp', 'T1', 'T1_std', 'T2*', 'T2*_std', 'T2E', 'T2E_std', 'Qubit Frequency'])

    # Main loop
    for i in range(iterations):
        t1_times = np.linspace(qubit.rxy.duration()*1.5, 4*T1, points)
        t1_times = t1_times - t1_times%4e-9

        ramsey_times = np.linspace(qubit.rxy.duration()*3, 4*ramsey_est, points)
        ramsey_times = ramsey_times - ramsey_times%8e-9

        echo_times = np.linspace(qubit.rxy.duration()*3, 4*T2E_est, points)
        echo_times = echo_times - echo_times%8e-9

        print(f"Running iteration {i + 1} of {iterations}")
        
        # Timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Measure coherence
        try:
            analyzed_dset = meas.single_qubit_timedomain.measure_coherence_times(
                quantum_device=quantum_device,
                qubit_name="q3", # CHANGE
                t1_times=t1_times,
                ramsey_times=ramsey_times,
                echo_times=echo_times,
                artificial_detuning=3 / ramsey_times[-1],
                plot_figures=False
            )
        
            # Extract T1
            try:
                t1 = analyzed_dset.t1_analysis.quantities_of_interest['T1'].nominal_value
                t1_std_dev = analyzed_dset.t1_analysis.quantities_of_interest['T1'].std_dev
            except:
                t1 = np.nan
                t1_std_dev = np.nan
        
            # Extract T2* and qubit frequency
            try:
                if 'T2*' in analyzed_dset.ramsey_analysis.quantities_of_interest:
                    t2_star = analyzed_dset.ramsey_analysis.quantities_of_interest['T2*'].nominal_value
                    t2_star_std_dev = analyzed_dset.ramsey_analysis.quantities_of_interest['T2*'].std_dev
                    qubit_freq = analyzed_dset.ramsey_analysis.quantities_of_interest["qubit_frequency"].nominal_value
                elif 'T2*_1' in analyzed_dset.ramsey_analysis.quantities_of_interest:
                    t2_star = min(
                        analyzed_dset.ramsey_analysis.quantities_of_interest['T2*_1'].nominal_value,
                        analyzed_dset.ramsey_analysis.quantities_of_interest['T2*_2'].nominal_value
                    )
                    t2_star_std_dev = min(
                        analyzed_dset.ramsey_analysis.quantities_of_interest['T2*_1'].std_dev,
                        analyzed_dset.ramsey_analysis.quantities_of_interest['T2*_2'].std_dev
                    )
                    qubit_freq = analyzed_dset.ramsey_analysis.quantities_of_interest["qubit_frequency"].nominal_value
                else:
                    t2_star = np.nan
                    t2_star_std_dev = np.nan
                    qubit_freq = np.nan
            except:
                t2_star = np.nan
                t2_star_std_dev = np.nan
                qubit_freq = np.nan
        
            # Extract T2E
            try:
                t2e = analyzed_dset.echo_analysis.quantities_of_interest['t2_echo'].nominal_value
                t2e_std_dev = analyzed_dset.echo_analysis.quantities_of_interest['t2_echo'].std_dev
            except:
                t2e = np.nan
                t2e_std_dev = np.nan
            
            del analyzed_dset 
            gc.collect() 

        except Exception as e:
            print(f"Iteration {i+1}: failed with error {e}. Skipping data logging for this iteration.")
            t1, t1_std_dev, t2_star, t2_star_std_dev, t2e, t2e_std_dev, qubit_freq = np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan

        print(f"[{timestamp}] T1 = {t1:.2e}, T2* = {t2_star:.2e}, T2E = {t2e:.2e}, qubitfreq = {qubit_freq}")
    

        writer.writerow([i + 1, timestamp, t1, t1_std_dev, t2_star, t2_star_std_dev, t2e, t2e_std_dev, qubit_freq])
        
        file.flush()
        
        del t1_times
        del ramsey_times
        del echo_times
        gc.collect()