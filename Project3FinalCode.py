import sys
sys.path.append('../')
from Common.project_library import *

# Modify the information below according to you setup and uncomment the entire section

# 1. Interface Configuration
project_identifier = 'P3B' # enter a string corresponding to P0, P2A, P2A, P3A, or P3B
ip_address = '169.254.195.158' # enter your computer's IP address
hardware = False # True when working with hardware. False when working in the simulation

# 2. Servo Table configuration
short_tower_angle = 270 # enter the value in degrees for the identification tower 
tall_tower_angle = 90 # enter the value in degrees for the classification tower
drop_tube_angle = 180#270# enter the value in degrees for the drop tube. clockwise rotation from zero degrees

# 3. Qbot Configuration
bot_camera_angle = 0 # angle in degrees between -21.5 and 0

# 4. Bin Configuration
# Configuration for the colors for the bins and the lines leading to those bins.
# Note: The line leading up to the bin will be the same color as the bin 

bin1_offset = 0.15 # offset in meters
bin1_color = [1,0,0] # e.g. [1,0,0] for red
bin2_offset = 0.15
bin2_color = [0,1,0]
bin3_offset = 0.15
bin3_color = [0,0,1]
bin4_offset = 0.15
bin4_color = [1,0,1]

#--------------- DO NOT modify the information below -----------------------------

if project_identifier == 'P0':
    QLabs = configure_environment(project_identifier, ip_address, hardware).QLabs
    bot = qbot(0.1,ip_address,QLabs,None,hardware)
    
elif project_identifier in ["P2A","P2B"]:
    QLabs = configure_environment(project_identifier, ip_address, hardware).QLabs
    arm = qarm(project_identifier,ip_address,QLabs,hardware)

elif project_identifier == 'P3A':
    table_configuration = [short_tower_angle,tall_tower_angle,drop_tube_angle]
    configuration_information = [table_configuration,None, None] # Configuring just the table
    QLabs = configure_environment(project_identifier, ip_address, hardware,configuration_information).QLabs
    table = servo_table(ip_address,QLabs,table_configuration,hardware)
    arm = qarm(project_identifier,ip_address,QLabs,hardware)
    
elif project_identifier == 'P3B':
    table_configuration = [short_tower_angle,tall_tower_angle,drop_tube_angle]
    qbot_configuration = [bot_camera_angle]
    bin_configuration = [[bin1_offset,bin2_offset,bin3_offset,bin4_offset],[bin1_color,bin2_color,bin3_color,bin4_color]]
    configuration_information = [table_configuration,qbot_configuration, bin_configuration]
    QLabs = configure_environment(project_identifier, ip_address, hardware,configuration_information).QLabs
    table = servo_table(ip_address,QLabs,table_configuration,hardware)
    arm = qarm(project_identifier,ip_address,QLabs,hardware)
    bins = bins(bin_configuration)
    bot = qbot(0.1,ip_address,QLabs,bins,hardware)
    

#---------------------------------------------------------------------------------
# STUDENT CODE BEGINS
#---------------------------------------------------------------------------------

'''''
Dispenses a container and returns information about the weight and bin number
'''

def dispense_container():
    randNum = random.randint(1,6) #Spawns container with random ID from 1-6
    info = table.dispense_container(randNum,True)
    container_info = [info[1],int(info[2][4:])]
    return container_info #returns the weight and number portion of bin number

'''
Uses a set of tested coordinates and then
configures the arm to load containers with
the respective commands and the use of delay
'''
def load_container():
  home = (0.406,0,0.483) #Tested coordinates for important locations
  rotation = (0.0,-0.406,0.483) #This is for helping it rotate ninety degrees from pickup before it goes to dropoff
  pickup = (0.63,0,0.26)
  dropoff = (0,-0.479,0.462)

  arm.home()
  arm.move_arm(*pickup)  #asterisk is necessary to unpack tuple
  time.sleep(1.5) #Using time.sleep() between commands is essential to control flow
  arm.control_gripper(33)
  time.sleep(1.5)
  arm.move_arm(*home)
  time.sleep(1.5)
  arm.move_arm(*rotation)
  time.sleep(1.5)
  arm.move_arm(*dropoff)
  time.sleep(1.5)
  arm.control_gripper(-33)
  time.sleep(1.5)
  arm.home()
  
'''
Includes the followline algorithm and is currently hardcoded with time
If the left IR sensor doesn't detect the yellow line, the bot will drift
right to adjust and vice versa. Still need to implement short bursts of
movement
'''
def line_follow():
    left_reading,right_reading = bot.line_following_sensors()
    if bot.line_following_sensors() == [1,1]:
        bot.set_wheel_speed([0.1,0.1])
        time.sleep(0.1)
    elif (left_reading == 1 and right_reading == 0):
        bot.set_wheel_speed([0.02,0.04])
    elif (left_reading == 0 and right_reading == 1):
        bot.set_wheel_speed([0.04,0.02])
    elif (bot.line_following_sensors() == [0,0]): #All the others are self-explanatory, but this one turns left in the event that it gets off course
        bot.set_wheel_speed([0.05,0.17])
    else:
        bot.stop()
        
        

def transfer_container(bin_id):
    bot.activate_ultrasonic_sensor() #Combined use of ultrasonic and colour sensors
    bot.activate_color_sensor()
    dump_check = False
    if(bin_id == 1):
        destination = [1,0,0] #Conditional to determine what colour reading it should look for
    elif (bin_id == 2):
        destination = [0,1,0]
    elif (bin_id == 3):
        destination = [0,0,1]
    else:
        destination = [1,0,1]
    while dump_check == False:
        line_follow()
        distance = bot.read_ultrasonic_sensor()
        colour_sensor = bot.read_color_sensor()
        colour = colour_sensor[0]
        if destination == colour and distance <= 0.06: #Stop Condition is when bin colour is found and we are close enough
            bot.stop()
            drop_container()
            bot.deactivate_ultrasonic_sensor()
            bot.deactivate_color_sensor()
            dump_check = True
        else:
            pass
    bot.stop()    
    return_home()
   
    
'''
Used in combination with return home function to ensure that the bot
gets to the home position fairly consistently
'''
def return_home():
    BOT_HOME = (1.5,-0.025,0)
    thres = 0.05
    lower_bounds = (BOT_HOME[0] - thres, BOT_HOME[1]-thres) #Use a approximate area around end first to get it closer to home
    upper_bounds = (BOT_HOME[0] + thres, BOT_HOME[1]+thres)
    pos = bot.position()

    while True:
        line_data = bot.line_following_sensors()
        bot.set_wheel_speed([0.075,0.075])
        time.sleep(0.075)
        
        if (pos[0] >= lower_bounds[0] and pos[0] <= upper_bounds[0]) and (pos[1] >= lower_bounds[1] and pos[1] <= upper_bounds[1]):
            bot.stop()
            time.sleep(0.5)
            bot.forward_distance(0.075) #When close to home, move it slightly forward to adjust for next cycle
            time.sleep(0.5)
            break
        if line_data[1] == False:
            bot.set_wheel_speed([0.05, 0.13])
            time.sleep(0.05)
        if line_data[0] == False:
            bot.set_wheel_speed([0.09, 0.05])
            time.sleep(0.05)

        if line_data[0] == False and line_data[1] == False:
            bot.set_wheel_speed([0.05, 0.17])
            time.sleep(0.05)
        
        pos = bot.position()
        

'''
The linear actuator makes this function easier
'''        
def drop_container():
    bot.activate_linear_actuator() #Very simple process without having to turn right and then dump
    bot.dump()
    bot.deactivate_linear_actuator()


'''
Test Run to show TA 
'''            
def pickup(bin_id):
    weight = 0
    count = 0
        
    while (count<3) and (weight<=90):
        time.sleep(1)
        if ((table.load_cell_sensor(0.2)[0])!=0) and count == 0: #Checks if there is any previous container before dispensing which is important so two don't stack on top of each other
            load_container()
            count+=1
            weight+= table.load_cell_sensor(0.2)[0]
            current_container = dispense_container()
        elif count == 0:
            bin_id1 = dispense_container()
            load_container()
            count+=1
            weight += bin_id1[0]
            bin_id2 = dispense_container()
        elif count == 1 and bin_id[1] == current_container[1]:
            load_container()
            count+=1
            weight+= current_container[0]
            current_container = dispense_container()
            print(current_container)
        elif count == 2 and bin_id[1] == current_container[1]:
            load_container()
            count+=1
            weight += current_container[0]
            current_container = dispense_container()
        else:
            break
    return bin_id,current_container  
    
if __name__ == "__main__":
    first_id = dispense_container()   #The first container data storage to be sent to pickup function
    bin_id,current_container = pickup(first_id)
    print("The destination is Bin",bin_id[1])
    transfer_container(bin_id[1])
    while True:
        bin_id, current_container = pickup(current_container)
        transfer_container(bin_id[1])
     
#---------------------------------------------------------------------------------
# STUDENT CODE ENDS
#---------------------------------------------------------------------------------
