## FEMbyGEN
A FreeCAD module that uses Generative Design to calculate and show structural analysis results

### Background 
This project was developed based on [Rahul](https://github.com/MightyBucket/) Master's thesis and [Ogeday Yavuz](https://github.com/OgedaYY/) Graduation Thesis.  
[František Löffelmann](https://github.com/fandaL)'s [calculix/beso](https://github.com/calculix/beso) topology optimization script was added as a feature recently.  
The following process image is taken from [Master Thesis Poster of Rahul Jhuree](https://mightybucket.github.io/misc/FYP_poster.pdf):

<img src="https://mightybucket.github.io/pics/masters-dissertation/process1.png" width="668px" alt="Rahul Jhuree's generative design process" />

For more information about Rahul's thesis please view the [dissertation](https://mightybucket.github.io/projects/2021/05/31/masters-dissertation.html).

### Requirements
- scipy => 1.10.1
- [FreeCAD](https://www.freecad.org) => 0.20.0

### Installation
Recommended installation of the workbench is via the FreeCAD [Addon Manager](https://wiki.freecad.org/Std_AddonMgr).  
A restart of FreeCAD is required after installation.

### Usage

A starter guide exist in [forum post](https://forum.freecad.org/viewtopic.php?p=728205#p728205)

1. Create a FEM simulation in FreeCAD by using the [classical procedure](https://wiki.freecad.org/FEM_Workbench). This file will be your master simulation.
2. Open FEMbyGEN workbench. Press first toolbar icon for initialization. It will create a spreadsheet which name is `Parameters`. Open it and write your parameters for different generations.
3. Click the second toolbar icon to automatically alias parameter names and dimensions all at once.
4. Assign your aliased dimensions to sketch constraints or any other property fields using the [expressions editor](https://wiki.freecad.org/Expressions).
5. Click the **Generate** toolbar icon and then the `Generate` button to create new generations. Check the generation files by using the provided GUI or simply by clicking its table cell.
6. Use **FEA Generations** toolbar icon to generate FEM simulations of all created generations.
7. Check all results by clicking **Show Results** toolbar icon. Note: open the generated files by clicking table rows of results GUI. In addition, all results will append to the master file, check tree view for that.

#### Notes
The addon can also suggest optimum geometry for boundary conditions.

1. By clicking **Create Geo Generations** toolbar icon, the ability to choose boundaries such as supports, pressures, forces and the function will create an optimum body.
2. By clicking the **Topology** toolbar icon a topology optimization analysis will be executed.

### Feedback
Bug reports are greatly appreciated. Please open a ticket in this repository. Please remember to always add your full [About](https://wiki.freecad.org/About) info when opening a ticket (and make sure you're using the latest version of the addon). Feature requests can also be requested in this repository. Please consider logging into the FreeCAD [forum thread](https://forum.freecad.org/viewtopic.php?t=71905) dedicated to the FEMbyGEN addon to discuss your ideas with the devs.

### License
LGPLv2.1 ([LICENSE](LICENSE))
