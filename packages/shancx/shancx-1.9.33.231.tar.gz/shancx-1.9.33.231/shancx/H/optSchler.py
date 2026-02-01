import torch.optim as optim
from torch.optim.lr_scheduler import StepLR, ReduceLROnPlateau
def getoptSchler(lr=3e-5,gamma=0.85)
     optimizer = optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
     # scheduler = ReduceLROnPlateau(optimizer, mode='min', factor=0.1, patience=5, verbose=True)
     scheduler = StepLR(optimizer, step_size=10, gamma=gamma)  #step_size=10, 
     return optimizer,scheduler 
"""
import torch.cuda.amp as amp  
scaler = amp.GradScaler()   
with amp.autocast():   
optimizer.zero_grad()
       scaler.scale(loss).backward()  
       scaler.step(optimizer)   
       scaler.update()   
current_lr = optimizer.param_groups[0]['lr']
writer.add_scalar('Learning_Rate/lr', current_lr, epoch)  
scheduler.step()   # scheduler.step(val_loss) 
"""