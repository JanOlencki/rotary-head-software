# Rotary Head for Antenna Measurement
This repository is a part of the Rotary Head project. It was developed at the [Gdańsk University of Technology](https://pg.edu.pl/en). 
The other parts of the project can be found in the following repositories:
- [rotary-head-electronics](https://github.com/JanOlencki/rotary-head-electronics)
- [rotary-head-mechanics](https://github.com/JanOlencki/rotary-head-mechanics)
- [rotary-head-firmware](https://github.com/JanOlencki/rotary-head-firmware)

There is the article titled ["A Low-Cost System for Far-Field Non-Anechoic Measurements of Antenna Performance Figures"](https://ieeexplore.ieee.org/document/10103864) which discusses results obtained using Rotary Heads.

# Software for Automating Measurements

## Repository contents
All software is written in Python. The repository contains the following items:
- Rotary Head driver
- *Anritsu MS20xxC* driver
- Command Line Interface program
- Example script
 
## Usage

### CLI
You can use the CLI (Command Line Interface) by running `python -m antenna_meas_cli.cli` command. All available options are listed in the features section and can be explored using the `--help` switch added to the command.

#### Features
- Listing available devices (both Rotary Tables and VNAs)
- Automatic measurement of an antenna characteristic
- Save measurement to a S2P file
- Live display of the measurement on the plot
- Stop the Rotary Table on program exit

### Example script
[The example script](/src/example.py) can be found in `src/` directory. It performs the following actions:
- initializes communication with the Rotary Table and the VNA,
- prepares both devices for a measurement,
- takes a measurement of an antenna characteristic,
- rotates an antenna back to its home position. 

## Dependencies
- Python *v3.9*
- NI-VISA driver *v21.0* (https://www.ni.com/pl-pl/support/downloads/drivers/download.ni-visa.html#409839)

### Python packages
- pyvisa *v1.11*
- scikit-rf *v0.19*
- click *v8.0*
- crc8 *v0.1*
- pyserial *v3.5*
- pytest *v6.2* (only for a testing purpose)
