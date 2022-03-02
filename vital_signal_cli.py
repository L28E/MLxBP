#!/usr/bin/env python3

import cmd
import os
import tkinter as tk
from tkinter import filedialog

import numpy as np
from matplotlib import pyplot as plt
from pandas import DataFrame, read_csv

import signal_utils
import feature_extraction
import preprocessing

banner = """                                                                          
       ___               __     __                     __         
\  / |  |   /\  |       /__` | / _` |\ |  /\  |       /  ` |    | 
 \/  |  |  /~~\ |___    .__/ | \__> | \| /~~\ |___    \__, |___ | 
                                                                                                                                                                            
Command line tool/module to process ECG and PPG signals for ML analysis. Type "help" or "?" to list commands.                    
"""

help_text = """
-Start with the "load" command to load some data from a file
-Then, use the "select" command to choose a column from that data to manipulate
-Then, use filter functions or transforms to manipulate the signal
-You can plot the current signal with the "plot" command.

Documented commands (type help <command>):
"""

data = None
column = None
signal = None
sample_rate = None

# ===============================================================================================================================
# CLI COMMANDS GO HERE
# ===============================================================================================================================

class PrePro_Cli(cmd.Cmd):
    intro = banner
    prompt = "pre-pro: "
    file = None
    doc_header = help_text

    def __init__(self):
        cmd.Cmd.__init__(self)

    def do_load(self, arg):
        "The start of the preprocessing workflow. Select the file which contains the data you want to process"
        global data
        global sample_rate

        if arg == '':
            print("No file specfied")
        elif not os.path.isfile(arg.strip("'")):
            print("Not a file")
        else:
            data = signal_utils._load_csv(arg.strip("'"))
            print(data.columns)  # TODO: pretty print this
            print("Data loaded!")
            sample_rate = signal_utils._get_sample_rate(data)
        return

    def do_select(self, arg):
        "Select the column you wish to manipulate. Makes a deep copy of the original so you are free to manipulate the signal while retaining a copy of the original."
        global signal

        # TODO: Should check if arg is an index to avoid errors
        if data is not None:
            # Make a true copy of the signal for manipulation
            signal = signal_utils._true_copy_arr(data[arg])
            print("Signal selected!")
        else:
            print("Please load data first")
        return

    def do_trim(self,arg):
        "Manually remove erroneous data from the start of the current signal AND the entire dataset"
        global data
        global signal

        if arg == '':
            print("No index specfied")
        elif int(arg) <= 0:
            print("Expected non-zero positive integer")
        elif data is None:
            print("Please load data first")
        else:
            index=int(arg)            
            # Truncate the pandas dataframe
            data=signal_utils._manual_trim(data,index)            
                                    
            # If there is a signal selected, truncate the said signal too. 
            if signal is not None:                
                signal=signal[index:]     
            print("Done.")          
        return

    def do_plot(self, arg):
        "Plot the current signal"
        if data is None:
            print("Please load data first")
        elif signal is None:
            print("Please select a signal first")
        else:
            plt.plot(signal)
            plt.show()
        return

    def do_showfs(self, arg):
        "Display the sampling frequency"
        if data is None:
            print("Please load data first")
        else:
            print(sample_rate)
        return

    def do_lowpass(self, arg):
        """Apply a (Chebyshev II) lowpass filter with the specified parameters.
usage: lowpass \x1B[3mFILTER_ORDER\x1B[0m \x1B[3mSTOP_BAND_ATTENUATION\x1B[0m \x1B[3mCORNER_FREQUENCY\x1B[0m
ex: lowpass 30 40 20"""
        global signal

        if data is None:
            print("Please load data first")
        elif signal is None:
            print("Please select a signal first")
        else:
            args = arg.split()
            y = preprocessing._lowpass(signal, int(args[0]), int(args[1]), int(args[2]), sample_rate)

            plt.plot(y)
            plt.show()

            if (input("Keep Changes? (y/n): ") == 'y'):
                signal = y
                print("changes applied")
            else:
                print("changes discarded")
        return

    def do_cleanecg(self, arg):
        "Uses neurokit2 to clean an ECG signal with the Elgendi method"
        global signal

        if data is None:
            print("Please load data first")
        elif signal is None:
            print("Please select a signal first")
        else:
            y = preprocessing._cleanECG(signal, sample_rate)

            plt.plot(y)
            plt.show()

            if (input("Keep Changes? (y/n): ") == 'y'):
                signal = y
                print("changes applied")
            else:
                print("changes discarded")
        return

    def do_cleanppg(self, arg):
        "Uses neurokit2 to clean a PPG signal with the Elgendi method"
        global signal

        if data is None:
            print("Please load data first")
        elif signal is None:
            print("Please select a signal first")
        else:
            y = preprocessing._cleanPPG(signal, sample_rate)

            plt.plot(y)
            plt.show()

            if (input("Keep Changes? (y/n): ") == 'y'):
                signal = y
                print("changes applied")
            else:
                print("changes discarded")
        return
    
    def do_butter(self, arg):
        """Apply a Butterworth lowpass filter with the specified parameters.
usage: lowpass  \x1B[3mCORNER_FREQUENCY\x1B[0m
ex: butter 4"""
        global signal

        if data is None:
            print("Please load data first")
        elif signal is None:
            print("Please select a signal first")
        else:
            args = arg.split()
            y = preprocessing._butter(signal, int(args[0]), sample_rate)

            plt.plot(y)
            plt.show()

            if (input("Keep Changes? (y/n): ") == 'y'):
                signal = y
                print("changes applied")
            else:
                print("changes discarded")
        return

    def do_sqi(self,arg):
        "Prints the signal quality index. Meant for ECG signals"
        print(signal_utils._sqi(signal,sample_rate))
        return

    def do_segment(self,arg):
        "Get individual heart beats"
        global signal

        alpha = signal_utils._seg(signal,sample_rate)
        num = len(alpha)
        kSQ = np.zeros([num,1])
        pSQ = np.zeros([num,1])
        lastvalue=0

        for acc in range(1,num,1):
            stnum = str(acc)
            signal  = alpha[stnum]["Signal"]

            kSQI = signal_utils._kSQI(signal)
            kSQ[acc - 1] = kSQI
            pSQI = signal_utils._ecg_quality_pSQI(signal, sampling_rate=sample_rate)
            pSQ[acc - 1] = pSQI

            #print(f"kSQI:{kSQI}   pSQI:{pSQI}")

        #Getting the best 10 pulses
        for i in range(len(kSQ)):
            if int(kSQ[i]) > 6.0:
                if (kSQ[i+1] > 6) & (kSQ[i+2] > 6) & (kSQ[i+2] > 6)& (kSQ[i+3] > 6) & (kSQ[i+4] > 6) &(kSQ[i + 5] > 6) & (kSQ[i+6] > 6) & (kSQ[i+7] > 6)& (kSQ[i+8] > 6) & (kSQ[i+9] > 6):
                    lastvalue=i
                    break
        j=0
        number = len(alpha["1"]["Signal"])
        tenpulse = np.zeros([number*10, 1])
        #for j in range(1310):
        for ac2 in range(lastvalue+1,lastvalue+11,1):
            sig = alpha[str(ac2)]["Signal"]
            for val in sig:
                tenpulse[j] = val
                j = j + 1

        #print(tenpulse)
        signal = tenpulse
        print(len(signal))
        return
    
    def do_write(self, arg):
        "Writes the current signal to a file in a machine readable format"
        if data is None:
            print("Please load data first")
        elif signal is None:
            print("Please select a signal first")
        else:
            # TODO: Implement this
            print("This command is not implemented yet")
        return

    def do_quit(self, arg):
        "Quit and exit the program"
        return True

    def do_dump(self, arg):
        "A function for debugging. Prints all the values in the current signal"
        signal_utils._dump(signal)

    def do_wavelet(self, arg):
        "Applies wavelet filtering to the signal"
        global signal

        if data is None:
            print("Please load data first")
        elif signal is None:
            print("Please select a signal first")
        else:
            y = preprocessing._wavelet(signal)
            plt.plot(y)
            plt.show()

            if (input("Keep Changes? (y/n): ") == 'y'):
                signal = y
                print("changes applied")
            else:
                print("changes discarded")
        return

    def do_decompose(self, arg):
        "Gets the morphological based features of a signal"
        #cD1, cD2, cA = feature_extraction._decompose(signal)
        #yin = np.append(cA, cD1)
        #yin = np.append(yin, cD2)
        yin = feature_extraction._decompose(signal)
        print(yin)
        return

    def do_entropy(self, arg):
        "Entropy based features"
        y = signal
        value = feature_extraction._sample_entropy(signal)
        print(value)
        return

    def do_skew(self, arg):
        "Calculate the skew of the signal"
        value = feature_extraction._skew(signal)
        print(value)
        return

    def do_kurt(self, arg):
        "Kurtosis of the signal"
        value = feature_extraction._kurt(signal)
        print(value)
        return

    def do_rr_interval(self,arg):
        "RR Interval of an ECG signal"
        print(feature_extraction._rr_interval(signal,sample_rate))

    def do_pat(self,arg):
        "pulse arrival time (between a PPG sys. peak and an ECG R peak)"
        print(feature_extraction._pulse_arrival_time(data,sample_rate,"Red"))
        return

    def do_extract(self,arg):
        "extracts 'em all. First dialog is the directory with data, second dialog is the csv with measured bp."    
        global data
        global sample_rate
        global signal     

        num_err=0
        num_ppg=0
        num_ecg=0
        num_missing=0
        num_empty=0        
        
        root = tk.Tk()
        root.withdraw()               

        csv_dir= filedialog.askdirectory() 
        bp_filepath=filedialog.askopenfilename()        

        # Open the spreadsheet with true blood pressure measurements
        bp_data = read_csv(bp_filepath.strip("'"), delimiter=",")

        # Create an output dataframe with every available feature, a column for systolic pressure, diastolic pressure, and signal type 
        #ecg_columns=['Filename', 'SBP', 'DBP', 'HR', 'HRV', 'RR', 'PAT', 'ENT', 'SKEW', 'KURT',
        #'D1','D2','D3','D4','D5','D6','D7','D8','D9','D10','D11','D12','D13','D14','D15','D16','D17','D18',
        #'D19','D20','D21','D22','D23','D24','D25','D26','D27','D28','D29','D30','D31','D32','D33','D34']
        ecg_columns = ['Filename', 'SBP', 'DBP', 'HR', 'HRV', 'RR', 'PAT', 'ENT', 'SKEW', 'KURT']
        ecg_dataframe=DataFrame(columns=ecg_columns)

        #TODO: ppg dataframe

        # For every file in the directory (Assuming a flat file hierarchy) 
        dir_list = os.listdir(csv_dir)   
        files = [f for f in dir_list if f.endswith(".csv")]

        for file in files:  

            print("Now Extracting: " + file)

            # Try to load the CSV into a dataframe
            try:
                data = signal_utils._load_csv(os.path.join(csv_dir,file))
                sample_rate = signal_utils._get_sample_rate(data)                
                    
                # Get the real bp measurement
                real_bp=bp_data[bp_data["Filename"].str.contains(file.strip(".csv"),regex=False)]                
                
                # Check for validity. We'll see what checks we REALLY need when the automation breaks :)
                if data.empty:
                    print("Empty data file!")
                    num_empty+=1
                    continue
                elif real_bp.empty:
                    print("No measured blood pressure found!")
                    num_missing+=1
                    continue      

                # Extract different features based on the signal type.
                if "ECG" in data.columns:                
                    print("ECG data file")                    

                    # Temporary dataframe for holding features as they are calculated
                    temp_df=DataFrame(columns=ecg_columns)

                    # Evaluate SQI  
                    signal = preprocessing._cleanECG(data["ECG"], sample_rate)                    
                    if signal_utils._sqi(signal,sample_rate) < 0.7:
                        print("Poor quality signal. Skipping.")
                        continue
                                       
                    # Get features 
                    # TODO: FEATURES WHICH USE SAMPLE RATE ARE BORKED!
                    temp_df.at[0,'HR']= 1/feature_extraction._rr_interval(signal,sample_rate)*60
                    temp_df.at[0,'HRV']=0  #TODO
                    temp_df.at[0,'RR']=feature_extraction._rr_interval(signal,sample_rate)
                    temp_df.at[0,'PAT']=feature_extraction._pulse_arrival_time(data,sample_rate,"Red")
                    temp_df.at[0,'ENT']=feature_extraction._sample_entropy(signal)
                    temp_df.at[0,'SKEW']=feature_extraction._skew(signal)
                    temp_df.at[0,'KURT']=feature_extraction._kurt(signal)
                    
                    #D=feature_extraction._decompose(signal)
                    #for x in range(1,34):
                     #   temp_df.at[0,'D'+str(x)]=D[x]

                    # Add the filename and true blood pressure to the temporary dataframe
                    temp_df.at[0,'Filename']=file
                    temp_df.at[0,'SBP']=real_bp.get('SBP').item()
                    temp_df.at[0,'DBP']=real_bp.get('DBP').item()

                    # Append to output dataframe
                    ecg_dataframe=ecg_dataframe.append(temp_df)
                    num_ecg+=1

                elif "Green" in data.columns:
                    print("PPG data file") 
                    
                    #TODO: Evaluate the ppg qulity
                    #TODO: get ppg
                    num_ppg+=1
                    continue     
                else:
                    print("Couldn't find an the expected columns")
                    continue          
            except KeyError:
                # This happens when the time column cannot be found in the sample rate calculation. TODO: Need to resolve this
                num_err+=1
                print("Keyerror!")                
            except ValueError:
                # This happens when there are duplicate entries in the blood pressure spreadsheet. TODO: Need to remove them from the spreadsheet
                num_err+=1
                print("Value error!")            

        # Write the output dataframe to a csv
        ecg_dataframe.to_csv("ecg_Features.csv")

        #TODO write ppg dataframe

        print("\nnumber of errors: " + str(num_err))
        print("number of signals w/o blood pressure: " + str(num_missing))
        print("number of empty files: " + str(num_empty))
        print("number of ppg files: " + str(num_ppg))
        print("number of ecg files: " + str(num_ecg))        

        return

def main():
    cli = PrePro_Cli()
    cli.cmdloop()

if __name__ == "__main__":
    main()