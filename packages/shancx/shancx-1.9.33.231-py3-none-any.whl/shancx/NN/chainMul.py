import subprocess
import time
import logging
import os
import argparse
import datetime
import traceback
from dateutil.relativedelta import relativedelta
import pandas as pd 
from shancx.NN import Mul_TH
from shancx.NN import _loggersPlus
from shancx.NN import cleanupLogs
from shancx.sendM import sendMES
BASE_DIR = '/mnt/wtx_weather_forecast/scx/sever7/product_log_scx/code06_re2_cp1/exam/mk_trainsatRadarMSG1'
PYTHON_ENV = '/home/scx/miniconda3/envs/mqpf/bin/python'
DEFAULT_GPU = '0'
DEFAULT_TIMEOUT = 2400
SCRIPT_DELAY = 2
# minutedict = {"20":8,"30":6,"40":4,"50":2,"0":0}   
minutedict = {"0": 0 }   
class PipelineExecutor:  
    def __init__(self, UTC, sat_cd, gpu=DEFAULT_GPU):
        self.UTCstr = UTC.strftime("%Y%m%d%H%M")
        self.sat_cd = sat_cd
        self.gpu = gpu
        self.produce_time= self.producetime(UTC)
        self.scripts = self._initialize_scripts()    
    def producetime(self,UTC):   
        _minute = UTC.minute
        _minute = minutedict.get(str(_minute),None)
        if _minute is not None :
            start_time = UTC - relativedelta(minutes=_minute)  # "20":8 indicates that the step 2 command is executed at the 12-minute mark, which is between 20 and 10 minutes.
            return start_time
        else:
            return None
    def _initialize_scripts(self):
        #step 1 command 
        scripts = [            
            {
                'name': 'MSGsat',
                'cmd': f"cd {os.path.join(BASE_DIR, 'makeMSGnc')} && {PYTHON_ENV} MSGsat.py --times {self.UTCstr[:12]}",
                'timeout': DEFAULT_TIMEOUT
            }
        ]
        #step 2 command 
        if self.produce_time is not None:
            times_str = self.produce_time.strftime("%Y%m%d%H%M")[:12]
            scripts.extend([
                            #   {
                            #       'name': 'mainSAT',
                            #       'cmd': f"cd {os.path.join('/mnt/wtx_weather_forecast/scx', 'mqpf_GEOSH9SEAStestCal')} && {PYTHON_ENV} mainSAT.py --times {times_str[:12]} --satcd H9SEAS --sepSec 360 --gpu '{self.gpu}' --isOverwrite --classer 'WT_RTH9SEAS'",
                            #       'timeout': DEFAULT_TIMEOUT
                            #   },
                            #   {
                            #       'name': 'mainSAT',
                            #       'cmd': f"cd {os.path.join('/mnt/wtx_weather_forecast/scx', 'mqpf_GEOSH9SEAStestCal')} && {PYTHON_ENV} mainSAT.py --times {times_str[:12]} --satcd H9CHNNEAS --sepSec 360 --gpu '{self.gpu}' --isOverwrite --classer 'WT_RTH9OC'",
                            #       'timeout': DEFAULT_TIMEOUT
                            #   },
                            #   {
                            #       'name': 'mainSAT',
                            #       'cmd': f"cd {os.path.join('/mnt/wtx_weather_forecast/scx', 'mqpf_GEOSH9SEAStestCal')} && {PYTHON_ENV} mainSAT.py --times {times_str[:12]} --satcd H9OC --sepSec 360 --gpu '{self.gpu}' --isOverwrite --classer 'WT_RTH9CHNNEAS'",
                            #       'timeout': DEFAULT_TIMEOUT
                            #   },
                            # #   [
                            # #     #  {
                            # #     #   'name': 'satPzlSATREF',
                            # #     #   'cmd': f"cd {os.path.join(BASE_DIR, 'SawPuz')} && {PYTHON_ENV} satPzlSAT.py --times {times_str[:12]} --satcd '{self.sat_cd}' --mqpf_cd 'REF'",
                            # #     #   'timeout': DEFAULT_TIMEOUT
                            # #     #  },
                            # #     #  {
                            # #     #   'name': 'satPzlSATQPF',
                            # #     #   'cmd': f"cd {os.path.join(BASE_DIR, 'SawPuz')} && {PYTHON_ENV} satPzlSAT.py --times {times_str[:12]} --satcd '{self.sat_cd}' --mqpf_cd 'QPF' --isUpload ",
                            # #     #   'timeout': DEFAULT_TIMEOUT  
                            # #     #  }    
                            # #   ] 
                           ])
        else:
            logger.warning("produce_time is None, skipping mainSAT, satPzlSATREF and satPzlSATQPF command execution")        
        return scripts
    def execute_script(self, conf): 
        script_info = conf[0] 
        script_name = script_info['name']
        timeout = script_info['timeout']      
        logger.info(f"Starting to execute script: {script_name}")       
        try:
            result = subprocess.run(
                                     script_info['cmd'],
                                     shell=True,
                                     timeout=timeout,
                                     check=False,  
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE,
                                     text=True
                                   )            
            if result.returncode != 0:
                logger.error(f"Script {script_name} execution failed, return code: {result.returncode}")
                if result.stdout.strip():
                    logger.error(f"Output before failure:\n{result.stdout}")
                if result.stderr.strip():
                    logger.error(f"Error output:\n{result.stderr}")
                logger.error(f"Traceback:\n{traceback.format_exc()}")
                return False            
            # Success case
            if result.stdout.strip():
                logger.debug(f"[{script_name}] Output:\n{result.stdout}")
            if result.stderr.strip():
                logger.warning(f"[{script_name}] Warning output:\n{result.stderr}")               
            logger.info(f"Script {script_name} executed successfully")
            return True            
        except Exception as e:
            logger.error(f"Script {script_name} execution exception: {str(e)}")
            logger.error(f"Traceback:\n{traceback.format_exc()}")
            sendMES(f"{traceback.format_exc()} ",NN="MT1")
            return False    
    def run_pipeline(self):
        """Execute complete script pipeline"""
        logger.info(f"Starting to process time slot: {self.UTCstr}, satellite: {self.sat_cd}")        
        for i, script in enumerate(self.scripts, 1): 
            if isinstance(script, list):  
                logger.info(f"Executing step {i}/{len(self.scripts)}: satPzlSAT") 
                Mul_TH(self.execute_script,[script])
            else:   
                logger.info(f"Executing step {i}/{len(self.scripts)}: {script['name']}")     
                if not self.execute_script((script,)):
                    logger.error(f"Pipeline interrupted at {script['name']}, processing failed")
                    return False
            if i < len(self.scripts):
                time.sleep(SCRIPT_DELAY)        
        logger.info(f"Time slot {self.UTCstr} processing completed")
        return True
def main(conf): 
    utc,sat_cd,gpu = conf[0],conf[1],conf[2]
    executor = PipelineExecutor(utc, sat_cd, gpu)
    return executor.run_pipeline()
def options():
    parser = argparse.ArgumentParser(description='Pipeline Cascade time command execution')
    parser.add_argument('--times', type=str, default='202412010000,202508010000') 
    parser.add_argument('--sat_cd', type=str, default='MSG') 
    parser.add_argument('--gpu', type=str, default='0')
    config= parser.parse_args()
    print(config)
    config.times = config.times.split(",")
    if len(config.times) == 1:
        config.times = [config.times[0], config.times[0]]
    config.times = [datetime.datetime.strptime(config.times[0], "%Y%m%d%H%M"),
                    datetime.datetime.strptime(config.times[1], "%Y%m%d%H%M")]
    return config
if __name__ == "__main__":
    cfg = options()
    sUTC = cfg.times[0]
    eUTC = cfg.times[-1]
    sat_cd  = cfg.sat_cd
    gpu =cfg.gpu
    sUTCstr = sUTC.strftime("%Y%m%d%H%M")
    dir_ = f"./logs/{sat_cd}"
    logger = _loggersPlus(root = dir_ , phase=f"{sUTCstr}_Pipeline")
    from shancx.NN import cleanupLogs
    stats = cleanupLogs(dir_,30, '*.log', False, False) 
    logging.info(f"clean={stats['total_dirs']}, cleanfile={stats['deleted_files']}, error={len(stats['errors'])}") 

    timeList = pd.date_range(sUTC, eUTC, freq='30min')
    # filtered_times = [t for t in timeList if t.hour  % 4 == 0 and t.minute == 0]  #t.mintues
    # result_times = []
    # for t in filtered_times:
    #     result_times.extend(pd.date_range(t - pd.Timedelta(minutes=30), t, freq='10T')) 
    # for UTC in result_times:
    #     main((UTC,sat_cd,gpu))
    Mul_TH(main,[timeList,[sat_cd],[gpu]],2)




 
 
 
