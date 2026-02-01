import numpy as np
from pathlib import Path
import os
import uuid
import traceback
def npzSave(output, data):
    try:
        output_path = Path(output)
        if output_path.suffix in ['.npy', '.nc', '.h5', '.hdf5']:
            output_path = output_path.with_suffix('.npz')    
        output_path.parent.mkdir(parents=True, exist_ok=True)
        temp_filename = output_path.with_suffix(f'.tmp.{uuid.uuid4()}.npz')    
        np.savez_compressed(temp_filename, data=data)
        os.replace(temp_filename, output_path)   
        print(f"{output_path} done")
    except Exception as e:
        print(traceback.format_exc())
        if temp_filename and temp_filename.exists():
            try:
                os.remove(temp_filename)
                print(f"⚠ Temporary files have been cleared: {temp_filename}")
            except:
                pass            
def npzLoad(output_path):
    return np.load(Path(output_path).with_suffix('.npz'))['data']
"""
npzSave(output, data)
npzLoad(output_path)
"""