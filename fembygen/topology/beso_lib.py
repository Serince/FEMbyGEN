import numpy as np
import operator
from math import *
import os

def QT_TRANSLATE_NOOP(context, text):
    return text
import FreeCADGui
import FreeCAD
FreeCADGui.addLanguagePath(os.path.join(FreeCAD.getUserAppDataDir(),"\Mod\FEMbyGEN\fembygen\translations"))
FreeCADGui.updateLocale()

class Elements:
    def __init__(self):
        self.tria3 = {}
        self.tria6 = {}
        self.quad4 = {}
        self.quad8 = {}
        self.tetra4 = {}
        self.tetra10 = {}
        self.hexa8 = {}
        self.hexa20 = {}
        self.penta6 = {}
        self.penta15 = {}

    def __iter__(self):
        self.elements = [self.tria3, self.tria6, self.quad4, self.quad8, self.tetra4,
                         self.tetra10, self.hexa8, self.hexa20, self.penta6, self.penta15]
        self.current_index = 0
        return self

    def __next__(self):
        if self.current_index < len(self.elements):
            current_element = self.elements[self.current_index]
            self.current_index += 1
            return current_element
        else:
            raise StopIteration


class BesoLib_types:

    def types(elm_type):
        if elm_type in ["S3", "CPS3", "CPE3", "CAX3", "M3D3"]:
            number_of_nodes = 3
            only_translations = False
            elm_category = "tria3"
        elif elm_type in ["S6", "CPS6", "CPE6", "CAX6", "M3D6"]:
            number_of_nodes = 6
            only_translations = False
            elm_category = "tria6"
        elif elm_type in ["S4", "S4R", "CPS4", "CPS4R", "CPE4", "CPE4R", "CAX4", "CAX4R", "M3D4", "M3D4R"]:
            number_of_nodes = 4
            only_translations = False
            elm_category = "quad4"
        elif elm_type in ["S8", "S8R", "CPS8", "CPS8R", "CPE8", "CPE8R", "CAX8", "CAX8R", "M3D8", "M3D8R"]:
            number_of_nodes = 8
            only_translations = False
            elm_category = "quad8"
        elif elm_type == "C3D4":
            number_of_nodes = 4
            only_translations = True
            elm_category = "tetra4"
        elif elm_type == "C3D10":
            number_of_nodes = 10
            only_translations = True
            elm_category = "tetra10"
        elif elm_type in ["C3D8", "C3D8R", "C3D8I"]:
            number_of_nodes = 8
            only_translations = True
            elm_category = "hexa8"
        elif elm_type in ["C3D20", "C3D20R", "C3D20RI"]:
            number_of_nodes = 20
            only_translations = True
            elm_category = "hexa20"
        elif elm_type == "C3D6":
            number_of_nodes = 6
            only_translations = True
            elm_category = "penta6"
        elif elm_type == "C3D15":
            number_of_nodes = 15
            only_translations = True
            elm_category = "penta15"
        elif elm_type == ["B31", "B31R", "T3D2"]:
            number_of_nodes = 2
            only_translations = False
            elm_category = "line2"
        elif elm_type == ["B32", "B32R", "T3D3"]:
            number_of_nodes = 3
            only_translations = False
            elm_category = "line3"
        elif elm_type in ["CPE3", "CPE6", "CPE4", "CPE4R", "CPE8", "CPE8R"]:
            number_of_nodes = None
            only_translations = False
            elm_category = "plane strain"
        elif elm_type in ["CPS3", "CPS6", "CPS4", "CPS4R", "CPS8", "CPS8R"]:
            number_of_nodes = None
            only_translations = False
            elm_category = "plane stress"
        elif elm_type in ["CAX3", "CAX6", "CAX4", "CAX4R", "CAX8", "CAX8R"]:
            number_of_nodes = None
            only_translations = False
            elm_category = "axisymmetry"
        else:
            elm_category = ""
            if (shells_as_composite is True) and (elm_type in ["S3", "S4", "S4R", "S8"]):
                msg = ("\nERROR: " + elm_type + "element type found. CalculiX might need S6 or S8R elements for "
                                                "composite\n")
                print(msg)
                BesoLib_types.write_to_log(file_name, msg)
            return
        return number_of_nodes, only_translations, elm_category

# function to print ongoing messages to the log file


    def write_to_log(file_name, msg):
        f_log = open(file_name[:-4] + ".log.fcmacro", "a")
        f_log.write(msg)
        f_log.close()


# function importing a mesh consisting of nodes, volume and shell elements
    def import_inp(file_name, domains_from_config, domain_optimized, shells_as_composite):
        nodes = {}  # dict with nodes position
        all_elements = Elements()
        model_definition = True
        domains = {}
        read_domain = False
        read_node = False
        elm_category = []
        elm_2nd_line = False
        elset_generate = False
        special_type = ""  # for plane strain, plane stress, or axisymmetry
        plane_strain = set()
        plane_stress = set()
        axisymmetry = set()

        try:
            f = open(file_name, "r")
        except IOError:
            msg = ("CalculiX input file " + file_name + " not found. Check your inputs.")
            BesoLib_types.write_to_log(file_name, "\nERROR: " + msg + "\n")
            raise Exception(msg)
        line = "\n"
        include = ""
        while line != "":
            if include:
                line = f_include.readline()
                if line == "":
                    f_include.close()
                    include = ""
                    line = f.readline()
            else:
                line = f.readline()
            if line.strip() == '':
                continue
            elif line[0] == '*':  # start/end of a reading set
                if line[0:2] == '**':  # comments
                    continue
                if line[:8].upper() == "*INCLUDE":
                    start = 1 + line.index("=")
                    include = line[start:].strip().strip('"')
                    f_include = open(os.path.join(os.path.split(file_name)[0] + f"/{include}"), "r")
                    continue
                read_node = False
                elm_category = []
                elm_2nd_line = False
                read_domain = False
                elset_generate = False

            # reading nodes
            if (line[:5].upper() == "*NODE") and (model_definition is True):
                read_node = True
            elif read_node is True:
                line_list = line.split(',')
                number = int(line_list[0])
                x = float(line_list[1])
                y = float(line_list[2])
                z = float(line_list[3])
                nodes[number] = [x, y, z]

            # reading elements
            elif line[:8].upper() == "*ELEMENT":
                current_elset = ""
                line_list = line[8:].split(',')
                for line_part in line_list:
                    if line_part.split('=')[0].strip().upper() == "TYPE":
                        elm_type = line_part.split('=')[1].strip().upper()
                    elif line_part.split('=')[0].strip().upper() == "ELSET":
                        current_elset = line_part.split('=')[1].strip()
                number_of_nodes, only_translations, elm_category = BesoLib_types.types(elm_type)

            elif elm_category != []:
                line_list = line.split(',')
                if elm_2nd_line is False:
                    en = int(line_list[0])  # element number
                    if current_elset:  # save en to the domain
                        try:
                            domains[current_elset].add(en)
                        except KeyError:
                            domains[current_elset] = {en}
                    if elm_category == "plane strain":
                        plane_strain.add(en)
                    elif elm_category == "plane stress":
                        plane_stress.add(en)
                    elif elm_category == "axisymmetry":
                        axisymmetry.add(en)
                    getattr(all_elements, elm_category)[en] = [int(x) for x in line_list[1:]]
                    if len(getattr(all_elements, elm_category)[en]) != number_of_nodes:
                        elm_2nd_line = True
                else:
                    elm_2nd_line = False
                    getattr(all_elements, elm_category)[en] += [int(x) for x in line_list]

            # reading domains from elset
            elif line[:6].upper() == "*ELSET":
                line_split_comma = line.split(",")
                if "=" in line_split_comma[1]:
                    name_member = 1
                    try:
                        if "GENERATE" in line_split_comma[2].upper():
                            elset_generate = True
                    except IndexError:
                        pass
                else:
                    name_member = 2
                    if "GENERATE" in line_split_comma[1].upper():
                        elset_generate = True
                member_split = line_split_comma[name_member].split("=")
                current_elset = member_split[1].strip()
                try:
                    domains[current_elset]
                except KeyError:
                    domains[current_elset] = set()
                if elset_generate is False:
                    read_domain = True
            elif read_domain is True:
                for en in line.split(","):
                    en = en.strip()
                    if en.isdigit():
                        domains[current_elset].add(int(en))
                    elif en.isalpha():  # else: en is name of a previous elset
                        domains[current_elset].update(domains[en])
            elif elset_generate is True:
                line_split_comma = line.split(",")
                try:
                    if line_split_comma[3]:
                        en_generated = list(range(int(line_split_comma[0]), int(line_split_comma[1]) + 1,
                                                int(line_split_comma[2])))
                except IndexError:
                    en_generated = list(range(int(line_split_comma[0]), int(line_split_comma[1]) + 1))
                domains[current_elset].update(en_generated)

            elif line[:5].upper() == "*STEP":
                model_definition = False
        f.close()

        for dn in domains:
            domains[dn] = list(domains[dn])
        en_all = []
        opt_domains = []
        all_available = False
        for dn in domains_from_config:
            if dn.upper() == "ALL_AVAILABLE":
                all_available = True
                continue
            try:
                en_all.extend(domains[dn])
            except KeyError:
                msg = "Element set '{}' not found in the inp file.".format(dn)
                BesoLib_types.write_to_log(file_name, "\nERROR: " + msg + "\n")
                raise Exception(msg)
            if domain_optimized[dn] is True:
                opt_domains.extend(domains[dn])
        msg = ("domains: %.f\n" % len(domains_from_config))

        if all_available:  # domain called all_available will contain rest of the elements
            en_all2 = set()
            en_all2 = en_all2.union(all_elements.tria3.keys(), all_elements.tria6.keys(), all_elements.quad4.keys(), all_elements.quad8.keys(),
                                    all_elements.tetra4.keys(), all_elements.tetra10.keys(), all_elements.hexa8.keys(), all_elements.hexa20.keys(),
                                    all_elements.penta6.keys(), all_elements.penta15.keys())

            domain_elements = all_elements
            domains["all_available"] = en_all2 - set(en_all)
            opt_domains.extend(domains["all_available"])
            en_all = list(en_all2)
        else:
            domain_elements = Elements()
            # only elements in domains_from_config are stored, the rest is discarded
            keys = set(en_all).intersection(set(all_elements.tria3.keys()))
            domain_elements.tria3 = {k: all_elements.tria3[k] for k in keys}
            keys = set(en_all).intersection(set(all_elements.tria6.keys()))
            domain_elements.tria6 = {k: all_elements.tria6[k] for k in keys}
            keys = set(en_all).intersection(set(all_elements.quad4.keys()))
            domain_elements.quad4 = {k: all_elements.quad4[k] for k in keys}
            keys = set(en_all).intersection(set(all_elements.quad8.keys()))
            domain_elements.quad8 = {k: all_elements.quad8[k] for k in keys}
            keys = set(en_all).intersection(set(all_elements.tetra4.keys()))
            domain_elements.tetra4 = {k: all_elements.tetra4[k] for k in keys}
            keys = set(en_all).intersection(set(all_elements.tetra10.keys()))
            domain_elements.tetra10 = {k: all_elements.tetra10[k] for k in keys}
            keys = set(en_all).intersection(set(all_elements.hexa8.keys()))
            domain_elements.hexa8 = {k: all_elements.hexa8[k] for k in keys}
            keys = set(en_all).intersection(set(all_elements.hexa20.keys()))
            domain_elements.hexa20 = {k: all_elements.hexa20[k] for k in keys}
            keys = set(en_all).intersection(set(all_elements.penta6.keys()))
            domain_elements.penta6 = {k: all_elements.penta6[k] for k in keys}
            keys = set(en_all).intersection(set(all_elements.penta15.keys()))
            domain_elements.penta15 = {k: all_elements.penta15[k] for k in keys}
            en_all = list(domain_elements.tria3.keys()) + list(domain_elements.tria6.keys()) + list(domain_elements.quad4.keys()) + \
                list(domain_elements.quad8.keys()) + list(domain_elements.tetra4.keys()) + list(domain_elements.tetra10.keys()) + \
                list(domain_elements.hexa8.keys()) + list(domain_elements.hexa20.keys()) + list(domain_elements.penta6.keys()) + \
                list(domain_elements.penta15.keys())

        msg += ("nodes  : %.f\nTRIA3  : %.f\nTRIA6  : %.f\nQUAD4  : %.f\nQUAD8  : %.f\nTETRA4 : %.f\nTETRA10: %.f\n"
                "HEXA8  : %.f\nHEXA20 : %.f\nPENTA6 : %.f\nPENTA15: %.f\n"
                % (len(nodes), len(domain_elements.tria3), len(domain_elements.tria6), len(domain_elements.quad4), len(domain_elements.quad8),
                len(domain_elements.tetra4), len(domain_elements.tetra10), len(
                    domain_elements.hexa8), len(domain_elements.hexa20),
                len(domain_elements.penta6), len(domain_elements.penta15)))
        print(msg)
        BesoLib_types.write_to_log(file_name, msg)

        if not opt_domains:
            row = "None optimized domain has been found. Check your inputs."
            msg = ("\nERROR: " + row + "\n")
            BesoLib_types.write_to_log(file_name, msg)
            assert False, row

        return nodes, domain_elements, domains, opt_domains, en_all, plane_strain, plane_stress, axisymmetry


# function for computing volumes or area (shell elements) and centres of gravity
# approximate for 2nd order elements!
class elm_volume_cg:
    def  __init__(self,file_name, nodes, Elements):
        self.file_name= file_name
        self.nodes= nodes
        self.Elements= Elements
        self.u = [0.0, 0.0, 0.0]
        self.v = [0.0, 0.0, 0.0]
        self.w = [0.0, 0.0, 0.0]

    def tria_area_cg(self,nod):
        # Compute volume
        for i in range(3):
            self.u[i] = self.nodes[nod[2]][i] - self.nodes[nod[1]][i]
            self.v[i] = self.nodes[nod[0]][i] - self.nodes[nod[1]][i]
        area_tria = np.linalg.norm(np.cross(self.u, self.v)) / 2.0
        # Compute centre of gravity
        x_cg = sum(self.nodes[n][0] for n in nod) / 3.0
        y_cg = sum(self.nodes[n][1] for n in nod) / 3.0
        z_cg = sum(self.nodes[n][2] for n in nod) / 3.0
        cg_tria = [x_cg, y_cg, z_cg]
        return area_tria, cg_tria

    def tetra_volume_cg(self,nod):
        # Compute volume
        for i in range(3):
            self.u[i] = self.nodes[nod[2]][i] - self.nodes[nod[1]][i]
            self.v[i] = self.nodes[nod[3]][i] - self.nodes[nod[1]][i]
            self.w[i] = self.nodes[nod[0]][i] - self.nodes[nod[1]][i]
        volume_tetra = abs(np.dot(np.cross(self.u, self.v), self.w)) / 6.0
        # Compute centre of gravity
        x_cg = sum(self.nodes[n][0] for n in nod) / 4.0
        y_cg = sum(self.nodes[n][1] for n in nod) / 4.0
        z_cg = sum(self.nodes[n][2] for n in nod) / 4.0
        cg_tetra = [x_cg, y_cg, z_cg]
        return volume_tetra, cg_tetra

    def second_order_info(self,elm_type):
        msg = "\nINFO: areas and centres of gravity of " + elm_type.upper() + " elements ignore mid-nodes' positions\n"
        print(msg)
        
    def elm_volume_cg(self):

        # defining volume and centre of gravity for all element types
        volume_elm = {}
        area_elm = {}
        cg = {}

        for en, nod in self.Elements.tria3.items():
            [area_elm[en], cg[en]] = self.tria_area_cg(nod)

        if self.Elements.tria6:
            self.second_order_info("tria6")
        for en, nod in self.Elements.tria6.items():  # copy from tria3
            [area_elm[en], cg[en]] = self.tria_area_cg(nod)

        for en, nod in self.Elements.quad4.items():
            [a1, cg1] = self.tria_area_cg(nod[0:3])
            [a2, cg2] = self.tria_area_cg(nod[0:1] + nod[2:4])
            area_elm[en] = float(a1 + a2)
            cg[en] = [[], [], []]
            for k in [0, 1, 2]:  # denote x, y, z dimensions
                cg[en][k] = (a1 * cg1[k] + a2 * cg2[k]) / area_elm[en]

        if self.Elements.quad8:
            self.second_order_info("quad8")
        for en, nod in self.Elements.quad8.items():  # copy from quad4
            [a1, cg1] = self.tria_area_cg(nod[0:3])
            [a2, cg2] = self.tria_area_cg(nod[0:1] + nod[2:4])
            area_elm[en] = float(a1 + a2)
            cg[en] = [[], [], []]
            for k in [0, 1, 2]:  # denote x, y, z dimensions
                cg[en][k] = (a1 * cg1[k] + a2 * cg2[k]) / area_elm[en]

        for en, nod in self.Elements.tetra4.items():
            [volume_elm[en], cg[en]] = self.tetra_volume_cg(nod)

        if self.Elements.tetra10:
            self.second_order_info("tetra10")
        for en, nod in self.Elements.tetra10.items():  # copy from tetra4
            [volume_elm[en], cg[en]] = self.tetra_volume_cg(nod)

        for en, nod in self.Elements.hexa8.items():
            [v1, cg1] = self.tetra_volume_cg(nod[0:3] + nod[5:6])
            [v2, cg2] = self.tetra_volume_cg(nod[0:1] + nod[2:3] + nod[4:6])
            [v3, cg3] = self.tetra_volume_cg(nod[2:3] + nod[4:7])
            [v4, cg4] = self.tetra_volume_cg(nod[0:1] + nod[2:5])
            [v5, cg5] = self.tetra_volume_cg(nod[3:5] + nod[6:8])
            [v6, cg6] = self.tetra_volume_cg(nod[2:5] + nod[6:7])
            volume_elm[en] = float(v1 + v2 + v3 + v4 + v5 + v6)
            cg[en] = [[], [], []]
            for k in [0, 1, 2]:  # denote x, y, z dimensions
                cg[en][k] = (v1 * cg1[k] + v2 * cg2[k] + v3 * cg3[k] + v4 * cg4[k] + v5 * cg5[k] + v6 * cg6[k]
                            ) / volume_elm[en]

        if self.Elements.hexa20:
            self.second_order_info("hexa20")
        for en, nod in self.Elements.hexa20.items():  # copy from hexa8
            [v1, cg1] = self.tetra_volume_cg(nod[0:3] + nod[5:6])
            [v2, cg2] = self.tetra_volume_cg(nod[0:1] + nod[2:3] + nod[4:6])
            [v3, cg3] = self.tetra_volume_cg(nod[2:3] + nod[4:7])
            [v4, cg4] = self.tetra_volume_cg(nod[0:1] + nod[2:5])
            [v5, cg5] = self.tetra_volume_cg(nod[3:5] + nod[6:8])
            [v6, cg6] = self.tetra_volume_cg(nod[2:5] + nod[6:7])
            volume_elm[en] = float(v1 + v2 + v3 + v4 + v5 + v6)
            cg[en] = [[], [], []]
            for k in [0, 1, 2]:  # denote x, y, z dimensions
                cg[en][k] = (v1 * cg1[k] + v2 * cg2[k] + v3 * cg3[k] + v4 * cg4[k] + v5 * cg5[k] + v6 * cg6[k]
                            ) / volume_elm[en]

        for en, nod in self.Elements.penta6.items():
            [v1, cg1] = self.tetra_volume_cg(nod[0:4])
            [v2, cg2] = self.tetra_volume_cg(nod[1:5])
            [v3, cg3] = self.tetra_volume_cg(nod[2:6])
            volume_elm[en] = float(v1 + v2 + v3)
            cg[en] = [[], [], []]
            for k in [0, 1, 2]:  # denote x, y, z dimensions
                cg[en][k] = (v1 * cg1[k] + v2 * cg2[k] + v3 * cg3[k]) / volume_elm[en]

        if self.Elements.penta15:
            self.second_order_info("penta15")  # copy from penta6
        for en, nod in self.Elements.penta15.items():
            [v1, cg1] = self.tetra_volume_cg(nod[0:4])
            [v2, cg2] = self.tetra_volume_cg(nod[1:5])
            [v3, cg3] = self.tetra_volume_cg(nod[2:6])
            volume_elm[en] = float(v1 + v2 + v3)
            cg[en] = [[], [], []]
            for k in [0, 1, 2]:  # denote x, y, z dimensions
                cg[en][k] = (v1 * cg1[k] + v2 * cg2[k] + v3 * cg3[k]) / volume_elm[en]

        # finding the minimum and maximum cg position
        x_cg = []
        y_cg = []
        z_cg = []
        for xyz in cg.values():
            x_cg.append(xyz[0])
            y_cg.append(xyz[1])
            z_cg.append(xyz[2])
        cg_min = [min(x_cg), min(y_cg), min(z_cg)]
        cg_max = [max(x_cg), max(y_cg), max(z_cg)]

        return cg, cg_min, cg_max, volume_elm, area_elm



# function for copying .inp file with additional elsets, materials, solid and shell sections, different output request
# elm_states is a dict of the elements containing 0 for void element or 1 for full element
class write_inp:

    def __init__(self,file_name, file_nameW, elm_states, number_of_states, domains, domains_from_config, domain_optimized,
            domain_thickness, domain_offset, domain_orientation, domain_material, domain_volumes, domain_shells,
            plane_strain, plane_stress, axisymmetry, save_iteration_results, i, reference_points, shells_as_composite,
            optimization_base, displacement_graph, domain_FI_filled):
        self.file_name=file_name
        self.file_nameW=file_nameW
        self.elm_states=elm_states
        self.number_of_states=number_of_states
        self.domains=domains
        self.domains_from_config=domains_from_config
        self.domain_optimized=domain_optimized
        self.domain_thickness=domain_thickness
        self.domain_offset=domain_offset
        self.domain_orientation=domain_orientation
        self.domain_material=domain_material
        self.domain_volumes=domain_volumes
        self.domain_shells=domain_shells
        self.plane_strain=plane_strain
        self.plane_stress=plane_stress
        self.axisymmetry=axisymmetry
        self.save_iteration_results=save_iteration_results
        self.save_iteration_results=save_iteration_results
        self.i=i
        self.reference_points=reference_points
        self.shells_as_composite=shells_as_composite
        self.optimization_base=optimization_base
        self.displacement_graph=displacement_graph
        self.domain_FI_filled=domain_FI_filled
        
        if self.reference_points == "nodes":
            self.fR = open(self.file_name[:-4] + "_separated.inp", "r")
        else:
            self.fR = open(self.file_name, "r")
        self.fW = open(self.file_nameW + ".inp", "w", newline="\n")
        
    # function for writing ELSETs of each state

    def write_elset(self):
        self.fW.write(" \n")
        self.fW.write("** Added ELSETs by optimization:\n")
        for self.dn in self.domains_from_config:
            if self.domain_optimized[self.dn] is True:
                self.elsets_used[self.dn] = []
                self.elset_new[self.dn] = {}
                for self.sn in range(self.number_of_states):
                    self.elset_new[self.dn][self.sn] = []
                    for en in self.domains[self.dn]:
                        if self.elm_states[en] == self.sn:
                            self.elset_new[self.dn][self.elm_states[en]].append(en)
                for self.sn, en_list in self.elset_new[self.dn].items():
                    if en_list:
                        self.elsets_used[self.dn].append(self.sn)
                        self.fW.write("*ELSET,ELSET=" + self.dn + str(self.sn) + "\n")
                        position = 0
                        for en in en_list:
                            if position < 8:
                                self.fW.write(str(en) + ", ")
                                position += 1
                            else:
                                self.fW.write(str(en) + ",\n")
                                position = 0
                        self.fW.write("\n")
        self.fW.write(" \n")
        # all available elsets together
        if "all_available" in self.domains.keys():
            self.fW.write(" \n")
            self.fW.write("*ELSET,ELSET=all_available\n")
            position = 0
            for en in self.domains["all_available"]:
                if position < 8:
                    self.fW.write(str(en) + ", ")
                    position += 1
                else:
                    self.fW.write(str(en) + ",\n")
                    position = 0
            self.fW.write("\n")

    # function to add orientation to solid or shell section
    def add_orientation(self):
        try:
            self.fW.write(", ORIENTATION=" + self.domain_orientation[self.dn][self.sn] + "\n")
        except (KeyError, IndexError):
            self.fW.write("\n")
    def write_inp_function(self):

        elsets_done = 0
        sections_done = 0
        outputs_done = 1
        commenting = False
        self.elset_new = {}
        self.elsets_used = {}
        msg_error = ""
        for line in self.fR:
            if line[0] == "*":
                commenting = False

            # writing ELSETs
            if (line[:6].upper() == "*ELSET" and elsets_done == 0) or (line[:5].upper() == "*STEP" and elsets_done == 0):
                self.write_elset()
                elsets_done = 1

            # optimization materials, solid and shell sections
            if line[:5].upper() == "*STEP" and sections_done == 0:
                if elsets_done == 0:
                    self.write_elset()
                    elsets_done = 1

                self.fW.write(" \n")
                self.fW.write("** Materials and sections in optimized domains\n")
                self.fW.write("** (redefines elements properties defined above):\n")
                for dn in self.domains_from_config:
                    if self.domain_optimized[dn]:
                        print(self.elsets_used)
                        for sn in self.elsets_used[dn]:
                            print(sn)

                            self.fW.write("*MATERIAL, NAME=" + dn + str(sn) + "\n")
                            self.fW.write(
                                f'*ELASTIC\n{self.domain_material[dn][0]:.6}, {self.domain_material[dn][1]:.6}\n*DENSITY\n{self.domain_material[dn][2]:.6}\n*CONDUCTIVITY')
                            self.fW.write(
                                f'\n{self.domain_material[dn][3]:.6}\n*EXPANSION\n{self.domain_material[dn][4]:.6}\n*SPECIFIC HEAT\\n{self.domain_material[dn][5]:.6}\n')

                            if self.domain_volumes[dn]:
                                self.fW.write("*SOLID SECTION, ELSET=" + dn + str(sn) + ", MATERIAL=" + dn + str(sn))
                                self.add_orientation()
                            elif len(self.plane_strain.intersection(self.domain_shells[dn])) == len(self.domain_shells[dn]):
                                self.fW.write("*SOLID SECTION, ELSET=" + dn + str(sn) + ", MATERIAL=" + dn + str(sn))
                                self.add_orientation()
                                self.fW.write(str(self.domain_thickness[dn][sn]) + "\n")
                            elif self.plane_strain.intersection(self.domain_shells[dn]):
                                msg_error = dn + " domain does not contain only plane strain types for 2D elements"
                            elif len(self.plane_stress.intersection(self.domain_shells[dn])) == len(self.domain_shells[dn]):
                                self.fW.write("*SOLID SECTION, ELSET=" + dn + str(sn) + ", MATERIAL=" + dn + str(sn))
                                self.add_orientation()
                                self.fW.write(str(self.domain_thickness[dn][sn]) + "\n")
                            elif self.plane_stress.intersection(self.domain_shells[dn]):
                                msg_error = dn + " domain does not contain only plane stress types for 2D elements"
                            elif len(self.axisymmetry.intersection(self.domain_shells[dn])) == len(self.domain_shells[dn]):
                                self.fW.write("*SOLID SECTION, ELSET=" + dn + str(sn) + ", MATERIAL=" + dn + str(sn))
                                self.add_orientation()
                            elif self.axisymmetry.intersection(self.domain_shells[dn]):
                                msg_error = dn + " domain does not contain only axisymmetry types for 2D elements"
                            elif self.shells_as_composite is True:
                                self.fW.write("*SHELL SECTION, ELSET=" + dn + str(sn) + ", OFFSET=" + str(self.domain_offset[dn]) +
                                        ", COMPOSITE")
                                self.add_orientation()
                                # 0.1 + 0.8 + 0.1 of thickness, , material name
                                self.fW.write(str(0.1 * self.domain_thickness[dn][sn]) + ",," + dn + str(sn) + "\n")
                                self.fW.write(str(0.8 * self.domain_thickness[dn][sn]) + ",," + dn + str(sn) + "\n")
                                self.fW.write(str(0.1 * self.domain_thickness[dn][sn]) + ",," + dn + str(sn) + "\n")
                            else:
                                self.fW.write("*SHELL SECTION, ELSET=" + dn + str(sn) + ", MATERIAL=" + dn + str(sn) +
                                        ", OFFSET=" + str(self.domain_offset[dn]))
                                self.add_orientation()
                                self.fW.write(str(self.domain_thickness[dn][sn]) + "\n")
                            self.fW.write(" \n")
                            if msg_error:
                                BesoLib_types.write_to_log(self.file_name, "\nERROR: " + msg_error + "\n")
                                raise Exception(msg_error)
                sections_done = 1

            if line[:5].upper() == "*STEP":
                outputs_done -= 1

            # output request only for element stresses in .dat file:
            if line[0:10].upper() == "*NODE FILE" or line[0:8].upper() == "*EL FILE" or \
                    line[0:13].upper() == "*CONTACT FILE" or line[0:11].upper() == "*NODE PRINT" or \
                    line[0:9].upper() == "*EL PRINT" or line[0:14].upper() == "*CONTACT PRINT":
                if outputs_done < 1:
                    self.fW.write(" \n")
                    if self.optimization_base in ["stiffness", "buckling"]:
                        for dn in self.domains_from_config:
                            self.fW.write("*EL PRINT, " + "ELSET=" + dn + "\n")
                            self.fW.write("ENER\n")
                    if self.optimization_base == "heat":
                        for dn in self.domains_from_config:
                            self.fW.write("*EL PRINT, " + "ELSET=" + dn + ", FREQUENCY=1000" + "\n")
                            self.fW.write("HFL\n")
                    if (self.reference_points == "integration points") and (self.domain_FI_filled is True):
                        for dn in self.domains_from_config:
                            self.fW.write("*EL PRINT, " + "ELSET=" + dn + "\n")
                            self.fW.write("S\n")
                    elif self.reference_points == "nodes":
                        self.fW.write("*EL FILE, GLOBAL=NO\n")
                        self.fW.write("S\n")
                    if self.displacement_graph:
                        ns_written = []
                        for [ns, component] in self.displacement_graph:
                            if ns not in ns_written:
                                ns_written.append(ns)
                                self.fW.write("*NODE PRINT, NSET=" + ns + "\n")
                                self.fW.write("U\n")
                    self.fW.write(" \n")
                    outputs_done += 1
                commenting = True
                if not self.save_iteration_results or np.mod(float(self.i - 1), self.save_iteration_results) != 0:
                    continue
            elif commenting is True:
                if not self.save_iteration_results or np.mod(float(self.i - 1), self.save_iteration_results) != 0:
                    continue

            self.fW.write(line)
        self.fR.close()
        self.fW.close()

# function for importing results from .dat file
# Failure Indices are computed at each integration point and maximum or average above each element is returned
def import_FI_int_pt(reference_value, file_nameW, domains, criteria, domain_FI, file_name, elm_states,
                     domains_from_config, steps_superposition, displacement_graph):
    
    try:
        f = open(file_nameW + ".dat", "r")
    except IOError:
        msg = "CalculiX result file not found, check your inputs, (make sure that your folder path/name does not contains any spaces)"
        BesoLib_types.write_to_log(file_name, "\nERROR: " + msg + "\n")
        assert False, msg
    last_time = "initial"  # TODO solve how to read a new step which differs in time
    step_number = -1
    criteria_elm = {}  # {en1: numbers of applied criteria, en2: [], ...}
    FI_step = []  # list for steps - [{en1: list for criteria FI, en2: [], ...}, {en1: [], en2: [], ...}, next step]
    energy_density_step = []  # list for steps - [{en1: energy_density, en2: ..., ...}, {en1: ..., ...}, next step]
    energy_density_eigen = {}  # energy_density_eigen[eigen_number][en_last] = np.average(ener_int_pt)
    heat_flux = {}  # only for the last step

    memorized_steps = set()  # steps to use in superposition
    if steps_superposition:
        # {sn: {en: [sxx, syy, szz, sxy, sxz, syz], next element with int. pt. stresses}, next step, ...}
        step_stress = {}
        step_ener = {}  # energy density {sn: {en: ener, next element with int. pt. stresses}, next step, ...}
        for LCn in range(len(steps_superposition)):
            for (scale, sn) in steps_superposition[LCn]:
                sn -= 1  # step numbering in CalculiX is from 1, but we have it 0 based
                memorized_steps.add(sn)
                step_stress[sn] = {}
                step_ener[sn] = {}

    # prepare FI dict from failure criteria
    for dn in domain_FI:
        if domain_FI[dn]:
            for en in domains[dn]:
                cr = []
                for dn_crit in domain_FI[dn][elm_states[en]]:
                    cr.append(criteria.index(dn_crit))
                criteria_elm[en] = cr

    def compute_FI(sxx, syy, szz, sxy, syz, sxz, criteria_elm, criteria, FI_int_pt):
        for en in criteria_elm:
            if en in criteria_elm:
                criteria_en = criteria[en]
                for FIn in criteria_elm[en]:
                    criterion_type, criterion_value = criteria_en[FIn]
                    if criterion_type == "stress_von_Mises":
                        s_allowable = criterion_value
                        s_diff_sq_sum = 0.5 * ((sxx - syy) ** 2 + (syy - szz) ** 2 + (szz - sxx) ** 2 +
                                           6 * (sxy ** 2 + syz ** 2 + sxz ** 2))
                        FI = np.sqrt(s_diff_sq_sum) / s_allowable
                        FI_int_pt[FIn].append(FI)
                    elif criterion_type == "user_def":
                        FI_int_pt[FIn].append(eval(criterion_value))
                    else:
                        msg = f"\nError: failure criterion {criteria[FIn]} not recognized.\n"
                        BesoLib_types.write_to_log(file_name, msg)
    def save_FI(sn, en):
        FI_step[sn][en] = []
        for FIn in range(len(criteria)):
            FI_step[sn][en].append(None)
            if FIn in criteria_elm[en]:
                if reference_value == "max":
                    FI_step[sn][en][FIn] = max(FI_int_pt[FIn])
                elif reference_value == "average":
                    FI_step[sn][en][FIn] = np.average(FI_int_pt[FIn])

    read_stresses = 0
    read_energy_density = 0
    read_heat_flux = 0
    read_displacement = 0
    disp_i = [None for _ in range(len(displacement_graph))]
    disp_condition = {}
    disp_components = []
    read_buckling_factors = 0
    buckling_factors = []
    read_eigenvalues = 0
    for line in f:
        line_split = line.split()
        if line.replace(" ", "") == "\n":
            if read_stresses == 1:
                save_FI(step_number, en_last)
            if read_energy_density == 1:
                if read_eigenvalues:
                    energy_density_eigen[eigen_number][en_last] = np.average(ener_int_pt)
                else:
                    energy_density_step[step_number][en_last] = np.average(ener_int_pt)
            if read_heat_flux == 1:
                heat_flux[en_last] = np.average(heat_int_pt)
            if read_displacement == 1:
                for cn in ns_reading:
                    try:
                        disp_i[cn] = max([disp_i[cn]] + disp_condition[cn])
                    except TypeError:
                        disp_i[cn] = max(disp_condition[cn])
            read_stresses -= 1
            read_energy_density -= 1
            read_heat_flux -= 1
            read_displacement -= 1
            read_buckling_factors -= 1
            FI_int_pt = [[] for _ in range(len(criteria))]
            ener_int_pt = []
            heat_int_pt = []
            en_last = None

        elif line[:9] == " stresses":
            if line.split()[-4] in map(lambda x: x.upper(), domains_from_config):  # TODO upper already on user input
                read_stresses = 2
                if last_time != line_split[-1]:
                    step_number += 1
                    FI_step.append({})
                    energy_density_step.append({})
                    if steps_superposition:
                        disp_components.append({})  # appending sn
                    last_time = line_split[-1]
                    read_eigenvalues = False  # TODO not for frequencies?
        elif line[:24] == " internal energy density":
            if line.split()[-4] in map(lambda x: x.upper(), domains_from_config):  # TODO upper already on user input
                read_energy_density = 2
                if last_time != line_split[-1]:
                    step_number += 1
                    FI_step.append({})
                    energy_density_step.append({})
                    if steps_superposition:
                        disp_components.append({})  # appending sn
                    last_time = line_split[-1]
                    read_eigenvalues = False  # TODO not for frequencies?

        elif line[:10] == " heat flux":
            if line.split()[-4] in map(lambda x: x.upper(), domains_from_config):  # TODO upper already on user input
                read_heat_flux = 2

        elif line[:48] == "     B U C K L I N G   F A C T O R   O U T P U T":
            read_buckling_factors = 3
        elif read_buckling_factors == 1:
            buckling_factors.append(float(line_split[1]))
        elif line[:54] == "                    E I G E N V A L U E    N U M B E R":
            eigen_number = int(line_split[-1])
            read_eigenvalues = True
            energy_density_eigen[eigen_number] = {}

        elif line[:14] == " displacements":
            cn = 0
            ns_reading = []
            for [ns, component] in displacement_graph:
                if ns.upper() == line_split[4]:
                    ns_reading.append(cn)
                    disp_condition[cn] = []
                cn += 1
            read_displacement = 2
            if steps_superposition:
                if last_time != line_split[-1]:
                    step_number += 1
                    disp_components.append({})  # appending sn
                    FI_step.append({})
                    energy_density_step.append({})
                    last_time = line_split[-1]
                ns = line_split[4]
                disp_components[-1][ns] = []  # appending ns

        elif read_stresses == 1:
            en = int(line_split[0])
            if en_last != en:
                if en_last:
                    save_FI(step_number, en_last)
                    FI_int_pt = [[] for _ in range(len(criteria))]
                en_last = en
            sxx = float(line_split[2])
            syy = float(line_split[3])
            szz = float(line_split[4])
            sxy = float(line_split[5])
            sxz = float(line_split[6])
            syz = float(line_split[7])
            syx = sxy
            szx = sxz
            szy = syz
            compute_FI()
            if step_number in memorized_steps:
                try:
                    step_stress[step_number][en]
                except KeyError:
                    step_stress[step_number][en] = []
                step_stress[step_number][en].append([sxx, syy, szz, sxy, sxz, syz])

        elif read_energy_density == 1:
            en = int(line_split[0])
            if en_last != en:
                if en_last:
                    if read_eigenvalues:
                        energy_density_eigen[eigen_number][en_last] = np.average(ener_int_pt)
                    else:
                        energy_density_step[step_number][en_last] = np.average(ener_int_pt)
                    ener_int_pt = []
                en_last = en
            energy_density = float(line_split[2])
            ener_int_pt.append(energy_density)
            if step_number in memorized_steps:
                try:
                    step_ener[step_number][en]
                except KeyError:
                    step_ener[step_number][en] = []
                    step_ener[step_number][en].append(energy_density)

        elif read_heat_flux == 1:
            en = int(line_split[0])
            if en_last != en:
                if en_last:
                    heat_flux[en_last] = np.average(heat_int_pt)
                    heat_int_pt = []
                en_last = en
            heat_flux_total = np.sqrt(float(line_split[2]) ** 2 + float(line_split[3]) ** 2 + float(line_split[4]) ** 2)
            heat_int_pt.append(heat_flux_total)

        elif read_displacement == 1:
            ux = float(line_split[1])
            uy = float(line_split[2])
            uz = float(line_split[3])
            for cn in ns_reading:
                component = displacement_graph[cn][1]
                if component.upper() == "TOTAL":  # total displacement
                    disp_condition[cn].append(sqrt(ux ** 2 + uy ** 2 + uz ** 2))
                else:
                    disp_condition[cn].append(eval(component))
            if steps_superposition:  # save ux, uy, uz for steps superposition
                disp_components[step_number][ns].append((ux, uy, uz))

    if read_stresses == 1:
        save_FI(step_number, en_last)
    if read_energy_density == 1:
        if read_eigenvalues:
            energy_density_eigen[eigen_number][en_last] = np.average(ener_int_pt)
        else:
            energy_density_step[step_number][en_last] = np.average(ener_int_pt)
    if read_heat_flux == 1:
        heat_flux[en_last] = np.average(heat_int_pt)
    if read_displacement == 1:
        for cn in ns_reading:
            try:
                disp_i[cn] = max([disp_i[cn]] + disp_condition[cn])
            except TypeError:
                disp_i[cn] = max(disp_condition[cn])
    f.close()

    # superposed steps
    # step_stress = {sn: {en: [[sxx, syy, szz, sxy, sxz, syz], next integration point], next element with int. pt. stresses}, next step, ...}
    # steps_superposition = [[(sn, scale), next scaled step to add, ...], next superposed step]
    for LCn in range(len(steps_superposition)):
        FI_step.append({})
        energy_density_step.append({})

        # sum scaled stress components at each integration point
        superposition_stress = {}
        superposition_energy_density = {}
        for (scale, sn) in steps_superposition[LCn]:
            sn -= 1  # step numbering in CalculiX is from 1, but we have it 0 based
            # with stresses
            for en in step_stress[sn]:
                try:
                    superposition_stress[en]
                except KeyError:
                    superposition_stress[en] = []  # list of integration points
                for ip in range(len(step_stress[sn][en])):
                    try:
                        superposition_stress[en][ip]
                    except IndexError:
                        superposition_stress[en].append([0, 0, 0, 0, 0, 0])  # components of stress
                    for component in range(6):
                        superposition_stress[en][ip][component] += scale * step_stress[sn][en][ip][component]
            # again with energy density
            for en in step_ener[sn]:
                try:
                    superposition_energy_density[en]
                except KeyError:
                    superposition_energy_density[en] = []  # list of integration points
                for ip in range(len(step_ener[sn][en])):
                    try:
                        superposition_energy_density[en][ip]
                    except IndexError:
                        superposition_energy_density[en].append(0)  # components of stress
                    for component in range(6):
                        superposition_energy_density[en][ip] += scale * step_ener[sn][en][ip]

        # compute FI in each element at superposed step
        for en in superposition_stress:
            FI_int_pt = [[] for _ in range(len(criteria))]
            for ip in range(len(superposition_stress[en])):
                sxx = superposition_stress[en][ip][0]
                syy = superposition_stress[en][ip][1]
                szz = superposition_stress[en][ip][2]
                sxy = superposition_stress[en][ip][3]
                sxz = superposition_stress[en][ip][4]
                syz = superposition_stress[en][ip][5]
                syx = sxy
                szx = sxz
                szy = syz
                compute_FI()  # fill FI_int_pt
            sn = -1  # last step number
            save_FI(sn, en)  # save value to FI_step for given en
        # compute average energy density over integration point at superposed step
        for en in superposition_energy_density:
            ener_int_pt = []
            for ip in range(len(superposition_energy_density[en])):
                ener_int_pt.append(superposition_energy_density[en][ip])
            sn = -1  # last step number
            energy_density_step[sn][en] = np.average(ener_int_pt)

        # superposition of displacements to graph, same code block as in import_displacement function
        cn = 0
        for (ns, component) in displacement_graph:
            ns = ns.upper()
            uxe = []
            uye = []
            uze = []
            for en2 in range(len(disp_components[0][ns])):
                uxe.append(0)
                uye.append(0)
                uze.append(0)
                for (scale, sn) in steps_superposition[LCn]:
                    sn -= 1  # step numbering in CalculiX is from 1, but we have it 0 based
                    uxe[-1] += scale * disp_components[sn][ns][en2][0]
                    uye[-1] += scale * disp_components[sn][ns][en2][1]
                    uze[-1] += scale * disp_components[sn][ns][en2][2]

            for en2 in range(len(uxe)):  # iterate over elements in nset
                ux = uxe.pop()
                uy = uye.pop()
                uz = uze.pop()
                if component.upper() == "TOTAL":  # total displacement
                    disp_condition[cn].append(sqrt(ux ** 2 + uy ** 2 + uz ** 2))
                else:
                    disp_condition[cn].append(eval(component))
            try:
                disp_i[cn] = max([disp_i[cn]] + disp_condition[cn])
            except TypeError:
                disp_i[cn] = max(disp_condition[cn])
            cn += 1

    return FI_step, energy_density_step, disp_i, buckling_factors, energy_density_eigen, heat_flux


# function for importing displacements if import_FI_int_pt is not called to read .dat file
def import_displacement(file_nameW, displacement_graph, steps_superposition):
    f = open(file_nameW + ".dat", "r")
    read_displacement = 0
    disp_i = [None for _ in range(len(displacement_graph))]
    disp_condition = {}
    disp_components = []
    last_time = "initial"
    step_number = -1
    for line in f:
        line_split = line.split()
        if line.replace(" ", "") == "\n":
            if read_displacement == 1:
                for cn in ns_reading:
                    try:
                        disp_i[cn] = max([disp_i[cn]] + disp_condition[cn])
                    except TypeError:
                        disp_i[cn] = max(disp_condition[cn])
            read_displacement -= 1

        elif line[:14] == " displacements":
            cn = 0
            ns_reading = []
            for [ns, component] in displacement_graph:
                if ns.upper() == line_split[4]:
                    ns_reading.append(cn)
                    disp_condition[cn] = []
                cn += 1
            read_displacement = 2
            if steps_superposition:
                if last_time != line_split[-1]:
                    step_number += 1
                    disp_components.append({})  # appending sn
                    last_time = line_split[-1]
                ns = line_split[4]
                disp_components[-1][ns] = []  # appending ns

        elif read_displacement == 1:
            ux = float(line_split[1])
            uy = float(line_split[2])
            uz = float(line_split[3])
            for cn in ns_reading:
                component = displacement_graph[cn][1]
                if component.upper() == "TOTAL":  # total displacement
                    disp_condition[cn].append(sqrt(ux ** 2 + uy ** 2 + uz ** 2))
                else:
                    disp_condition[cn].append(eval(component))
            if steps_superposition:  # save ux, uy, uz for steps superposition
                disp_components[step_number][ns].append((ux, uy, uz))

    if read_displacement == 1:
        for cn in ns_reading:
            try:
                disp_i[cn] = max([disp_i[cn]] + disp_condition[cn])
            except TypeError:
                disp_i[cn] = max(disp_condition[cn])
    f.close()

    # superposition of displacements to graph, same code block as in import_FI_int_pt function
    for LCn in range(len(steps_superposition)):  # steps superposition
        cn = 0
        for (ns, component) in displacement_graph:
            ns = ns.upper()
            uxe = []
            uye = []
            uze = []
            for en2 in range(len(disp_components[0][ns])):
                uxe.append(0)
                uye.append(0)
                uze.append(0)
                for (scale, sn) in steps_superposition[LCn]:
                    sn -= 1  # step numbering in CalculiX is from 1, but we have it 0 based
                    uxe[-1] += scale * disp_components[sn][ns][en2][0]
                    uye[-1] += scale * disp_components[sn][ns][en2][1]
                    uze[-1] += scale * disp_components[sn][ns][en2][2]

            for en2 in range(len(uxe)):  # iterate over elements in nset
                ux = uxe.pop()
                uy = uye.pop()
                uz = uze.pop()
                if component.upper() == "TOTAL":  # total displacement
                    disp_condition[cn].append(sqrt(ux ** 2 + uy ** 2 + uz ** 2))
                else:
                    disp_condition[cn].append(eval(component))
            try:
                disp_i[cn] = max([disp_i[cn]] + disp_condition[cn])
            except TypeError:
                disp_i[cn] = max(disp_condition[cn])
            cn += 1
    return disp_i


# function for importing results from .frd file
# Failure Indices are computed at each node and maximum or average above each element is returned
class import_FI_node:
    def __init__(self,reference_value, file_nameW, domains, criteria, domain_FI, file_name, elm_states,
                steps_superposition):
        self.reference_value=reference_value
        self.file_nameW=file_nameW
        self.domains=domains
        self.criteria=criteria
        self.domain_FI=domain_FI
        self.file_name=file_name
        self.elm_states=elm_states
        self.steps_superposition=steps_superposition
        
        try:
            self.f = open(self.file_nameW + ".frd", "r")
        except IOError:
            msg = "CalculiX result file not found, check your inputs"
            BesoLib_types.write_to_log(self.file_name, "\nERROR: " + msg + "\n")
            assert False, msg

        self.memorized_steps = set()  # steps to use in superposition
        if self.steps_superposition:
            # {sn: {en: [sxx, syy, szz, sxy, sxz, syz], next element with int. pt. stresses}, next step, ...}
            self.step_stress = {}
            for LCn in range(len(self.steps_superposition)):
                for (scale, sn) in self.steps_superposition[LCn]:
                    sn -= 1  # step numbering in CalculiX is from 1, but we have it 0 based
                    self.memorized_steps.add(sn)
                    self.step_stress[sn] = {}

        # prepare ordered elements of interest and failure criteria for each element
        self.criteria_elm = {}
        for self.dn in domain_FI:
            for self.en in domains[self.dn]:
                self.cr = []
                for dn_crit in domain_FI[self.dn][elm_states[self.en]]:
                    self.cr.append(criteria.index(dn_crit))
                self.criteria_elm[self.en] = self.cr
        self.sorted_elements = sorted(self.criteria_elm.keys())  # [en_lowest, ..., en_highest]

    def compute_FI(self):  # for the actual node
        if self.en in self.criteria_elm:
            for FIn in self.criteria_elm[self.en]:
                if self.criteria[FIn][0] == "stress_von_Mises":
                    s_allowable = self.criteria[FIn][1]
                    self.FI_node[self.nn][FIn] = np.sqrt(0.5 * ((self.sxx - self.syy) ** 2 + (self.syy - self.szz) ** 2 + (self.szz - self.sxx) ** 2 +
                                                    6 * (self.sxy ** 2 + self.syz ** 2 + self.sxz ** 2))) / s_allowable
                elif self.criteria[FIn][0] == "user_def":
                    self.FI_node[self.nn][FIn] = eval(self.criteria[FIn][1])
                else:
                    msg = "\nError: failure criterion " + str(self.criteria[FIn]) + " not recognised.\n"
                    BesoLib_types.write_to_log(self.file_name, msg)

    def save_FI(self,sn, en):
        self.FI_step[sn][en] = []
        for FIn in range(len(self.criteria)):
            self.FI_step[sn][en].append(None)
            if FIn in self.criteria_elm[en]:
                if self.reference_value == "max":
                    self.FI_step[sn][en][FIn] = max(self.FI_elm[en][FIn])
                elif self.reference_value == "average":
                    self.FI_step[sn][en][FIn] = np.average(self.FI_elm[en][FIn])
    def import_FI_node(self):

        read_mesh = False
        frd_nodes = {}  # en associated to given node
        elm_nodes = {}
        for en in self.sorted_elements:
            elm_nodes[en] = []
        read_stress = False
        sn = -1
        FI_step = []  # list for steps - [{en1: list for criteria FI, en2: [], ...}, {en1: [], en2: [], ...}, next step]
        for line in self.f:
            # reading mesh
            if line[:6] == "    3C":
                read_mesh = True
            elif read_mesh is True:
                if line[:3] == " -1":
                    en = int(line[3:13])
                    if en == self.sorted_elements[0]:
                        self.sorted_elements.pop(0)
                        read_elm_nodes = True
                    else:
                        read_elm_nodes = False
                elif line[:3] == " -2" and read_elm_nodes is True:
                    associated_nn = list(map(int, line.split()[1:]))
                    elm_nodes[en] += associated_nn
                    for nn in associated_nn:
                        frd_nodes[nn] = en

            # block end
            if line[:3] == " -3":
                if read_mesh is True:
                    read_mesh = False
                    frd_nodes_sorted = sorted(frd_nodes.items())  # [(nn, en), ...]
                elif read_stress is True:
                    read_stress = False
                    FI_elm = {}
                    for en in elm_nodes:
                        FI_elm[en] = [[] for _ in range(len(self.criteria))]
                        if en in self.criteria_elm:
                            for FIn in self.criteria_elm[en]:
                                for nn in elm_nodes[en]:
                                    FI_elm[en][FIn].append(FI_node[nn][FIn])
                    FI_step.append({})
                    for en in FI_elm:
                        self.save_FI(sn, en)

            # reading stresses
            elif line[:11] == " -4  STRESS":
                read_stress = True
                sn += 1
                FI_node = {}
                for nn in frd_nodes:
                    FI_node[nn] = [[] for _ in range(len(self.criteria))]
                next_node = 0
            elif read_stress is True:
                if line[:3] == " -1":
                    nn = int(line[3:13])
                    if nn == frd_nodes_sorted[next_node][0]:
                        next_node += 1
                        self.sxx = float(line[13:25])
                        self.syy = float(line[25:37])
                        self.szz = float(line[37:49])
                        self.sxy = float(line[49:61])
                        self.syz = float(line[61:73])
                        self.szx = float(line[73:85])
                        self.syx = sxy
                        self.szy = syz
                        self.sxz = szx
                        self.en = frd_nodes[nn]
                        self.compute_FI()
                        if sn in self.memorized_steps:
                            try:
                                self.step_stress[sn][en]
                            except KeyError:
                                self.step_stress[sn][en] = {}
                            self.step_stress[sn][en][nn] = [sxx, syy, szz, sxy, sxz, syz]
        self.f.close()

    # superposed steps
    # step_stress = {sn: {en: [[sxx, syy, szz, sxy, sxz, syz], next node], next element with nodal stresses}, next step, ...}
    # steps_superposition = [[(sn, scale), next scaled step to add, ...], next superposed step]
        for LCn in range(len(self.steps_superposition)):
            FI_step.append({})

            # sum scaled stress components at each integration node
            superposition_stress = {}
            for (scale, sn) in self.steps_superposition[LCn]:
                sn -= 1  # step numbering in CalculiX is from 1, but we have it 0 based
                for en in self.step_stress[sn]:
                    try:
                        superposition_stress[en]
                    except KeyError:
                        superposition_stress[en] = {}  # for nodes
                    for nn in elm_nodes[en]:
                        try:
                            superposition_stress[en][nn]
                        except KeyError:
                            superposition_stress[en][nn] = [0, 0, 0, 0, 0, 0]  # components of stress
                        for component in range(6):
                            superposition_stress[en][nn][component] += scale * self.step_stress[sn][en][nn][component]

            # compute FI in each element at superposed step
            for en in superposition_stress:
                FI_node = {}
                for nn in elm_nodes[en]:
                    FI_node[nn] = [[] for _ in range(len(self.criteria))]
                    self.sxx = superposition_stress[en][nn][0]
                    self.syy = superposition_stress[en][nn][1]
                    self.szz = superposition_stress[en][nn][2]
                    self.sxy = superposition_stress[en][nn][3]
                    self.sxz = superposition_stress[en][nn][4]
                    self.syz = superposition_stress[en][nn][5]
                    self.syx = self.sxy
                    self.szx = self.sxz
                    self.szy = self.syz
                    self.compute_FI()  # fill FI_node
                FI_elm[en] = [[] for _ in range(len(self.criteria))]

                if en in self.criteria_elm:
                    for FIn in self.criteria_elm[en]:
                        for nn in elm_nodes[en]:
                            FI_elm[en][FIn].append(FI_node[nn][FIn])
                sn = -1  # last step number
                self.save_FI(sn, en)  # save value to FI_step for given en

        return FI_step


# function for switch element states
class switching:
    def __init__(self,elm_states, domains_from_config, domain_optimized, domains, FI_step_max, domain_density, domain_thickness,
            domain_shells, area_elm, volume_elm, sensitivity_number, mass, mass_referential, mass_addition_ratio,
            mass_removal_ratio, compensate_state_filter, mass_excess, decay_coefficient, FI_violated, i_violated, i,
            mass_goal_i, domain_same_state):
        self.elm_states=elm_states
        self.domains_from_config=domains_from_config
        self.domain_optimized=domain_optimized
        self.domains=domains
        self.FI_step_max=FI_step_max
        self.domain_density=domain_density
        self.domain_thickness=domain_thickness
        self.domain_shells=domain_shells
        self.area_elm=area_elm
        self.volume_elm=volume_elm
        self.sensitivity_number=sensitivity_number
        self.mass=mass
        self.mass_referential=mass_referential
        self.mass_addition_ratio=mass_addition_ratio
        self.mass_removal_ratio=mass_removal_ratio
        self.compensate_state_filter=compensate_state_filter
        self.mass_excess=mass_excess
        self.decay_coefficient=decay_coefficient
        self.FI_violated=FI_violated
        self.i_violated=i_violated
        self.i=i
        self.mass_goal_i=mass_goal_i
        self.domain_same_state=domain_same_state




    def compute_difference(self,failing=False):
        if self.en in self.domain_shells[self.dn]:  # shells mass difference
            self.mass[self.i] += self.area_elm[self.en] * self.domain_density[self.dn][self.elm_states_en] * self.domain_thickness[self.dn][self.elm_states_en]
            if (failing is False) and (self.elm_states_en != 0):  # for potential switching down
                self.mass_decrease[self.en] = self.area_elm[self.en] * (
                    self.domain_density[self.dn][self.elm_states_en] * self.domain_thickness[self.dn][self.elm_states_en] -
                    self.domain_density[self.dn][self.elm_states_en - 1] * self.domain_thickness[self.dn][self.elm_states_en - 1])
            if self.elm_states_en < len(self.domain_density[self.dn]) - 1:  # for potential switching up
                self.mass_increase[self.en] = self.area_elm[self.en] * (
                    self.domain_density[self.dn][self.elm_states_en + 1] * self.domain_thickness[self.dn][self.elm_states_en + 1] -
                    self.domain_density[self.dn][self.elm_states_en] * self.domain_thickness[self.dn][self.elm_states_en])
        else:  # volumes mass difference
            self.mass[self.i] += self.volume_elm[self.en] * self.domain_density[self.dn][self.elm_states_en]
            if (failing is False) and (self.elm_states_en != 0):  # for potential switching down
                self.mass_decrease[self.en] = self.volume_elm[self.en] * (
                    self.domain_density[self.dn][self.elm_states_en] - self.domain_density[self.dn][self.elm_states_en - 1])
            if self.elm_states_en < len(self.domain_density[self.dn]) - 1:  # for potential switching up
                self.mass_increase[self.en] = self.volume_elm[self.en] * (
                    self.domain_density[self.dn][self.elm_states_en + 1] - self.domain_density[self.dn][self.elm_states_en])
    def switching(self):
        self.mass_increase = {}
        self.mass_decrease = {}
        sensitivity_number_opt = {}
        self.mass.append(0)
        mass_overloaded = 0.0
        # switch up overloaded elements
        for self.dn in self.domains_from_config:
            if self.domain_optimized[self.dn] is True:
                len_domain_density_dn = len(self.domain_density[self.dn])
                if self.domain_same_state[self.dn] in ["max", "average"]:
                    new_state = 0
                    failing = False
                    highest_state = 0
                    sensitivity_number_list = []
                    sensitivity_number_of_domain = 0
                    for self.en in self.domains[self.dn]:  # find highest state, sensitivity number and if failing
                        self.elm_states_en = self.elm_states[self.en]
                        if self.elm_states_en >= highest_state:
                            if self.domain_same_state[self.dn] == "max":
                                sensitivity_number_of_domain = max(sensitivity_number_of_domain, self.sensitivity_number[self.en])
                            highest_state = self.elm_states_en
                        if self.FI_step_max[self.en] >= 1:  # new state if failing
                            failing = True
                            if self.elm_states_en < len_domain_density_dn - 1:
                                new_state = max(new_state, self.elm_states_en + 1)
                            else:
                                new_state = max(new_state, self.elm_states_en)
                        else:
                            new_state = max(new_state, self.elm_states_en)
                        if self.domain_same_state[self.dn] == "average":
                            sensitivity_number_list.append(self.sensitivity_number[self.en])

                    if self.domain_same_state[self.dn] == "average":
                        sensitivity_number_of_domain = np.average(sensitivity_number_list)

                    self.mass_increase[self.dn] = 0
                    self.mass_decrease[self.dn] = 0
                    for en in self.domains[self.dn]:  # evaluate mass, prepare to sorting and switching
                        self.elm_states[self.en] = highest_state
                        self.elm_states_en = self.elm_states[self.en]
                        self.compute_difference(failing)
                        if (failing is True) and (new_state != highest_state):
                            self.elm_states[self.en] = new_state
                            self.elm_states_en = self.elm_states[self.en]
                            self.mass[self.i] += self.mass_increase[self.en]
                            mass_overloaded += self.mass_increase[self.en]
                            mass_goal_i += self.mass_increase[self.en]
                        elif failing is False:  # use domain name dn instead of element number for future switching
                            sensitivity_number_opt[self.dn] = sensitivity_number_of_domain
                            try:
                                self.mass_increase[self.dn] += self.mass_increase[self.en]
                            except KeyError:
                                pass
                            try:
                                self.mass_decrease[self.dn] += self.mass_decrease[self.en]
                            except KeyError:
                                pass

                else:  # domain_same_state is False
                    for self.en in self.domains[self.dn]:
                        if self.FI_step_max[self.en] >= 1:  # increase state if it is not the highest
                            en_added = False
                            if self.elm_states[self.en] < len_domain_density_dn - 1:
                                self.elm_states[self.en] += 1
                                en_added = True
                            self.elm_states_en = self.elm_states[self.en]
                            if en in self.domain_shells[self.dn]:  # shells
                                self.mass[self.i] += self.area_elm[self.en] * self.domain_density[self.dn][self.elm_states_en] * self.domain_thickness[
                                    self.dn][self.elm_states_en]
                                if en_added is True:
                                    mass_difference = self.area_elm[self.en] * (
                                        self.domain_density[self.dn][self.elm_states_en] * self.domain_thickness[self.dn][self.elm_states_en] -
                                        self.domain_density[self.dn][self.elm_states_en - 1] * self.domain_thickness[self.dn][self.elm_states_en - 1])
                                    mass_overloaded += mass_difference
                                    mass_goal_i += mass_difference
                            else:  # volumes
                                self.mass[self.i] += self.volume_elm[self.en] * self.domain_density[self.dn][self.elm_states_en]
                                if en_added is True:
                                    mass_difference = self.volume_elm[self.en] * (
                                        self.domain_density[self.dn][self.elm_states_en] - self.domain_density[self.dn][self.elm_states_en - 1])
                                    mass_overloaded += mass_difference
                                    mass_goal_i += mass_difference
                        else:  # rest of elements prepare to sorting and switching
                            self.elm_states_en = self.elm_states[self.en]
                            self.compute_difference()  # mass to add or remove
                            sensitivity_number_opt[self.en] = self.sensitivity_number[self.en]
        # sorting
        sensitivity_number_sorted = sorted(sensitivity_number_opt.items(), key=operator.itemgetter(1))
        sensitivity_number_sorted2 = list(sensitivity_number_sorted)
        if self.i_violated:
            if self.mass_removal_ratio - self.mass_addition_ratio > 0:  # removing from initial mass
                mass_to_add = self.mass_addition_ratio * self.mass_referential * np.exp(self.decay_coefficient * (self.i - self.i_violated))
                if sum(self.FI_violated[self.i - 1]):
                    mass_to_remove = self.mass_addition_ratio * self.mass_referential * np.exp(self.decay_coefficient * (self.i - self.i_violated)) \
                        - mass_overloaded
                else:
                    mass_to_remove = self.mass_removal_ratio * self.mass_referential * np.exp(self.decay_coefficient * (self.i - self.i_violated)) \
                        - mass_overloaded
            else:  # adding to initial mass  TODO include stress limit
                mass_to_add = self.mass_removal_ratio * self.mass_referential * np.exp(self.decay_coefficient * (self.i - self.i_violated))
                mass_to_remove = mass_to_add
        else:
            mass_to_add = self.mass_addition_ratio * self.mass_referential
            mass_to_remove = self.mass_removal_ratio * self.mass_referential
        if self.compensate_state_filter is True:
            if self.mass_excess > 0:
                mass_to_remove += self.mass_excess
            else:  # compensate by adding more mass
                mass_to_add -= self.mass_excess
        mass_added = mass_overloaded
        mass_removed = 0.0
        # if mass_goal_i < mass[i - 1]:  # going from bigger mass to lower
        added_elm = set()
        while mass_added < mass_to_add:
            if sensitivity_number_sorted:
                self.en = sensitivity_number_sorted.pop(-1)[0]  # highest sensitivity number
                try:
                    self.mass[self.i] += self.mass_increase[self.en]
                    mass_added += self.mass_increase[self.en]
                    if isinstance(self.en, int):
                        self.elm_states[self.en] += 1
                    else:  # same state domain en
                        if self.mass_increase[self.en] == 0:
                            raise KeyError
                        for en2 in self.domains[self.en]:
                            self.elm_states[en2] += 1
                    added_elm.add(self.en)
                except KeyError:  # there is no mass_increase due to highest element state
                    pass
            else:
                break
        popped = 0
        while mass_removed < mass_to_remove:
            if self.mass[self.i] <= self.mass_goal_i:
                break
            if sensitivity_number_sorted:
                self.en = sensitivity_number_sorted.pop(0)[0]  # lowest sensitivity number
                popped += 1
                if isinstance(self.en, int):
                    if self.elm_states[self.en] != 0:
                        self.mass[self.i] -= self.mass_decrease[self.en]
                        mass_removed += self.mass_decrease[self.en]
                        self.elm_states[self.en] -= 1
                else:  # same state domain en
                    if self.mass_decrease[self.en] != 0:
                        self.mass[self.i] -= self.mass_decrease[self.en]
                        mass_removed += self.mass_decrease[self.en]
                        for en2 in self.domains[self.en]:
                            self.elm_states[en2] -= 1
            else:  # switch down elements just switched up or tried to be switched up (already in the highest state)
                try:
                    self.en = sensitivity_number_sorted2[popped][0]
                    popped += 1
                except IndexError:
                    break
                if isinstance(self.en, int):
                    if self.elm_states[self.en] != 0:
                        self.elm_states[self.en] -= 1
                        if self.en in added_elm:
                            self.mass[self.i] -= self.mass_increase[self.en]
                            mass_removed += self.mass_increase[self.en]
                        else:
                            self.mass[self.i] -= self.mass_decrease[self.en]
                            mass_removed += self.mass_decrease[self.en]
                else:  # same state domain en
                    if self.mass_decrease[self.en] != 0:
                        for en2 in self.domains[self.en]:
                            self.elm_states[en2] -= 1
                        if self.en in added_elm:
                            self.mass[self.i] -= self.mass_increase[self.en]
                            mass_removed += self.mass_increase[self.en]
                        else:
                            self.mass[self.i] -= self.mass_decrease[self.en]
                            mass_removed += self.mass_decrease[self.en]
        return self.elm_states, self.mass



# function for exporting the resulting mesh in separate files for each state of elm_states
# only elements found by import_inp function are taken into account
class export_frd:
    def __init__(self,file_nameW, nodes, Elements, elm_states, number_of_states):
        self.file_nameW=file_nameW
        self.nodes=nodes
        self.Elements=Elements
        self.elm_states=elm_states
        self.number_of_states=number_of_states


    def get_associated_nodes(self,elm_category):
        for en in elm_category:
            if self.elm_states[en] == self.state:
                self.associated_nodes.extend(elm_category[en])

    def write_elm(self,elm_category, category_symbol):
        for en in elm_category:
            if self.elm_states[en] == self.state:
                self.f.write(" -1" + str(en).rjust(10, " ") + category_symbol.rjust(5, " ") + "\n")
                line = ""
                nodes_done = 0
                if category_symbol == "4":  # hexa20 different node numbering in inp and frd file
                    for np in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9,
                               10, 11, 16, 17, 18, 19, 12, 13, 14, 15]:
                        nn = elm_category[en][np]
                        line += str(nn).rjust(10, " ")
                        if np in [9, 15]:
                            self.f.write(" -2" + line + "\n")
                            line = ""
                elif category_symbol == "5":  # penta15 has different node numbering in inp and frd file
                    for np in [0, 1, 2, 3, 4, 5, 6, 7, 8, 12,
                               13, 14, 9, 10, 11]:
                        nn = elm_category[en][np]
                        line += str(nn).rjust(10, " ")
                        if np in [12, 11]:
                            self.f.write(" -2" + line + "\n")
                            line = ""
                else:
                    for nn in elm_category[en]:
                        line += str(nn).rjust(10, " ")
                        nodes_done += 1
                        if nodes_done == 10 and elm_category != Elements.tetra10:
                            self.f.write(" -2" + line + "\n")
                            line = ""
                    self.f.write(" -2" + line + "\n")

    # find all possible states in elm_states and run separately for each of them
    def export_frd(self):
        for self.state in range(self.number_of_states):
            self.f = open(self.file_nameW + "_state" + str(self.state) + ".frd", "w")

            # print nodes
            associated_nodes = []
            self.get_associated_nodes(self.Elements.tria3)
            self.get_associated_nodes(self.Elements.tria6)
            self.get_associated_nodes(self.Elements.quad4)
            self.get_associated_nodes(self.Elements.quad8)
            self.get_associated_nodes(self.Elements.tetra4)
            self.get_associated_nodes(self.Elements.tetra10)
            self.get_associated_nodes(self.Elements.penta6)
            self.get_associated_nodes(self.Elements.penta15)
            self.get_associated_nodes(self.Elements.hexa8)
            self.get_associated_nodes(self.Elements.hexa20)

            associated_nodes = sorted(list(set(associated_nodes)))
            self.f.write("    1C\n")
            self.f.write("    2C" + str(len(associated_nodes)).rjust(30, " ") + 37 * " " + "1\n")
            for nn in associated_nodes:
                self.f.write(" -1" + str(nn).rjust(10, " ") + "% .5E% .5E% .5E\n" % (self.nodes[nn][0], self.nodes[nn][1], self.nodes[nn][2]))
            self.f.write(" -3\n")

            # print elements
            self.elm_sum = 0
            for en in self.elm_states:
                if self.elm_states[en] == self.state:
                    self.elm_sum += 1
            self.f.write("    3C" + str(self.elm_sum).rjust(30, " ") + 37 * " " + "1\n")
            self.write_elm(self.Elements.tria3, "7")
            self.write_elm(self.Elements.tria6, "8")
            self.write_elm(self.Elements.quad4, "9")
            self.write_elm(self.Elements.quad8, "10")
            self.write_elm(self.Elements.tetra4, "3")
            self.write_elm(self.Elements.tetra10, "6")
            self.write_elm(self.Elements.penta6, "2")
            self.write_elm(self.Elements.penta15, "5")
            self.write_elm(self.Elements.hexa8, "1")
            self.write_elm(self.Elements.hexa20, "4")
            self.f.write(" -3\n")
            self.f.close()


# function for exporting the resulting mesh in separate files for each state of elm_states
# only elements found by import_inp function are taken into account
class export_inp:
    def __init__(self,file_nameW, nodes, Elements, elm_states, number_of_states):
        self.file_nameW=file_nameW
        self.nodes=nodes
        self.Elements=Elements
        self.elm_states=elm_states
        self.number_of_states=number_of_states
        
    def get_associated_nodes(self,elm_category):
        for en in elm_category:
            if self.elm_states[en] == self.state:
                self.associated_nodes.extend(elm_category[en])

    def write_elements_of_type(self,elm_type, elm_type_inp):
        if elm_type:
            self.f.write("*ELEMENT, TYPE=" + elm_type_inp + ", ELSET=state" + str(self.state) + "\n")
            for en, nod in elm_type.items():
                if self.elm_states[en] == self.state:
                    self.f.write(str(en))
                    for nn in nod:
                        self.f.write(", " + str(nn))
                    self.f.write("\n")

    # find all possible states in elm_states and run separately for each of them
    def export_inp(self):
        for self.state in range(self.number_of_states):
            self.f = open(self.file_nameW + "_state" + str(self.state) + ".inp", "w")

            # print nodes
            self.associated_nodes = []
            self.get_associated_nodes(self.Elements.tria3)
            self.get_associated_nodes(self.Elements.tria6)
            self.get_associated_nodes(self.Elements.quad4)
            self.get_associated_nodes(self.Elements.quad8)
            self.get_associated_nodes(self.Elements.tetra4)
            self.get_associated_nodes(self.Elements.tetra10)
            self.get_associated_nodes(self.Elements.penta6)
            self.get_associated_nodes(self.Elements.penta15)
            self.get_associated_nodes(self.Elements.hexa8)
            self.get_associated_nodes(self.Elements.hexa20)

            self.associated_nodes = sorted(list(set(self.associated_nodes)))
            self.f.write("*NODE\n")
            for nn in self.associated_nodes:
                self.f.write(str(nn) + ", % .5E, % .5E, % .5E\n" % (self.nodes[nn][0], self.nodes[nn][1], self.nodes[nn][2]))
            self.f.write("\n")

            # print elements
            # prints only basic element types
            self.write_elements_of_type(self.Elements.tria3, "S3")
            self.write_elements_of_type(self.Elements.tria6, "S6")
            self.write_elements_of_type(self.Elements.quad4, "S4")
            self.write_elements_of_type(self.Elements.quad8, "S8")
            self.write_elements_of_type(self.Elements.tetra4, "C3D4")
            self.write_elements_of_type(self.Elements.tetra10, "C3D10")
            self.write_elements_of_type(self.Elements.penta6, "C3D6")
            self.write_elements_of_type(self.Elements.penta15, "C3D15")
            self.write_elements_of_type(self.Elements.hexa8, "C3D8")
            if self.Elements.hexa20:
                self.f.write("*ELEMENT, TYPE=C3D20\n")
                for en, nod in self.Elements.hexa20.items():
                    self.f.write(str(en))
                    for nn in nod[:15]:
                        self.f.write(", " + str(nn))
                    self.f.write("\n")
                    for nn in nod[15:]:
                        self.f.write(", " + str(nn))
                    self.f.write("\n")
            self.f.close()

class beso_lib_2:
# sub-function to write vtk mesh
    def vtk_mesh(file_nameW, nodes, Elements):
        f = open(file_nameW + ".vtk", "w")
        f.write("# vtk DataFile Version 3.0\n")
        f.write("Results from optimization\n")
        f.write("ASCII\n")
        f.write("DATASET UNSTRUCTURED_GRID\n")

        # nodes
        associated_nodes = set()
        for nn_lists in list(Elements.tria3.values()) + list(Elements.tria6.values()) + list(Elements.quad4.values()) + \
                list(Elements.quad8.values()) + list(Elements.tetra4.values()) + list(Elements.tetra10.values()) + \
                list(Elements.penta6.values()) + list(Elements.penta15.values()) + list(Elements.hexa8.values()) + \
                list(Elements.hexa20.values()):
            associated_nodes.update(nn_lists)
        associated_nodes = sorted(associated_nodes)
        # node renumbering table for vtk format which does not jump over node numbers and contains only associated nodes
        nodes_vtk = [None for _ in range(max(nodes.keys()) + 1)]
        nn_vtk = 0
        for nn in associated_nodes:
            nodes_vtk[nn] = nn_vtk
            nn_vtk += 1

        f.write("\nPOINTS " + str(len(associated_nodes)) + " float\n")
        line_count = 0
        for nn in associated_nodes:
            f.write("{} {} {} ".format(nodes[nn][0], nodes[nn][1], nodes[nn][2]))
            line_count += 1
            if line_count % 2 == 0:
                f.write("\n")
        f.write("\n")

        # elements
        number_of_elements = len(Elements.tria3) + len(Elements.tria6) + len(Elements.quad4) + len(Elements.quad8) + \
            len(Elements.tetra4) + len(Elements.tetra10) + len(Elements.penta6) + len(Elements.penta15) + \
            len(Elements.hexa8) + len(Elements.hexa20)
        en_all = list(Elements.tria3.keys()) + list(Elements.tria6.keys()) + list(Elements.quad4.keys()) + \
            list(Elements.quad8.keys()) + list(Elements.tetra4.keys()) + list(Elements.tetra10.keys()) + \
            list(Elements.penta6.keys()) + list(Elements.penta15.keys()) + list(Elements.hexa8.keys()) + \
            list(Elements.hexa20.keys())  # defines vtk element numbering from 0

        size_of_cells = 4 * len(Elements.tria3) + 7 * len(Elements.tria6) + 5 * len(Elements.quad4) + \
            9 * len(Elements.quad8) + 5 * len(Elements.tetra4) + 11 * len(Elements.tetra10) + \
            7 * len(Elements.penta6) + 16 * len(Elements.penta15) + 9 * len(Elements.hexa8) + \
            21 * len(Elements.hexa20)
        f.write("\nCELLS " + str(number_of_elements) + " " + str(size_of_cells) + "\n")

        def write_elm(elm_category, node_length):
            for en in elm_category:
                f.write(node_length)
                for nn in elm_category[en]:
                    f.write(" " + str(nodes_vtk[nn]) + " ")
                f.write("\n")

        write_elm(Elements.tria3, "3")
        write_elm(Elements.tria6, "6")
        write_elm(Elements.quad4, "4")
        write_elm(Elements.quad8, "8")
        write_elm(Elements.tetra4, "4")
        write_elm(Elements.tetra10, "10")
        write_elm(Elements.penta6, "6")
        write_elm(Elements.penta15, "15")
        write_elm(Elements.hexa8, "8")
        write_elm(Elements.hexa20, "20")

        f.write("\nCELL_TYPES " + str(number_of_elements) + "\n")
        cell_types = "5 " * len(Elements.tria3) + "22 " * len(Elements.tria6) + "9 " * len(Elements.quad4) + \
                    "23 " * len(Elements.quad8) + "10 " * len(Elements.tetra4) + "24 " * len(Elements.tetra10) + \
                    "13 " * len(Elements.penta6) + "26 " * len(Elements.penta15) + "12 " * len(Elements.hexa8) + \
                    "25 " * len(Elements.hexa20)
        line_count = 0
        for char in cell_types:
            f.write(char)
            if char == " ":
                line_count += 1
                if line_count % 30 == 0:
                    f.write("\n")
        f.write("\n")

        f.write("\nCELL_DATA " + str(number_of_elements) + "\n")

        f.close()
        return en_all, associated_nodes


    def append_vtk_states(file_nameW, i, en_all, elm_states):
        f = open(file_nameW + ".vtk", "a")

        # element state
        f.write("\nSCALARS element_states" + str(i).zfill(3) + " float\n")
        f.write("LOOKUP_TABLE default\n")
        line_count = 0
        for en in en_all:
            f.write(str(elm_states[en]) + " ")
            line_count += 1
            if line_count % 30 == 0:
                f.write("\n")
        f.write("\n")
        f.close()

    # function for exporting result in the legacy vtk format
    # nodes and elements are renumbered from 0 not to jump over values


class export_vtk:
    def __init__(self,file_nameW, nodes, Elements, elm_states, sensitivity_number, criteria, FI_step, FI_step_max):
        self.file_nameW=file_nameW
        self.nodes=nodes
        self.Elements=Elements
        self.elm_states=elm_states
        self.sensitivity_number=sensitivity_number
        self.criteria=criteria
        self.FI_step=FI_step
        self.FI_step_max=FI_step_max
        self.f = open(self.file_nameW + ".vtk", "a")

    def append_nodal_state(self, en, elm_type):
        for nn in elm_type[en]:
            try:
                self.nodal_state[nn].append(self.elm_states[en])
            except KeyError:
                self.nodal_state[nn] = [self.elm_states[en]]

    def export_vtk(self):
        [en_all, associated_nodes] = beso_lib_2.vtk_mesh(self.file_nameW, self.nodes, self.Elements)
        # element state
        self.f.write("\nSCALARS element_states float\n")
        self.f.write("LOOKUP_TABLE default\n")
        line_count = 0
        for en in en_all:
            self.f.write(str(self.elm_states[en]) + " ")
            line_count += 1
            if line_count % 30 == 0:
                self.f.write("\n")
        self.f.write("\n")

        # sensitivity number
        self.f.write("\nSCALARS sensitivity_number float\n")
        self.f.write("LOOKUP_TABLE default\n")
        line_count = 0
        for en in en_all:
            self.f.write(str(self.sensitivity_number[en]) + " ")
            line_count += 1
            if line_count % 6 == 0:
                self.f.write("\n")
        self.f.write("\n")

        # FI
        FI_criteria = {}  # list of FI on each element
        for en in en_all:
            FI_criteria[en] = [None for _ in range(len(self.criteria))]
            for sn in range(len(self.FI_step)):
                for FIn in range(len(self.criteria)):
                    if self.FI_step[sn][en][FIn]:
                        if FI_criteria[en][FIn]:
                            FI_criteria[en][FIn] = max(FI_criteria[en][FIn], self.FI_step[sn][en][FIn])
                        else:
                            FI_criteria[en][FIn] = self.FI_step[sn][en][FIn]

        for FIn in range(len(self.criteria)):
            if self.criteria[FIn][0] == "stress_von_Mises":
                self.f.write("\nSCALARS FI=stress_von_Mises/" + str(self.criteria[FIn][1]).strip() + " float\n")
            elif self.criteria[FIn][0] == "user_def":
                self.f.write("SCALARS FI=" + self.criteria[FIn][1].replace(" ", "") + " float\n")
            self.f.write("LOOKUP_TABLE default\n")
            line_count = 0
            for en in en_all:
                if FI_criteria[en][FIn]:
                    self.f.write(str(FI_criteria[en][FIn]) + " ")
                else:
                    self.f.write("0 ")  # since Paraview do not recognise None value
                line_count += 1
                if line_count % 6 == 0:
                    self.f.write("\n")
            self.f.write("\n")

        # FI_max
        self.f.write("\nSCALARS FI_max float\n")
        self.f.write("LOOKUP_TABLE default\n")
        line_count = 0
        for en in en_all:
            self.f.write(str(self.FI_step_max[en]) + " ")
            line_count += 1
            if line_count % 6 == 0:
                self.f.write("\n")
        self.f.write("\n")

        # element state averaged at nodes

        self.nodal_state = {}
        for en in Elements.tria3:
            self.append_nodal_state(en, self.Elements.tria3)
        for en in Elements.tria6:
            self.append_nodal_state(en, self.Elements.tria6)
        for en in Elements.quad4:
            self.append_nodal_state(en, self.Elements.quad4)
        for en in Elements.quad8:
            self.append_nodal_state(en, self.Elements.quad8)
        for en in Elements.tetra4:
            self.append_nodal_state(en, self.Elements.tetra4)
        for en in Elements.tetra10:
            self.append_nodal_state(en, self.Elements.tetra10)
        for en in Elements.penta6:
            self.append_nodal_state(en, self.Elements.penta6)
        for en in Elements.penta15:
            self.append_nodal_state(en, self.Elements.penta15)
        for en in Elements.hexa8:
           self. append_nodal_state(en, self.Elements.hexa8)
        for en in Elements.hexa20:
            self.append_nodal_state(en, self.Elements.hexa20)

        self.f.write("\nPOINT_DATA " + str(len(associated_nodes)) + "\n")
        self.f.write("FIELD field_data 1\n")
        self.f.write("\nelement_states_averaged_at_nodes 1 " + str(len(associated_nodes)) + " float\n")
        line_count = 0
        for nn in associated_nodes:
            self.f.write(str(np.average(self.nodal_state[nn])) + " ")
            line_count += 1
            if line_count % 10 == 0:
                self.f.write("\n")
        self.f.write("\n")

        self.f.close()

class beso_lib_3:
    # function for exporting element values to csv file for displaying in Paraview, output format:
    # element_number, cg_x, cg_y, cg_z, element_state, sensitivity_number, failure indices 1, 2,..., maximal failure index
    # only elements found by import_inp function are taken into account
    def export_csv(domains_from_config, domains, criteria, FI_step, FI_step_max, file_nameW, cg, elm_states,
                sensitivity_number):
        # associate FI to each element and get maximums
        FI_criteria = {}  # list of FI on each element
        for dn in domains_from_config:
            for en in domains[dn]:
                FI_criteria[en] = [None for _ in range(len(criteria))]
                for sn in range(len(FI_step)):
                    for FIn in range(len(criteria)):
                        if FI_step[sn][en][FIn]:
                            if FI_criteria[en][FIn]:
                                FI_criteria[en][FIn] = max(FI_criteria[en][FIn], FI_step[sn][en][FIn])
                            else:
                                FI_criteria[en][FIn] = FI_step[sn][en][FIn]

        # write element values to the csv file
        f = open(file_nameW + ".csv", "w")
        line = "element_number, cg_x, cg_y, cg_z, element_state, sensitivity_number, "
        for cr in criteria:
            if cr[0] == "stress_von_Mises":
                line += "FI=stress_von_Mises/" + str(cr[1]).strip() + ", "
            else:
                line += "FI=" + cr[1].replace(" ", "") + ", "
        line += "FI_max\n"
        f.write(line)
        for dn in domains_from_config:
            for en in domains[dn]:
                line = str(en) + ", " + str(cg[en][0]) + ", " + str(cg[en][1]) + ", " + str(cg[en][2]) + ", " + \
                    str(elm_states[en]) + ", " + str(sensitivity_number[en]) + ", "
                for FIn in range(len(criteria)):
                    if FI_criteria[en][FIn]:
                        value = FI_criteria[en][FIn]
                    else:
                        value = 0  # since Paraview do not recognise None value
                    line += str(value) + ", "
                line += str(FI_step_max[en]) + "\n"
                f.write(line)
        f.close()


    # function for importing elm_states state from .frd file which was previously created as a resulting mesh
    # it is done via element numbers only; in case of the wrong mesh, no error is recognised
    def import_frd_state(continue_from, elm_states, number_of_states, file_name):
        for state in range(number_of_states):
            try:
                f = open(continue_from[:-5] + str(state) + ".frd", "r")
            except IOError:
                msg = continue_from[:-5] + str(state) + ".frd" + " file not found. Check your inputs."
                BesoLib_types.write_to_log(file_name, "\nERROR: " + msg + "\n")
                assert False, msg

            read_elm = False
            for line in f:
                if line[4:6] == "3C":  # start reading element numbers
                    read_elm = True
                elif read_elm is True and line[1:3] == "-1":
                    en = int(line[3:13])
                    elm_states[en] = state
                elif read_elm is True and line[1:3] == "-3":  # finish reading element numbers
                    break
            f.close()
        return elm_states


    # function for importing elm_states state from .frd file which was previously created as a resulting mesh
    # it is done via element numbers only; in case of the wrong mesh, no error is recognised
    def import_inp_state(continue_from, elm_states, number_of_states, file_name):
        for state in range(number_of_states):
            try:
                f = open(continue_from[:-5] + str(state) + ".inp", "r")
            except IOError:
                msg = continue_from[:-5] + str(state) + ".inp" + " file not found. Check your inputs."
                BesoLib_types.write_to_log(file_name, "\nERROR: " + msg + "\n")
                assert False, msg

            read_elm = False
            for line in f:
                if line[0] == '*' and not line[1] == '*':
                    read_elm = False
                if line[:8].upper() == "*ELEMENT":
                    read_elm = True
                elif read_elm == True:
                    try:
                        en = int(line.split(",")[0])
                        elm_states[en] = state
                    except ValueError:
                        pass
            f.close()
        return elm_states


    # function for importing elm_states state from .csv file
    def import_csv_state(continue_from, elm_states, file_name):
        try:
            f = open(continue_from, "r")
        except IOError:
            msg = continue_from + " file not found. Check your inputs."
            BesoLib_types.write_to_log(file_name, "\nERROR: " + msg + "\n")
            assert False, msg

        headers = f.readline().split(",")
        pos_en = [x.strip() for x in headers].index("element_number")
        pos_state = [x.strip() for x in headers].index("element_state")
        for line in f:
            en = int(line.split(",")[pos_en])
            state = int(line.split(",")[pos_state])
            elm_states[en] = state

        f.close()
        return elm_states
