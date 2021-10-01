# Installation instructions:
The goalis to demostrate the Phenix API using ChimeraX as the client

## Instructions
#### Get a branch of Phenix with preliminary ChimeraX integration
##### Option1: Git clone the branch fresh
1. cd phenix/modules/
2. mv phenix phenix.bak0
3. git clone https://github.com/phenix-project/phenix.git --depth=1 --branch=chimerax-integration

##### Option2: Switch to the new branch if already using git
1. cd phenix/modules/phenix
2. git pull
3. git switch chimerax-integration

#### Install ChimeraX bundle
1. git clone https://github.com/phenix-project/phenix-api.git
2. cd clients/chimerax-phenix-pyro
3. export RELEASE=1 (for me, following the instructions from Tristan here: https://github.com/tristanic/chimerax-phenix
4. make app-install

#### Set up tutorial
1. New project in Phenix GUI
2. Set up tutorial data
3. Choose the Cryo-EM>Refinement>Fragment MamK
4. Run Cryo-EM Comprehensive Validation
5. Open in Chimerax (the outliers should be clickable)


## Notes
Because I used Tristan's existing chimerax-phenix bundle as a template, there might be conflicts. (The command phenix connect for example). It is probably best to uninstall that bundle first if it is currently installed.
