import os, sys, csv
import matplotlib
matplotlib.use('Agg') # Terminalde çalışırken ekran hatası almamak için
import matplotlib.pyplot as plt

# ============================================================
# --- 0. BAĞLANTI AYARLARI ---
# ============================================================
FREECAD_BIN = r"C:\Program Files\FreeCAD 1.0\bin"
KLASOR_YOLU = r"C:\fork"
FC_DOSYA_ADI = "valfmacrolast.FCStd" 
CSV_DOSYA_ADI = "spreadsheet.csv"

FC_DOSYA_YOLU = os.path.join(KLASOR_YOLU, FC_DOSYA_ADI)
GIRDI_DOSYASI = os.path.join(KLASOR_YOLU, CSV_DOSYA_ADI)
OUTPUT_BASE = "C:/SurguValf_Analizleri"

if FREECAD_BIN not in sys.path:
    sys.path.append(FREECAD_BIN)

import FreeCAD
from CfdOF import CfdTools, CfdConsoleProcess
from CfdOF.Mesh import CfdMeshTools
from CfdOF.Solve import CfdCaseWriterFoam, CfdRunnableFoam

# ============================================================
# --- 1. GRAFİK VE TABLO FONKSİYONLARI ---
# ============================================================
def oku_kuvvet(solver_dizini):
    pp_dir = os.path.join(solver_dizini, "postProcessing")
    if not os.path.exists(pp_dir): return 0.0
    for root, dirs, files in os.walk(pp_dir):
        for f_name in files:
            full_path = os.path.join(root, f_name)
            if "force" in f_name.lower() and f_name.endswith(".dat"):
                try:
                    with open(full_path, 'r') as f:
                        lines = [l.strip() for l in f.readlines() if l.strip() and not l.startswith('#')]
                        if lines:
                            p = lines[-1].replace('(', ' ').replace(')', ' ').replace(',', ' ').split()
                            if len(p) > 6: return abs(float(p[3]) + float(p[6]))
                except: pass
    return 0.0

def grafik_ciz(solver_dizini, kayit_yolu, vaka_adi):
    pp_dir = os.path.join(solver_dizini, "postProcessing")
    force_file = None
    for root, dirs, files in os.walk(pp_dir):
        for f in files:
            if "force" in f.lower() and f.endswith(".dat"):
                force_file = os.path.join(root, f); break
    
    if force_file:
        try:
            it, fz = [], []
            with open(force_file, 'r') as f:
                for line in f:
                    if line.startswith('#') or not line.strip(): continue
                    p = line.replace('(', ' ').replace(')', ' ').replace(',', ' ').split()
                    if len(p) > 6:
                        it.append(int(p[0]))
                        fz.append(abs(float(p[3]) + float(p[6])))
            
            plt.figure(figsize=(8, 4))
            plt.plot(it, fz, color='blue', linewidth=2, label='Total Force (Z)')
            plt.title(f"Force Convergence - {vaka_adi}")
            plt.xlabel("Iteration"); plt.ylabel("Force [N]"); plt.grid(True)
            plt.savefig(os.path.join(kayit_yolu, "Kuvvet_Grafigi.png"))
            plt.close()
            print(f"   -> Grafik Kaydedildi: {vaka_adi}")
        except Exception as e:
            print(f"   -> Grafik Hatasi: {e}")

def final_tablosu_yap(sonuclar, cikis_yolu):
    if not sonuclar: return
    headers = ["Aciklik%", "Hiz(m/s)", "Kuvvet(N)"]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.axis('off')
    tbl = ax.table(cellText=sonuclar, colLabels=headers, loc='center', cellLoc='center')
    tbl.auto_set_font_size(False); tbl.set_fontsize(12); tbl.scale(1.2, 2)
    plt.title("VALF ANALIZI FINAL SONUCLARI", pad=20, fontweight='bold')
    plt.savefig(os.path.join(cikis_yolu, "Final_Sonuc_Tablosu.png"), bbox_inches='tight', dpi=150)
    plt.close()
    print("\n--- FINAL TABLOSU OLUSTURULDU ---")

# ============================================================
# --- 2. ANA DÖNGÜ ---
# ============================================================
if not os.path.exists(OUTPUT_BASE): os.makedirs(OUTPUT_BASE)
doc = FreeCAD.openDocument(FC_DOSYA_YOLU)

analiz_listesi = []
with open(GIRDI_DOSYASI, mode='r') as f:
    reader = csv.reader(f)
    next(reader)
    for row in reader:
        if row: analiz_listesi.append((int(row[0]), float(row[1])))

all_results = []
run_env = CfdTools.getRunEnvironment()

for counter, (op, vel) in enumerate(analiz_listesi, 1):
    case_name = f"Open_{op}_Vel_{vel}"
    subfolder = os.path.join(OUTPUT_BASE, case_name)
    if not os.path.exists(subfolder): os.makedirs(subfolder)
    
    print(f"\n[{counter}/9] ISLENIYOR: %{op} - {vel} m/s")

    doc.Spreadsheet.set('B1', f"{vel} m/s")
    doc.Spreadsheet.set('B2', str(op))
    doc.recompute()
    doc.CfdAnalysis.OutputPath = subfolder
    
    # Meshleme
    cart_mesh = CfdMeshTools.CfdMeshTools(doc.Cut_Mesh)
    cart_mesh.mesh_case_dir = os.path.join(subfolder, "meshCase")
    if not os.path.exists(cart_mesh.mesh_case_dir): os.makedirs(cart_mesh.mesh_case_dir)
    cart_mesh.writeMesh()
    m_p = CfdConsoleProcess.CfdConsoleProcess()
    m_p.start(CfdTools.makeRunCommand('Allmesh.bat', source_env=False), env_vars=run_env, working_dir=cart_mesh.mesh_case_dir)
    m_p.waitForFinished()
    
    # Solver
    doc.CfdSolver.Proxy.case_writer = CfdCaseWriterFoam.CfdCaseWriterFoam(doc.CfdAnalysis)
    doc.CfdSolver.Proxy.case_writer.writeCase()
    solver_dir = os.path.abspath(os.path.join(CfdTools.getOutputPath(doc.CfdAnalysis), doc.CfdSolver.InputCaseName))
    
    s_run = CfdRunnableFoam.CfdRunnableFoam(doc.CfdAnalysis, doc.CfdSolver)
    cmd_s = s_run.getSolverCmd(solver_dir)
    if cmd_s:
        s_proc = CfdConsoleProcess.CfdConsoleProcess()
        s_proc.start(cmd_s, env_vars=run_env, working_dir=solver_dir)
        s_proc.waitForFinished()

    # Grafik ve Veri Toplama
    grafik_ciz(solver_dir, subfolder, case_name)
    f_z = oku_kuvvet(solver_dir)
    all_results.append([op, vel, round(f_z, 2)])
    print(f"   -> Kuvvet: {round(f_z, 2)} N")

# TÜM ANALİZLER BİTİNCE TABLOYU OLUSTURMA
final_tablosu_yap(all_results, OUTPUT_BASE)
print("\n Klasörü kontrol et: " + OUTPUT_BASE)