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

'''
   Objectives
   ----------
. Need to randomize the containers that spawn
. Need to check the weight condition and 3 bottle condition when loading
. Need to implement the use of colour sensor when arriving at a bin
. Need to add the small corrections in container placement (for example,
  we can move the arm a bit back after placing a container on the bot and
  make it close its gripper and then move back forward which would push the
  previous container that was put a bit farther in
. Lastly, need to add the small angle adjustments after the bot returns home
. Might also need to check weight on the hopper and implement that in the
  dump function so that if a container is still left on the bot, it doesn't
  continue moving

'''

'''
Dispenses a container and returns information about the weight and bin number
'''

def dispense_container():
    randNum = random.randint(1,6)
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
  bot_home = (1.5,0,0)
  pickup = (0.63,0,0.26)
  dropoff = (0,-0.6,0.55)

  arm.move_arm(*pickup)  
  time.sleep(1) #Using time.sleep() between commands is essential to control flow
  arm.control_gripper(40)
  time.sleep(1)
  arm.move_arm(*dropoff)
  time.sleep(1)
  arm.control_gripper(-40)
  time.sleep(1)
  arm.move_arm(0.25,-0.3,0.5)
  time.sleep(1)
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
    else:
        bot.stop()
        
        

def transfer_container(bin_id):
    bot.activate_ultrasonic_sensor()
    bot.activate_color_sensor()
    dump_check = False
    if(bin_id == "1"):
        destination = [1,0,0]
    elif (bin_id == "2"):
        destination = [0,1,0]
    elif (bin_id == "3"):
        destination = [0,0,1]
    else:
        destination = [1,0,1]
    while dump_check == False:
        line_follow()
        distance = bot.read_ultrasonic_sensor()
        colour_sensor = bot.read_color_sensor()
        colour = colour_sensor[0]
        if destination == colour and distance <= 0.05:
            bot.stop()
            drop_container()
            bot.deactivate_ultrasonic_sensor()
            bot.deactivate_color_sensor()
            dump_check = True
        else:
            pass
    
    
'''
Used in combination with return home function to ensure that the bot
gets to the home position fairly consistently
'''
def pos():
    BOT_HOME = (1.5,0,0)
    pos = bot.position()
    for i in range(3):
        if abs(pos[i]-BOT_HOME[i])>0.1:
            return False
    return True
'''
Uses the position method rather than time to return home
'''

def return_home():
     home_reached = pos()
     while home_reached == False:
         line_follow()
         home_reached = pos()
         if home_reached == True:
             break
   
            
'''
The linear actuator makes this function easier
'''        
def drop_container():
    bot.activate_linear_actuator() #need to switch to rotational
    bot.dump()
    bot.deactivate_linear_actuator()


'''
Test Run to show TA 
'''            
def main():
    new_container = []
    weight = 0
    condition = True
    while condition:
        current_container = dispense_container()
        time.sleep(1)
        print(current_container)
        new_container.append(current_container)
        weight += new_container[0][0]
        print(weight)
        current_bin = new_container[0][1]
        load_container()
        time.sleep(1)
        current_container = dispense_container()
        print(current_container)
        new_container.append(current_container)
        weight += new_container[1][0]
        print(weight)
        current_bin_two = new_container[1][1]
        if (current_bin_two == current_bin) and (weight < 90):
            load_container()
            time.sleep(1)
            current_container = dispense_container()
            time.sleep(1)
            print(current_container)
            new_container.append(current_container)
            weight += new_container[2][0]
            print(weight)
            current_bin_three = new_container[2][1]
            if (current_bin_three == current_bin) and (weight < 90):
                load_container()
            else:
                condition = False
        else:
            condition = False
    transfer_container(current_bin)
    drop_container()
    return_home()
        
        
    

main()


#---------------------------------------------------------------------------------
# STUDENT CODE ENDS
#---------------------------------------------------------------------------------
