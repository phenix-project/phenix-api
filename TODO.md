### Tentative goals for the October Phenix realease:
1. An open in ChimeraX button for core Cryo-EM GUI tasks (Comprehensive Validation, Real Space Refinement, Resolve Cryo-EM, Map to Model,Dock in map, etc)
2. Ligand fit functionality where the user is viewing the density in ChimeraX, and wants to run a Phenix program and have the results loaded when ready.

### Requires
1. Launching ChimeraX from Phenix reliably on multiple platforms
2. Robust Client/Server implementation (using Pyro) integrated into the current Phenix GUI
3. A Chimerax bundle that acts as a client for phenix (using Pyro)
4. API functionality to define scenes to view
5. API functionality to run a program and load results
6. A program template implementation of ligand fit.
