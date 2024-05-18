import FreeCAD
import os


translate = FreeCAD.Qt.translate

def QT_TRANSLATE_NOOP(context, text):
    return text
import FreeCADGui
FreeCADGui.addLanguagePath(os.path.join(FreeCAD.getUserAppDataDir(),"\Mod\FEMbyGEN\fembygen\translations"))
FreeCADGui.updateLocale()

class BesoMain:
    import FreeCADGui
    import FreeCAD
    import os
    import time
    import sys
    import Fem
    import shutil
    import subprocess
    import numpy as np
    from fembygen.topology import beso_filters, beso_separate, beso_lib

    def __init__(self, analysis):

        self.doc = self.FreeCAD.ActiveDocument
        self.path = self.doc.Topology.path
        self.path_calculix = self.doc.Topology.path_calculix
        self.file_name = self.doc.Topology.file_name
        self.domain_optimized = self.doc.Topology.domain_optimized[analysis]
        self.domains_from_config = self.domain_optimized.keys()
        self.mass_goal_ratio = self.doc.Topology.mass_goal_ratio
        self.continue_from = self.doc.Topology.continue_from
        self.filter_list = self.doc.Topology.filter_list
        self.optimization_base = self.doc.Topology.optimization_base
        self.cpu_cores = self.doc.Topology.cpu_cores
        self.FI_violated_tolerance = self.doc.Topology.FI_violated_tolerance
        self.decay_coefficient = self.doc.Topology.decay_coefficient
        self.shells_as_composite = self.doc.Topology.shells_as_composite
        self.reference_points = self.doc.Topology.reference_points
        self.reference_value = self.doc.Topology.reference_value
        self.mass_addition_ratio = self.doc.Topology.mass_addition_ratio
        self.mass_removal_ratio = self.doc.Topology.mass_removal_ratio
        self.ratio_type = self.doc.Topology.ratio_type
        self.compensate_state_filter = self.doc.Topology.compensate_state_filter
        self.sensitivity_averaging = self.doc.Topology.sensitivity_averaging
        self.steps_superposition = self.doc.Topology.steps_superposition
        self.iterations_limit = self.doc.Topology.iterations_limit
        self.tolerance = self.doc.Topology.tolerance
        self.displacement_graph = self.doc.Topology.displacement_graph
        self.save_iteration_results = self.doc.Topology.save_iteration_results
        self.save_solver_files = self.doc.Topology.save_solver_files
        self.save_resulting_format = self.doc.Topology.save_resulting_format

        self.criteria = []
        self.domain_thickness = {}
        self.domain_offset = {}
        self.domain_orientation = {}
        self.domain_same_state = {}
        self.domain_FI_filled = False
        self.weight_factor2 = {}
        self.near_elm = {}
        self.weight_factor3 = []
        self.near_elm3 = []
        self.near_points = []
        self.weight_factor_node = []
        self.M = []
        self.weight_factor_distance = []
        self.near_nodes = []
        self.above_elm = {}
        self.below_elm = {}
        self.filter_auto = False

        self.domain_density = self.doc.Topology.domain_density[analysis]
        self.domain_material = self.doc.Topology.domain_material[analysis]

        try:
            self.domain_FI = self.doc.Topology.domain_FI[analysis]
            for dn in self.domain_FI:  # extracting each type of criteria
                if self.domain_FI[dn]:
                    self.domain_FI_filled = True
                for state in range(len(self.domain_FI[dn])):
                    for dn_crit in self.domain_FI[dn][state]:
                        if dn_crit not in self.criteria:
                            self.criteria.append(dn_crit)
        except:
            self.domain_FI = {}
        # default values if not defined by user
        for dn in self.domain_optimized:

            try:
                self.domain_thickness[dn] = self.doc.Topology.domain_thickness[analysis][dn]
            except KeyError:
                self.domain_thickness[dn] = []
            try:
                self.domain_offset[dn] = self.doc.Topology.domain_offset[analysis][dn]
            except KeyError:
                self.domain_offset[dn] = 0.0
            try:
                self.domain_orientation[dn] = self.doc.Topology.domain_orientation[analysis][dn]
            except KeyError:
                self.domain_orientation[dn] = []
            try:
                self.domain_same_state[dn] = self.doc.Topology.domain_same_state[analysis][dn]
            except KeyError:
                self.domain_same_state[dn] = False

        self.number_of_states = 0  # find number of states possible in elm_states
        for dn in self.domains_from_config:
            self.number_of_states = max(self.number_of_states, len(self.domain_density[dn]))

        # set an environmental variable driving number of cpu cores to be used by CalculiX

    def createFolder(self, path, file_name):
        try:
            self.os.mkdir(self.os.path.join(path, "topology_iterations"))
        except:
            self.shutil.rmtree(self.os.path.join(path, "topology_iterations"))
            msg = "Earlier topology simulations deleted"
            self.FreeCAD.Console.PrintMessage(msg)
            self.beso_lib.BesoLib_types.write_to_log(file_name, msg)
            self.os.mkdir(self.os.path.join(path, "topology_iterations"))

    def deleteFiles(self, file_nameW, save_solver_files, reference_points):
        if "inp" not in save_solver_files:
            self.os.remove(file_nameW + ".inp")
            if reference_points == "nodes":
                self.os.remove(self.file_name[:-4] + "_separated.inp")
        if "dat" not in save_solver_files:
            self.os.remove(file_nameW + ".dat")
        if "frd" not in save_solver_files:
            self.os.remove(file_nameW + ".frd")
        if "sta" not in save_solver_files:
            self.os.remove(file_nameW + ".sta")
        if "cvg" not in save_solver_files:
            self.os.remove(file_nameW + ".cvg")
        if "12d" not in save_solver_files:
            self.os.remove(file_nameW + ".12d")

    def main(self):
        from fembygen.topology import beso_plots

        self.os.putenv('OMP_NUM_THREADS', str(self.doc.Topology.cpu_cores))
        self.start_time = self.time.time()
        # writing log file with settings
        msg = "\n"
        msg += "---------------------------------------------------\n"
        msg += ("file_name = %s\n" % self.file_name)
        msg += ("Start at    " + self.time.ctime() + "\n\n")
        for dn in self.domain_optimized:
            msg += ("elset_name              = %s\n" % dn)
            msg += ("domain_optimized        = %s\n" % self.domain_optimized[dn])
            msg += ("domain_density          = %s\n" % self.domain_density[dn])
            msg += ("domain_thickness        = %s\n" % self.domain_thickness[dn])
            msg += ("domain_offset           = %s\n" % self.domain_offset[dn])
            msg += ("domain_orientation      = %s\n" % self.domain_orientation[dn])
            try:
                msg += ("domain_FI               = %s\n" % self.domain_FI[dn])
            except:
                msg += "domain_FI               = None\n"
            msg += ("domain_material         = %s\n" % self.domain_material[dn])
            msg += ("domain_same_state       = %s\n" % self.domain_same_state[dn])
            msg += "\n"
        msg += ("mass_goal_ratio         = %s\n" % self.mass_goal_ratio)
        msg += ("continue_from           = %s\n" % self.continue_from)
        msg += ("filter_list             = %s\n" % self.filter_list)
        msg += ("optimization_base       = %s\n" % self.optimization_base)
        msg += ("cpu_cores               = %s\n" % self.cpu_cores)
        msg += ("FI_violated_tolerance   = %s\n" % self.FI_violated_tolerance)
        msg += ("decay_coefficient       = %s\n" % self.decay_coefficient)
        msg += ("shells_as_composite     = %s\n" % self.shells_as_composite)
        msg += ("reference_points        = %s\n" % self.reference_points)
        msg += ("reference_value         = %s\n" % self.reference_value)
        msg += ("mass_addition_ratio     = %s\n" % self.mass_addition_ratio)
        msg += ("mass_removal_ratio      = %s\n" % self.mass_removal_ratio)
        msg += ("ratio_type              = %s\n" % self.ratio_type)
        msg += ("compensate_state_filter = %s\n" % self.compensate_state_filter)
        msg += ("sensitivity_averaging   = %s\n" % self.sensitivity_averaging)
        msg += ("steps_superposition     = %s\n" % self.steps_superposition)
        msg += ("iterations_limit        = %s\n" % self.iterations_limit)
        msg += ("tolerance               = %s\n" % self.tolerance)
        msg += ("displacement_graph      = %s\n" % self.displacement_graph)
        msg += ("save_iteration_results  = %s\n" % self.save_iteration_results)
        msg += ("save_solver_files       = %s\n" % self.save_solver_files)
        msg += ("save_resulting_format   = %s\n" % self.save_resulting_format)
        msg += "\n"
        self.file_name = self.os.path.join(self.path, self.file_name)
        self.beso_lib.BesoLib_types.write_to_log(self.file_name, msg)

        # mesh and domains importing
        [nodes, Elements, domains, opt_domains, en_all, plane_strain, plane_stress, axisymmetry] = self.beso_lib.BesoLib_types.import_inp(
            self.file_name, self.domains_from_config, self.domain_optimized, self.shells_as_composite)
        domain_shells = {}
        domain_volumes = {}
        for dn in self.domains_from_config:  # distinguishing shell elements and volume elements
            domain_shells[dn] = set(domains[dn]).intersection(list(Elements.tria3.keys()) + list(Elements.tria6.keys()) +
                                                              list(Elements.quad4.keys()) + list(Elements.quad8.keys()))
            domain_volumes[dn] = set(domains[dn]).intersection(list(Elements.tetra4.keys()) + list(Elements.tetra10.keys()) +
                                                               list(Elements.hexa8.keys()) + list(Elements.hexa20.keys()) +
                                                               list(Elements.penta6.keys()) + list(Elements.penta15.keys()))

        # initialize element states
        elm_states = {}
        if isinstance(self.continue_from, int):
            for dn in self.domains_from_config:
                if (len(self.domain_density[dn]) - 1) < self.continue_from:
                    sn = len(self.domain_density[dn]) - 1
                    msg = "\nINFO: elements from the domain " + dn + " were set to the highest state.\n"
                    self.beso_lib.BesoLib_types.write_to_log(self.file_name, msg)
                    print(msg)
                else:
                    sn = self.continue_from
                for en in domains[dn]:
                    elm_states[en] = sn
        elif self.continue_from[-4:] == ".frd":
            elm_states = self.beso_lib.import_frd_state(
                self.continue_from, elm_states, self.number_of_states, self.file_name)
        elif self.continue_from[-4:] == ".inp":
            elm_states = self.beso_lib.import_inp_state(
                self.continue_from, elm_states, self.number_of_states, self.file_name)
        elif self.continue_from[-4:] == ".csv":
            elm_states = self.beso_lib.import_csv_state(self.continue_from, elm_states, self.file_name)
        else:
            for dn in self.domains_from_config:
                for en in domains[dn]:
                    elm_states[en] = len(self.domain_density[dn]) - 1  # set to highest state

        # computing volume or area, and centre of gravity of each element
        [cg, cg_min, cg_max, volume_elm, area_elm] = self.beso_lib.elm_volume_cg(self.file_name, nodes, Elements).elm_volume_cg()
        mass = [0.0]
        print(cg)
        mass_full = 0  # sum from initial states TODO make it independent on starting elm_states?

        for dn in self.domains_from_config:
            if self.domain_optimized[dn] is True:
                for en in domain_shells[dn]:
                    mass[0] += self.domain_density[dn][elm_states[en]] * \
                        area_elm[en] * self.domain_thickness[dn][elm_states[en]]
                    mass_full += self.domain_density[dn][len(self.domain_density[dn]) - 1] * area_elm[en] * self.domain_thickness[dn][
                        len(self.domain_density[dn]) - 1]
                for en in domain_volumes[dn]:
                    mass[0] += self.domain_density[dn][elm_states[en]] * volume_elm[en]
                    mass_full += self.domain_density[dn][len(self.domain_density[dn]) - 1] * volume_elm[en]
        print(translate("FEMbyGEN","initial optimization domains mass {}" .format(mass[0])))

        if self.iterations_limit == "auto":  # automatic setting
            m = mass[0] / mass_full
            if self.ratio_type == "absolute" and (self.mass_removal_ratio - self.mass_addition_ratio > 0):
                iterations_limit = int((m - self.mass_goal_ratio) /
                                       (self.mass_removal_ratio - self.mass_addition_ratio) + 25)
            elif self.ratio_type == "absolute" and (self.mass_removal_ratio - self.mass_addition_ratio < 0):
                iterations_limit = int((self.mass_goal_ratio - m) /
                                       (self.mass_addition_ratio - self.mass_removal_ratio) + 25)
            elif self.ratio_type == "relative":
                it = 0
                if self.mass_removal_ratio - self.mass_addition_ratio > 0:
                    while m > self.mass_goal_ratio:
                        m -= m * (self.mass_removal_ratio - self.mass_addition_ratio)
                        it += 1
                else:
                    while m < self.mass_goal_ratio:
                        m += m * (self.mass_addition_ratio - self.mass_removal_ratio)
                        it += 1
                iterations_limit = it + 25
            print(translate("FEMbyGEN","\niterations_limit set automatically to %s" % iterations_limit))
            msg = ("\niterations_limit        = %s\n" % iterations_limit)
            self.beso_lib.BesoLib_types.write_to_log(self.file_name, msg)

        # preparing parameters for filtering sensitivity numbers
        """weight_factor2 = {}
        near_elm = {}
        weight_factor3 = []
        near_elm3 = []
        near_points = []
        weight_factor_node = []
        M = []
        weight_factor_distance = []
        near_nodes = []
        above_elm = {}
        below_elm = {}
        filter_auto = False"""
        for ft in self.filter_list:  # find if automatic filter range is used
            if ft[0] and (ft[1] == "auto") and not self.filter_auto:
                size_elm = self.beso_filters.BesoFilters(Elements,nodes).find_size_elm()
                self.filter_auto = True
        for ft in self.filter_list:
            if ft[0] and ft[1]:
                f_range = ft[1]
                if ft[0] == "casting":
                    if len(ft) == 3:
                        domains_to_filter = list(opt_domains)
                        filtered_dn = self.domains_from_config
                        self.beso_filters.BesoFilters(Elements,nodes).check_same_state(
                            self.domain_same_state, self.domains_from_config, self.file_name)
                    else:
                        domains_to_filter = []
                        filtered_dn = []
                        for dn in ft[3:]:
                            domains_to_filter += domains[dn]
                            filtered_dn.append(dn)
                        self.beso_filters.BesoFilters(Elements,nodes).check_same_state(self.domain_same_state, filtered_dn, self.file_name)
                    casting_vector = ft[2]
                    casting_vector = casting_vector.strip('()')
                    casting_vector = casting_vector.split(',')
                    casting_vector = [float(x) for x in casting_vector]
                    casting_vector = self.np.array(casting_vector)
                    if f_range == "auto":
                        size_avg = self.beso_filters.BesoFilters(Elements,nodes).get_filter_range(size_elm, domains, filtered_dn)
                        f_range = size_avg * 2
                        msg = "Filtered average element size is {}, filter range set automatically to {}".format(size_avg,
                                                                                                                 f_range)
                        print(msg)
                        self.beso_lib.BesoLib_types.write_to_log(self.file_name, msg)
                    [above_elm, below_elm] = self.beso_filters.BesoFilters(Elements,nodes).prepare2s_casting(cg, f_range, domains_to_filter,
                                                                                 above_elm, below_elm, casting_vector)
                    continue  # to evaluate other filters
                if len(ft) == 2:
                    domains_to_filter = list(opt_domains)
                    print(translate("FEMbyGEN","!!!!!! Domains to filter !!!!!!"))
                    print(domains_to_filter)
                    filtered_dn = self.domains_from_config
                    self.beso_filters.BesoFilters(Elements,nodes).check_same_state(self.domain_same_state, filtered_dn, self.file_name)
                else:
                    domains_to_filter = []
                    filtered_dn = []
                    for dn in ft[3:]:
                        domains_to_filter += domains[dn]
                        filtered_dn.append(dn)
                    self.beso_filters.BesoFilters(Elements,nodes).check_same_state(self.domain_same_state, filtered_dn, self.file_name)
                if f_range == "auto":
                    size_avg = self.beso_filters.BesoFilters(Elements,nodes).get_filter_range(size_elm,domains, filtered_dn)
                    f_range = size_avg * 2
                    msg = "Filtered average element size is {}, filter range set automatically to {}".format(
                        size_avg, f_range)
                    print(msg)
                    self.beso_lib.BesoLib_types.write_to_log(self.file_name, msg)
                if ft[0] == "over points":
                    self.beso_filters.BesoFilters(Elements,nodes).check_same_state(self.domain_same_state, self.domains_from_config, self.file_name)
                    [w_f3, n_e3, n_p] = self.beso_filters.BesoFilters(Elements,nodes).prepare3_tetra_grid(
                        self.file_name, cg, f_range, domains_to_filter)
                    self.weight_factor3.append(w_f3)
                    self.near_elm3.append(n_e3)
                    self.near_points.append(n_p)
                elif ft[0] == "over nodes":
                    self.beso_filters.BesoFilters(Elements,nodes).check_same_state(self.domain_same_state, self.domains_from_config, self.file_name)
                    [w_f_n, M_, w_f_d, n_n] = self.beso_filters.BesoFilters(Elements,nodes).prepare1s(
                        nodes, Elements, cg, f_range, domains_to_filter)
                    self.weight_factor_node.append(w_f_n)
                    self.M.append(M_)
                    self.weight_factor_distance.append(w_f_d)
                    self.near_nodes.append(n_n)
                elif ft[0] == "simple":
                    [weight_factor2, near_elm] = self.beso_filters.BesoFilters(Elements,nodes).prepare2s(cg, cg_min, cg_max, f_range, domains_to_filter,
                                                                             self.weight_factor2, self.near_elm)
                elif ft[0].split()[0] in ["erode", "dilate", "open", "close", "open-close", "close-open", "combine"]:
                    near_elm = self.beso_filters.BesoFilters(Elements,nodes).prepare_morphology(
                        cg, cg_min, cg_max, f_range, domains_to_filter, near_elm)

        # separating elements for reading nodal input
        if self.reference_points == "nodes":
            self.beso_separate.separating(self.file_name, nodes)

        # writing log table header
        msg = "\n"
        msg += "domain order: \n"
        dorder = 0
        for dn in self.domains_from_config:
            msg += str(dorder) + ") " + dn + "\n"
            dorder += 1
        msg += "\n   i              mass"
        if self.optimization_base == "stiffness":
            msg += "    ener_dens_mean"
        if self.optimization_base == "heat":
            msg += "    heat_flux_mean"
        if self.domain_FI_filled:
            msg += " FI_violated_0)"
            for dno in range(len(self.domains_from_config) - 1):
                msg += (" " + str(dno + 1)).rjust(4, " ") + ")"
            if len(self.domains_from_config) > 1:
                msg += " all)"
            msg += "          FI_mean    _without_state0         FI_max_0)"
            for dno in range(len(self.domains_from_config) - 1):
                msg += str(dno + 1).rjust(17, " ") + ")"
            if len(self.domains_from_config) > 1:
                msg += "all".rjust(17, " ") + ")"
        if self.displacement_graph:
            for (ns, component) in self.displacement_graph:
                if component == "total":  # total displacement
                    msg += (" " + ns + "(u_total)").rjust(18, " ")
                else:
                    msg += (" " + ns + "(" + component + ")").rjust(18, " ")
        if self.optimization_base == "buckling":
            msg += "  buckling_factors"

        msg += "\n"
        self.beso_lib.BesoLib_types.write_to_log(self.file_name, msg)

        # preparing for writing quick results
        file_name_resulting_states = self.os.path.join(self.path, "resulting_states")
        [en_all_vtk, associated_nodes] = self.beso_lib.vtk_mesh(file_name_resulting_states, nodes, Elements)
        # prepare for plotting
        # beso_plots.plotshow(domain_FI_filled, optimization_base, displacement_graph)

        # ITERATION CYCLE
        sensitivity_number = {}
        sensitivity_number_old = {}
        FI_max = []
        FI_mean = []  # list of mean stress in every iteration
        FI_mean_without_state0 = []  # mean stress without elements in state 0
        energy_density_mean = []  # list of mean energy density in every iteration
        heat_flux_mean = []  # list of mean heat flux in every iteration
        FI_violated = []
        disp_max = []
        buckling_factors_all = []
        i = 0
        i_violated = 0
        continue_iterations = True
        check_tolerance = False
        mass_excess = 0.0
        elm_states_before_last = {}
        elm_states_last = elm_states
        oscillations = False

        self.createFolder(self.path, self.file_name)

        while True:
            if self.FreeCADGui.activeDocument() == None:
                self.doc.Topology.LastState = 0
                break
            # creating the new .inp file for CalculiX
            file_nameW = self.os.path.join(self.path, "topology_iterations", "file" + str(i).zfill(3))
            self.beso_lib.write_inp(self.file_name, file_nameW, elm_states, self.number_of_states, domains, self.domains_from_config,
                                    self.domain_optimized, self.domain_thickness, self.domain_offset, self.domain_orientation, self.domain_material,
                                    domain_volumes, domain_shells, plane_strain, plane_stress, axisymmetry, self.save_iteration_results,
                                    i, self.reference_points, self.shells_as_composite, self.optimization_base, self.displacement_graph,
                                    self.domain_FI_filled).write_inp_function()
            # running CalculiX analysis

            if self.sys.platform.startswith('linux'):
                self.subprocess.call([self.os.path.normpath(self.path_calculix), file_nameW], cwd=self.path)
            else:
                self.subprocess.call([self.os.path.normpath(self.path_calculix), file_nameW], cwd=self.path, shell=True)

            # reading results and computing failure indices
            if (self.reference_points == "integration points") or (self.optimization_base == "stiffness") or \
                    (self.optimization_base == "buckling") or (self.optimization_base == "heat"):  # from .dat file
                [FI_step, energy_density_step, disp_i, buckling_factors, energy_density_eigen, heat_flux] = \
                    self.beso_lib.import_FI_int_pt(self.reference_value, file_nameW, domains, self.criteria, self.domain_FI, self.file_name, elm_states,
                                                   self.domains_from_config, self.steps_superposition, self.displacement_graph)
            if self.reference_points == "nodes":  # from .frd file
                FI_step = self.beso_lib.import_FI_node(self.reference_value, file_nameW, domains, self.criteria, self.domain_FI, self.file_name,
                                                       elm_states, self.steps_superposition).import_FI_node()
                disp_i = self.beso_lib.import_displacement(
                    file_nameW, self.displacement_graph, self.steps_superposition)
            disp_max.append(disp_i)

            # check if results were found
            missing_ccx_results = False
            if (self.optimization_base == "stiffness") and (not energy_density_step):
                missing_ccx_results = True
            elif (self.optimization_base == "buckling") and (not buckling_factors):
                missing_ccx_results = True
            elif (self.optimization_base == "heat") and (not heat_flux):
                missing_ccx_results = True
            elif self.domain_FI_filled and (not FI_step):
                missing_ccx_results = True
            if missing_ccx_results:
                msg = "CalculiX results not found, check CalculiX for errors. Ensure you choose the right optimization base"
                self.beso_lib.BesoLib_types.write_to_log(self.file_name, "\nERROR: " + msg + "\n")
                assert False, msg

            if self.domain_FI_filled:
                FI_max.append({})
                for dn in self.domains_from_config:
                    FI_max[i][dn] = 0
                    for en in domains[dn]:
                        for sn in range(len(FI_step)):
                            try:
                                FI_step_en = list(filter(lambda a: a is not None, FI_step[sn][en]))  # drop None FI
                                FI_max[i][dn] = max(FI_max[i][dn], max(FI_step_en))
                            except ValueError:
                                msg = "FI_max computing failed. Check if each domain contains at least one failure criterion."
                                self.beso_lib.BesoLib_types.write_to_log(self.file_name, "\nERROR: " + msg + "\n")
                                raise Exception(msg)
                            except KeyError:
                                msg = "Some result values are missing. Check available disk space or steps_superposition " \
                                    "settings"
                                self.beso_lib.BesoLib_types.write_to_log(self.file_name, "\nERROR: " + msg + "\n")
                                raise Exception(msg)
                print(translate("FEMbyGEN","FI_max, number of violated elements, domain name"))

            # handling with more steps
            FI_step_max = {}  # maximal FI over all steps for each element in this iteration
            energy_density_enlist = {}   # {en1: [energy from sn1, energy from sn2, ...], en2: [], ...}
            FI_violated.append([])
            dno = 0
            for dn in self.domains_from_config:
                FI_violated[i].append(0)
                for en in domains[dn]:
                    FI_step_max[en] = 0
                    if self.optimization_base == "stiffness":
                        energy_density_enlist[en] = []
                    for sn in range(len(FI_step)):
                        if self.domain_FI_filled:
                            FI_step_en = list(filter(lambda a: a is not None, FI_step[sn][en]))  # drop None FI
                            FI_step_max[en] = max(FI_step_max[en], max(FI_step_en))
                        if self.optimization_base == "stiffness":
                            energy_density_enlist[en].append(energy_density_step[sn][en])
                    if self.optimization_base == "stiffness":
                        sensitivity_number[en] = max(energy_density_enlist[en])
                    elif self.optimization_base == "heat":
                        try:
                            sensitivity_number[en] = heat_flux[en] / volume_elm[en]
                        except KeyError:
                            sensitivity_number[en] = heat_flux[en] / \
                                (area_elm[en] * self.domain_thickness[dn][elm_states[en]])
                    elif self.optimization_base == "failure_index":
                        sensitivity_number[en] = FI_step_max[en] / self.domain_density[dn][elm_states[en]]
                    if self.domain_FI_filled:
                        if FI_step_max[en] >= 1:
                            FI_violated[i][dno] += 1
                if self.domain_FI_filled:
                    print(str(FI_max[i][dn]).rjust(15) + " " + str(FI_violated[i][dno]).rjust(4) + "   " + dn)
                dno += 1

            # buckling sensitivities
            if self.optimization_base == "buckling":
                # eigen energy density normalization
                # energy_density_eigen[eigen_number][en_last] = np.average(ener_int_pt)
                denominator = []  # normalization denominator for each buckling factor with numbering from 0
                for eigen_number in energy_density_eigen:  # numbering from 1
                    denominator.append(max(energy_density_eigen[eigen_number].values()))
                bf_dif = {}
                bf_coef = {}
                buckling_influence_tolerance = 0.2  # Ki - K1 tolerance to influence sensitivity
                for bfn in range(len(buckling_factors) - 1):
                    bf_dif_i = buckling_factors[bfn + 1] - buckling_factors[0]
                    if bf_dif_i < buckling_influence_tolerance:
                        bf_dif[bfn] = bf_dif_i
                        bf_coef[bfn] = bf_dif_i / buckling_influence_tolerance
                for dn in self.domains_from_config:
                    for en in domains[dn]:
                        sensitivity_number[en] = energy_density_eigen[1][en] / denominator[0]
                        for bfn in bf_dif:
                            sensitivity_number[en] += energy_density_eigen[bfn + 1][en] / \
                                denominator[bfn] * bf_coef[bfn]

            # filtering sensitivity number
            kp = 0
            kn = 0
            for ft in self.filter_list:
                if ft[0] and ft[1]:
                    if ft[0] == "casting":
                        if len(ft) == 3:
                            domains_to_filter = list(opt_domains)
                        else:
                            domains_to_filter = []
                            for dn in ft[3:]:
                                domains_to_filter += domains[dn]
                        sensitivity_number = self.beso_filters.BesoFilters(Elements,nodes).run2_casting(sensitivity_number, above_elm, below_elm,
                                                                            domains_to_filter)
                        continue  # to evaluate other filters
                    if len(ft) == 2:
                        domains_to_filter = list(opt_domains)
                    else:
                        domains_to_filter = []
                        for dn in ft[2:]:
                            domains_to_filter += domains[dn]
                    if ft[0] == "over points":
                        sensitivity_number = self.beso_filters.BesoFilters(Elements,nodes).run3(sensitivity_number, self.weight_factor3[kp], self.near_elm3[kp],
                                                                    self.near_points[kp])
                        kp += 1
                    elif ft[0] == "over nodes":
                        sensitivity_number = self.beso_filters.BesoFilters(Elements,nodes).run1(self.file_name, sensitivity_number, self.weight_factor_node[kn], self.M[kn],
                                                                    self.weight_factor_distance[kn], self.near_nodes[kn], nodes,
                                                                    domains_to_filter)
                        kn += 1
                    elif ft[0] == "simple":
                        sensitivity_number = self.beso_filters.BesoFilters.run2(self.file_name, sensitivity_number, weight_factor2, near_elm,
                                                                    domains_to_filter)
                    elif ft[0].split()[0] in ["erode", "dilate", "open", "close", "open-close", "close-open", "combine"]:
                        if ft[0].split()[1] == "sensitivity":
                            sensitivity_number = self.beso_filters.BesoFilters(Elements,nodes).run_morphology(sensitivity_number, near_elm, domains_to_filter,
                                                                                  ft[0].split()[0])

            if self.sensitivity_averaging:
                for en in opt_domains:
                    # averaging with the last iteration should stabilize iterations
                    if i > 0:
                        sensitivity_number[en] = (sensitivity_number[en] + sensitivity_number_old[en]) / 2.0
                    sensitivity_number_old[en] = sensitivity_number[en]  # for averaging in the next step

            # computing mean stress from maximums of each element in all steps in the optimization domain
            if self.domain_FI_filled:
                FI_mean_sum = 0
                FI_mean_sum_without_state0 = 0
                mass_without_state0 = 0
            if self.optimization_base == "stiffness":
                energy_density_mean_sum = 0  # mean of element maximums
            if self.optimization_base == "heat":
                heat_flux_mean_sum = 0
            for dn in self.domain_optimized:
                if self.domain_optimized[dn] is True:
                    for en in domain_shells[dn]:
                        mass_elm = self.domain_density[dn][elm_states[en]] * \
                            area_elm[en] * self.domain_thickness[dn][elm_states[en]]
                        if self.domain_FI_filled:
                            FI_mean_sum += FI_step_max[en] * mass_elm
                            if elm_states[en] != 0:
                                FI_mean_sum_without_state0 += FI_step_max[en] * mass_elm
                                mass_without_state0 += mass_elm
                        if self.optimization_base == "stiffness":
                            energy_density_mean_sum += max(energy_density_enlist[en]) * mass_elm
                        if self.optimization_base == "heat":
                            heat_flux_mean_sum += heat_flux[en] * mass_elm
                    for en in domain_volumes[dn]:
                        mass_elm = self.domain_density[dn][elm_states[en]] * volume_elm[en]
                        if self.domain_FI_filled:
                            FI_mean_sum += FI_step_max[en] * mass_elm
                            if elm_states[en] != 0:
                                FI_mean_sum_without_state0 += FI_step_max[en] * mass_elm
                                mass_without_state0 += mass_elm
                        if self.optimization_base == "stiffness":
                            energy_density_mean_sum += max(energy_density_enlist[en]) * mass_elm
                        if self.optimization_base == "heat":
                            heat_flux_mean_sum += heat_flux[en] * mass_elm
            if self.domain_FI_filled:
                FI_mean.append(FI_mean_sum / mass[i])
                print("FI_mean                = {}".format(FI_mean[i]))
                if mass_without_state0:
                    FI_mean_without_state0.append(FI_mean_sum_without_state0 / mass_without_state0)
                    print("FI_mean_without_state0 = {}".format(FI_mean_without_state0[i]))
                else:
                    FI_mean_without_state0.append("NaN")
            if self.optimization_base == "stiffness":
                energy_density_mean.append(energy_density_mean_sum / mass[i])
                print("energy_density_mean    = {}".format(energy_density_mean[i]))
            if self.optimization_base == "heat":
                heat_flux_mean.append(heat_flux_mean_sum / mass[i])
                print("heat_flux_mean         = {}".format(heat_flux_mean[i]))

            if self.optimization_base == "buckling":
                k = 1
                for bf in buckling_factors:
                    print(translate("FEMbyGEN","buckling factor K{} = {}".format(k, bf)))
                    k += 1
            # writing log table row
            msg = str(i).rjust(4, " ") + " " + str(mass[i]).rjust(17, " ") + " "
            if self.optimization_base == "stiffness":
                msg += " " + str(energy_density_mean[i]).rjust(17, " ")
            if self.optimization_base == "heat":
                msg += " " + str(heat_flux_mean[i]).rjust(17, " ")
            if self.domain_FI_filled:
                msg += str(FI_violated[i][0]).rjust(13, " ")
                for dno in range(len(self.domains_from_config) - 1):
                    msg += " " + str(FI_violated[i][dno + 1]).rjust(4, " ")
                if len(self.domains_from_config) > 1:
                    msg += " " + str(sum(FI_violated[i])).rjust(4, " ")
                msg += " " + str(FI_mean[i]).rjust(17, " ") + " " + str(FI_mean_without_state0[i]).rjust(18, " ")
                FI_max_all = 0
                for dn in self.domains_from_config:
                    msg += " " + str(FI_max[i][dn]).rjust(17, " ")
                    FI_max_all = max(FI_max_all, FI_max[i][dn])
                if len(self.domains_from_config) > 1:
                    msg += " " + str(FI_max_all).rjust(17, " ")
            for cn in range(len(self.displacement_graph)):
                msg += " " + str(disp_i[cn]).rjust(17, " ")
            if self.optimization_base == "buckling":
                for bf in buckling_factors:
                    msg += " " + str(bf).rjust(17, " ")
                buckling_factors_all.append(buckling_factors)
            msg += "\n"
            self.beso_lib.BesoLib_types.write_to_log(self.file_name, msg)

            # export element values
            if self.save_iteration_results and self.np.mod(float(i), self.save_iteration_results) == 0:
                if "csv" in self.save_resulting_format:
                    self.beso_lib.export_csv(self.domains_from_config, domains, self.criteria, FI_step, FI_step_max, file_nameW, cg,
                                             elm_states, sensitivity_number)
                if "vtk" in self.save_resulting_format:
                    self.beso_lib.export_vtk(file_nameW, nodes, Elements, elm_states, sensitivity_number, self.criteria, FI_step,
                                             FI_step_max)

            # relative difference in a mean stress for the last 5 iterations must be < tolerance
            if len(FI_mean) > 5:
                difference_last = []
                for last in range(1, 6):
                    difference_last.append(abs(FI_mean[i] - FI_mean[i-last]) / FI_mean[i])
                difference = max(difference_last)
                if check_tolerance is True:
                    print(translate("FEMbyGEN","maximum relative difference in FI_mean for the last 5 iterations = {}" .format(difference)))
                if difference < self.tolerance:
                    continue_iterations = False
                elif FI_mean[i] == FI_mean[i-1] == FI_mean[i-2]:
                    continue_iterations = False
                    print("FI_mean[i] == FI_mean[i-1] == FI_mean[i-2]")
            # relative difference in a mean energy density for the last 5 iterations must be < tolerance
            if len(energy_density_mean) > 5:
                difference_last = []
                for last in range(1, 6):
                    try:
                        difference_last.append(
                            abs(energy_density_mean[i] - energy_density_mean[i - last]) / energy_density_mean[i])

                    except:
                        print(translate("FEMbyGEN","energy_density_mean is 0"))
                        difference_last.append(0)
                difference = max(difference_last)
                if check_tolerance is True:
                    print(translate("FEMbyGEN","maximum relative difference in energy_density_mean for the last 5 iterations = {}".format(difference)))
                if difference < self.tolerance:
                    continue_iterations = False
                elif energy_density_mean[i] == energy_density_mean[i - 1] == energy_density_mean[i - 2]:
                    continue_iterations = False
                    print(translate("FEMbyGEN","energy_density_mean[i] == energy_density_mean[i-1] == energy_density_mean[i-2]"))

            # finish or start new iteration
            if continue_iterations is False or i >= iterations_limit:
                if not(self.save_iteration_results and self.np.mod(float(i), self.save_iteration_results) == 0):
                    if "csv" in self.save_resulting_format:
                        self.beso_lib.export_csv(self.domains_from_config, domains, self.criteria, FI_step, FI_step_max, file_nameW, cg,
                                                 elm_states, sensitivity_number)
                    if "vtk" in self.save_resulting_format:
                        self.beso_lib.export_vtk(file_nameW, nodes, Elements, elm_states, sensitivity_number, self.criteria, FI_step,
                                                 FI_step_max)
                self.doc.Topology.LastState = i
                break
            # plot and save figures
            beso_plots.replot(self.path, i, oscillations, mass, self.domain_FI_filled, self.domains_from_config, FI_violated, FI_mean,
                              FI_mean_without_state0, FI_max, self.optimization_base, energy_density_mean, heat_flux_mean,
                              self.displacement_graph, disp_max, buckling_factors_all, savefig=True)

            i += 1  # iteration number
            print(translate("FEMbyGEN","\n----------- new iteration number %d ----------" % i))

            # set mass_goal for i-th iteration, check for number of violated elements
            if self.mass_removal_ratio - self.mass_addition_ratio > 0:  # removing from initial mass
                if sum(FI_violated[i - 1]) > sum(FI_violated[0]) + self.FI_violated_tolerance:
                    if mass[i - 1] >= self.mass_goal_ratio * mass_full:
                        mass_goal_i = mass[i - 1]  # use mass_new from previous iteration
                    else:  # not to drop below goal mass
                        mass_goal_i = self.mass_goal_ratio * mass_full
                    if i_violated == 0:
                        i_violated = i
                        check_tolerance = True
                elif mass[i - 1] <= self.mass_goal_ratio * mass_full:  # goal mass achieved
                    if not i_violated:
                        i_violated = i  # to start decaying
                        check_tolerance = True
                    try:
                        mass_goal_i
                    except NameError:
                        msg = "\nWARNING: mass goal is lower than initial mass. Check mass_goal_ratio."
                        self.beso_lib.BesoLib_types.write_to_log(self.file_name, msg + "\n")
                else:
                    mass_goal_i = self.mass_goal_ratio * mass_full
            else:  # adding to initial mass  TODO include stress limit
                if mass[i - 1] < self.mass_goal_ratio * mass_full:
                    mass_goal_i = mass[i - 1] + (self.mass_addition_ratio - self.mass_removal_ratio) * mass_full
                elif mass[i - 1] >= self.mass_goal_ratio * mass_full:
                    if not i_violated:
                        i_violated = i  # to start decaying
                        check_tolerance = True
                    mass_goal_i = self.mass_goal_ratio * mass_full

            # switch element states
            if self.ratio_type == "absolute":
                mass_referential = mass_full
            elif self.ratio_type == "relative":
                mass_referential = mass[i - 1]
            [elm_states, mass] = self.beso_lib.switching(elm_states, self.domains_from_config, self.domain_optimized, domains, FI_step_max,
                                                         self.domain_density, self.domain_thickness, domain_shells, area_elm, volume_elm,
                                                         sensitivity_number, mass, mass_referential, self.mass_addition_ratio,
                                                         self.mass_removal_ratio, self.compensate_state_filter, mass_excess, self.decay_coefficient,
                                                         FI_violated, i_violated, i, mass_goal_i, self.domain_same_state).switching()

            # filtering state
            mass_not_filtered = mass[i]  # use variable to store the "right" mass
            for ft in self.filter_list:
                if ft[0] and ft[1]:
                    if ft[0] == "casting":
                        continue  # to evaluate other filters
                    if len(ft) == 2:
                        domains_to_filter = list(opt_domains)
                    else:
                        domains_to_filter = []
                        for dn in ft[2:]:
                            domains_to_filter += domains[dn]

                    if ft[0].split()[0] in ["erode", "dilate", "open", "close", "open-close", "close-open", "combine"]:
                        if ft[0].split()[1] == "state":
                            # the same filter as for sensitivity numbers
                            elm_states_filtered = self.beso_filters.BesoFilters(Elements,nodes).run_morphology(elm_states, near_elm, domains_to_filter,
                                                                                   ft[0].split()[0], FI_step_max)
                            # compute mass difference
                            for dn in self.domains_from_config:
                                if self.domain_optimized[dn] is True:
                                    for en in domain_shells[dn]:
                                        if elm_states[en] != elm_states_filtered[en]:
                                            mass[i] += area_elm[en] * (
                                                self.domain_density[dn][elm_states_filtered[en]] * self.domain_thickness[dn][
                                                    elm_states_filtered[en]]
                                                - self.domain_density[dn][elm_states[en]] * self.domain_thickness[dn][elm_states[en]])
                                            elm_states[en] = elm_states_filtered[en]
                                    for en in domain_volumes[dn]:
                                        if elm_states[en] != elm_states_filtered[en]:
                                            mass[i] += volume_elm[en] * (
                                                self.domain_density[dn][elm_states_filtered[en]] - self.domain_density[dn][elm_states[en]])
                                            elm_states[en] = elm_states_filtered[en]
            print("mass = {}" .format(mass[i]))
            mass_excess = mass[i] - mass_not_filtered

            # export the present mesh
            self.beso_lib.append_vtk_states(file_name_resulting_states, i, en_all_vtk, elm_states)

            file_nameW2 = self.os.path.join(self.path, "topology_iterations", "file" + str(i).zfill(3))
            if self.save_iteration_results and self.np.mod(float(i), self.save_iteration_results) == 0:
                if "frd" in self.save_resulting_format:
                    self.beso_lib.export_frd(file_nameW2, nodes, Elements, elm_states, self.number_of_states)
                if "inp" in self.save_resulting_format:
                    self.beso_lib.export_inp(file_nameW2, nodes, Elements, elm_states, self.number_of_states)

            # check for oscillation state
            if elm_states_before_last == elm_states:  # oscillating state
                msg = "\nOSCILLATION: model turns back to " + str(i - 2) + "th iteration.\n"
                self.beso_lib.BesoLib_types.write_to_log(self.file_name, msg)
                print(msg)
                oscillations = True
                if i > 2:
                    self.doc.Topology.LastState = i-2
                else:
                    self.doc.Topology.LastState = i
                break
            elm_states_before_last = elm_states_last.copy()
            elm_states_last = elm_states.copy()

            # removing solver files
            if self.save_iteration_results and (i - 1) % self.save_iteration_results == 0:
                self.deleteFiles(file_nameW, self.save_solver_files, self.reference_points)

            else:
                self.os.remove(file_nameW + ".inp")
                self.os.remove(file_nameW + ".dat")
                self.os.remove(file_nameW + ".frd")
                self.os.remove(file_nameW + ".sta")
                self.os.remove(file_nameW + ".cvg")
                self.os.remove(file_nameW + ".12d")

        # export the resulting mesh
        if not (self.save_iteration_results and self.np.mod(float(i), self.save_iteration_results) == 0):
            if "frd" in self.save_resulting_format:
                self.beso_lib.export_frd(file_nameW, nodes, Elements, elm_states, self.number_of_states)
            if "inp" in self.save_resulting_format:
                self.beso_lib.export_inp(file_nameW, nodes, Elements, elm_states, self.number_of_states)

        # removing solver files
        self.deleteFiles(file_nameW, self.save_solver_files, self.reference_points)

        # plot and save figures
        beso_plots.replot(self.path, i, oscillations, mass, self.domain_FI_filled, self.domains_from_config, FI_violated, FI_mean,
                          FI_mean_without_state0, FI_max, self.optimization_base, energy_density_mean, heat_flux_mean,
                          self.displacement_graph, disp_max, buckling_factors_all, savefig=True)
        # print total time
        total_time = self.time.time() - self.start_time
        total_time_h = int(total_time / 3600.0)
        total_time_min = int((total_time % 3600) / 60.0)
        total_time_s = int(round(total_time % 60))
        msg = "\n"
        msg += ("Finished at  " + self.time.ctime() + "\n")
        showMsg = ("Total time   " + str(total_time_h) + " h " +
                   str(total_time_min) + " min " + str(total_time_s) + " \n")
        msg += showMsg + "\n"
        self.beso_lib.BesoLib_types.write_to_log(self.file_name, msg)
        print(showMsg)
