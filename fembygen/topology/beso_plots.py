# plotting graphs
import os
import FreeCAD
try:
    from FreeCAD.Plot import Plot
except ImportError:
    from freecad.plot import Plot

def QT_TRANSLATE_NOOP(context, text):
    return text
import FreeCADGui
import os

FreeCADGui.addLanguagePath(os.path.join(FreeCAD.getUserAppDataDir(),"\Mod\FEMbyGEN\fembygen\translations"))
FreeCADGui.updateLocale()

fig = Plot.figure(winTitle = "Topology Optimization")
axes = Plot.axesList()
ax1 = axes[0]
ax2 = 0
ax3 = 0
ax4 = 0
ax5 = 0
ax6 = 0
ax7 = 0

def replot(path, i, oscillations, mass, domain_FI_filled, domains_from_config, FI_violated, FI_mean, FI_mean_without_state0,
           FI_max, optimization_base, energy_density_mean, heat_flux_mean, displacement_graph, disp_max,
           buckling_factors_all,savefig=False):
    global ax1
    global ax2
    global ax3
    global ax4
    global ax5
    global ax6
    global ax7
    ax1.cla()
    l1 = ax1.plot(range(i+1), mass/mass[0]*100, label="Mass",color ="red")
    ax1.grid()
    ax1.set_xlabel("Iteration")
    ax1.set_ylabel("Mass %")
    ax1.tick_params(axis='y', colors="red")
    ax1.yaxis.label.set_color("red")
    Plot.plt.pause(0.0001)
    if savefig:
        Plot.save(os.path.join(path, "Mass"))
    
    if oscillations is True:
        i_plot = i - 1  # because other values for i-th iteration are not evaluated
    else:
        i_plot = i

    if optimization_base == "stiffness":
        # plot mean energy density
        if ax2 == 0:
            ax2 = ax1.twinx()
        ax2.cla()
        ax2.spines['right'].set_position(('outward', 0))
        ax2.tick_params(axis='y', colors="orange")
        ax2.set_ylabel("Energy density mean")
        ax2.yaxis.label.set_color("orange")
        ax2.yaxis.set_label_position("right")
        l2 = ax2.plot(range(i_plot+1),energy_density_mean,label ="energy density",color = "orange")
        if ax3 == 0:
            ax1.legend( handles=l1+l2 )
        Plot.plt.pause(0.0001)
        if savefig:
            Plot.save(os.path.join(path, "energy_density_mean"))

    if optimization_base == "heat":
        # plot mean heat flux
        if ax2 == 0:
            ax2 = ax1.twinx()
        ax2.cla()
        ax2.spines['right'].set_position(('outward', 0))
        ax2.tick_params(axis='y', colors="orange")
        ax2.set_ylabel("Heat flux mean")
        ax2.yaxis.label.set_color("orange")
        l2 = ax2.plot(range(i_plot+1), heat_flux_mean,label = "Heat flux mean", color = "orange")
        if ax3 == 0:
            ax1.legend( handles=l1+l2 )
        Plot.plt.pause(0.0001)
        if savefig:
            Plot.save(os.path.join(path, "heat_flux_mean"))

    """if displacement_graph:
        ax.cla()
        ax.set_xlabel("Iteration")
        ax.set_ylabel("Displacement")
        for cn in range(len(displacement_graph)):
            disp_max_cn = []
            for ii in range(i_plot + 1):
                disp_max_cn.append(disp_max[ii][cn])
            ax.plot(range(i + 1), disp_max_cn, label=displacement_graph[cn][0] + "(" + displacement_graph[cn][1] + ")",color ="orange")
        ax.patch.set_alpha(0.01)
        if savefig:
            Plot.save(os.path.join(path, "Displacement_max"))"""

    if optimization_base == "buckling":
        if ax2 == 0:
            ax2 = ax1.twinx()
        ax2.cla()
        ax2.spines['right'].set_position(('outward', 0))
        ax2.tick_params(axis='y', colors="orange")
        ax2.set_ylabel("Energy density mean")
        ax2.yaxis.label.set_color("orange")
        for bfn in range(len(buckling_factors_all[0])):
            buckling_factors_bfn = []
            for ii in range(i_plot + 1):
                buckling_factors_bfn.append(buckling_factors_all[ii][bfn])
            l2 = ax2.plot(range(i_plot + 1), buckling_factors_bfn, label="mode " + str(bfn + 1))
        if ax3 == 0:
            ax1.legend( handles=l1+l2 )    
        Plot.plt.pause(0.0001)
        if savefig:
            Plot.save(os.path.join(path, "buckling_factors"))

    if domain_FI_filled:  # FI contain something
        # plot number of elements with FI > 1
        dno = 0
        if ax3 == 0:
            ax3 = ax1.twinx()
        for dn in domains_from_config:
            FI_violated_dn = []
            for ii in range(i_plot + 1):
                FI_violated_dn.append(FI_violated[ii][dno])
            ax3.spines['right'].set_position(('outward', 50))
            ax3.set_ylabel("FI_violated_dn")
            ax3.tick_params(axis='y', colors="yellow")
            ax3.yaxis.label.set_color("yellow")
            l3 = ax3.plot(range(i_plot + 1), FI_violated_dn, label="FI_violated_dn",color ="yellow")
            if ax5 == 0:
                ax1.legend( handles=l1+l2+l3 )
            dno += 1
        """if len(domains_from_config) > 1:
            FI_violated_total = []
            for ii in range(i_plot + 1):
                FI_violated_total.append(sum(FI_violated[ii]))
            if ax4 == 0:
                ax4 = ax1.twinx()
            ax4.spines['right'].set_position(('outward',300))
            ax4.set_ylabel("FI_violated_total")
            ax4.tick_params(axis='y', colors="red")
            ax4.yaxis.label.set_color("red")
            l4 = ax4.plot(range(i_plot+1), FI_violated_total, label="Total",color ="red")
            if ax5 == 0:
                ax1.legend( handles=l1+l2+l3+l4 )"""
        Plot.plt.pause(0.0001)
        #fig.canvas.flush_events()
        if savefig:
            Plot.save(os.path.join(path, "FI_violated"))
        if ax5 == 0:
            ax5 = ax1.twinx()
        ax5.spines['right'].set_position(('outward', 110))
        ax5.set_ylabel("FI_mean")
        ax5.tick_params(axis='y', colors="cyan")
        ax5.yaxis.label.set_color("cyan")
        l5 = ax5.plot(range(i_plot+1), FI_mean, label="FI_mean",color ="cyan")
        
        if ax5 != 0:
            ax1.legend( handles=l1+l2+l3+l5 )
        if ax6 == 0:
            ax6= ax1.twinx()
        ax6.spines['right'].set_position(('outward',180))
        ax6.set_ylabel("FI_mean_without_state0")
        ax6.yaxis.label.set_color("green")
        ax6.tick_params(axis='y', colors="green")
        l6 = ax6.plot(range(i_plot+1), FI_mean_without_state0, label="without state 0",color = "green")
        if ax7 == 0:
            ax1.legend( handles=l1+l2+l3+l5+l6 )

        
        Plot.plt.pause(0.0001)
        if savefig:
            Plot.save(os.path.join(path, "FI_mean"))
        if ax7 == 0:
            ax7 = ax1.twinx()
        ax7.cla()
        # plot maximal failure indices
        for dn in domains_from_config:
            FI_max_dn = []
            for ii in range(i_plot + 1):
                FI_max_dn.append(FI_max[ii][dn])
            ax7.spines['right'].set_position(('outward', 260))
            ax7.set_ylabel("FI_max_dn")
            ax7.tick_params(axis='y', colors="black")
            ax7.yaxis.label.set_color("black")
            ax7.yaxis.set_label_position("right")
            l7 = ax7.plot(range(i_plot + 1), FI_max_dn, label="FI_max_dn",color ="black")
            
            if ax7 != 0:
                ax1.legend( handles=l1+l2+l3+l5+l6+l7 )

        if savefig:
            Plot.save(os.path.join(path, "FI_max"))

    fig.fig.tight_layout()
    fig.canvas.flush_events()