# GROUP - 10 - Scalable Project 3 - Deep-Water Exploration Through Satellite-Based Communication

## Group Members

- Abdullah Bin Omer Zia - 24333366
- Proteeti Kushari - 24333831
- Koray Yeşilova - 24357678
- Yuejia Liu - 24356593

## Project Overview

### Project Objective

- To simulate real-time communication with satellites, focusing on inter-device message relaying and simulated realistic failures

### Project Components

- Ship Devices
  - Zigzag patterned movement
  - Relevant data generation
  - Communication with Ground Control via Satellites
- Satellite Devices
  - Dynamic orbit path for movement simulated
  - Relay messages between Ships and Ground Control
- Ground Control
  - Communicates with the Ship devices
  - Consolidated received data into an output file

### Algorithms and Key Features

- Nearest-neighbor discovery for identification of satellites
- Haversine formula to calculate distance between devices
- Randomized failure simulation on satellite response and acknowledgement points

## Instructions to run the project

## ToDo

```
+ Ship movement fix -> Goes out of celtic sea and onto land, set an area and redefine movement. 
    - Initial position should be further south.
- Message actually sending properly:
    + Decrease the frequency of messages being sent
    - New values should relate to previous values
    + Visualisation to show message being sent as well.
    - Redefine communication range (increase)
    - ? Ground control should be peer as well - send responses to the ship (maybe ship only sends next message once previous is ack-ed?)
- "Realistic" Aspects:
    - Random delays (done but maybe increase time to exaggerate?)
    - Unexpected failures (x% of time) - new stop satellites script - stop a satellite based on port number on command
    - Corrupted messages? How to find out? Checksum?
- Get it to work on two Pis
- Hardcoded IPs and ports in a lot of files - fix them
```
