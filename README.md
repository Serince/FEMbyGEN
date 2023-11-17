## FEMbyGEN
A FreeCAD module that uses Generative Design to calculate and show structural analysis results

![diseration_poster](https://mightybucket.github.io/pics/masters-dissertation/process2.png)**from Rahul Master Thesis Poster**

### Background 
This project was devoloped based on [Rahul](https://github.com/MightyBucket/) Master's thesis and [Ogeday Yavuz](https://github.com/OgedaYY/) Graduation Thesis. 

For more information about Rahul thesis please read the [dissertation](https://mightybucket.github.io/projects/2021/05/31/masters-dissertation.html).

### Requirements
- scipy => 1.0.0
- [FreeCAD](https://freecadweb.org) => 0.19.0

FEMbyGEN has been tested on FreeCAD 0.20 and scipy 1.10.1

### Installation

Recommended installation is via the FreeCAD [Addon Manager](https://wiki.freecad.org/Std_AddonMgr). 

1. Tools → Addon manager
2. Find the **FEMbyGEN** addon. Install.
3. A restart prompt will display. Click Ok to restart FreeCAD.
5. Once FreeCAD reloads, find the [workbench selection drop down menu](https://wiki.freecad.org/Interface) in the top middle of the window, you should see the option for "**FEMbyGEN**. Selecting this will activate the workbench.

Result: All of the functions will work out of the box.

### Usage
1. Create a FEM simulation in Freecad by using the classical procedure described within wiki documentation. This file will be your master simulation. 
2. Open fembygen workbench. First button for initialization. It will create a spreadsheet which name is Parameters. You can open it and write your parameters and number of generations.
3. Then click the second button to alias parameter names and dimensions. Assign your dimensions by classical spreadsheet definition. Freecad wiki documentation and youtube can illustrate how this is done.
4. Click the generate button to create new generations. Check the files simply by clicking table in the FreeCAD UI.
5. Use FEA button to generate FEM simulations of all created generations.
6. Check all results by clicking results button. Note: open the generated files by clicking table rows of results GUI. In addition, all results will append to the master file, check tree view for that.

#### Notes
The addon will also suggest optimum geometry for boundry conditions. By clicking **Creategeo** button, the ability to choose boundries such as supports, pressures, forces, and the function will create an optimum body.

By clicking the **Topology** button a topology optimization analysis will be executed.

### Feedback
Bug reports are greatly appreciated. Please open a ticket in this repository. Please remember to always add your full [About](https://wiki.freecad.org/About) info when opening a ticket (and make sure you're using the latest version of the addon). Feature requests can also be requested in this repository. Please consider logging into the FreeCAD [forum thread]() dedicated to the FEMbyGEN addon to discuss your ideas with the devs.

### License
LGPLv2.1 ([LICENSE](LICENSE))
