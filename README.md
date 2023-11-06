# FEMbyGEN
A FreeCAD module that uses Generative Design to calculate and show structural analysis results

![alt text](https://mightybucket.github.io/pics/masters-dissertation/process2.png)**from Rahul Master Thesis Poster**

This project was devoloped based on [Rahul](https://github.com/MightyBucket/) Master's thesis and [Ogeday Yavuz](https://github.com/OgedaYY/) Graduation Thesis. To get more information about Rahul thesis click [here](https://mightybucket.github.io/projects/2021/05/31/masters-dissertation.html).

## Installation instructions

This folder contains the code for a workbench plug-in for FreeCAD. Therefore you must have FreeCAD installed to use it.
FreeCAD 0.20 can be downloaded for free from https://www.freecadweb.org/

You can install it by addon manager in the FreeCAD or you can add this webpage address to Edit > Preferences > Addon Manager > Custom repository in Freecad. Second method after downloading this repository and  manually copy the 'FembyGen' folder to the user 'Mod' directory for FreeCAD. This is normally found in the following directory:

in Windows:
`C:\Users\*UserName*\AppData\Roaming\FreeCAD\Mod

in Linux
/home/*UserName*/.local/FreeCAD/Mod
Where `UserName` is replaced with the name of your user profile.

Once copied, start up FreeCAD. From the workbench selection drop down menu in the top middle of the window, you should see the option for "FEMbyGEN". Selecting this will activate the workbench. All of the functions will work out of the box.

## Usage

Create a Fem simulation in Freecad by using classical procedure which described freecad fem wiki pages. This file  will be your master simulation. 

Then you can open fembygen workbench. First button for initialization. It will create a spreadsheet which name is Parameters. 
You can open it and write your parameters and number of generations. Then you can click second button to alias parameter names and dimensions. You can assign your dimensions by classical spreadsheet definition. Freecad wiki and youtube can help you how to define it.

After then everything is easy, just click generate button, to create your new generations. You can check the files simply by clicking table in Gui.

Then you can use Fea button to fem simulations of all created generations. 

You can check all results by clicking results button. You can open the generated files by clicking table rows of results Gui. And all results also will come to master file, you can check tree view for that.

It offers also a suggesting optimum geometry for your boundry conditions. By clicking creategeo button, You can choose your boundries such as supports, pressures,forces and the function will create an optimum body for you.

By clicking toplogy button you can run a topology optimization analysis. 

## Requirements
- scipy
