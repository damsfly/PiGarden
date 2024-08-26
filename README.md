# PiGarden
This program manages the watering of the garden and the greenhouse (tomatoes)
by controlling the water level in the cisterns and the moisture content of the soil.
The data are stored in a database. A Flask front-end controls watering and generates statistics.
Watering is scheduled to start twice a day, depending on the following conditions:
-If the moisture content of the tomato soil is 62% or higher, the greenhouse is not watered.
-If garden soil humidity is 62% or higher, garden watering does not take place.
-For both zones, the duration of watering is calculated according to the moisture content of the soil.
If the cisterns are not full enough, the water network is used.
If there's a problem with the PLC that obtains the soil moisture content, an e-mail is sent.
This program controls a Raspberry Pi 4b which operates solenoid valves, a pump and an ultrasonic distance sensor.
4 buttons are used to water the garden, water the tomatoes, activate the water in a tap and stop watering.
The front-end can control the Raspberry with the same functions as the physical buttons. 
System status (watering in progress, which zone, from which water source) and tank water levels are monitored.
All weather data are stored in an SQL database.
