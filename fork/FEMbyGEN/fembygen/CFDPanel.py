import os, time, csv
import FreeCAD
import FreeCADGui
from PySide2 import QtWidgets, QtCore
import matplotlib.pyplot as plt

# ============================================================
# --- 1. AJANLAR VE FOTOĞRAFÇILAR (SADECE KUVVET İÇİN) ---
# ============================================================
def oku_kuvvet(solver_dizini):
    pp_dir = os.path.join(solver_dizini, "postProcessing")
    if not os.path.exists(pp_dir): return 0.0
    for root, dirs, files in os.walk(pp_dir):
        for f_name in files:
            full_path = os.path.join(root, f_name)
            if "force" in full_path.lower() and f_name.endswith(".dat"):
                try:
                    with open(full_path, 'r') as f:
                        lines = [s.strip() for s in f.readlines() if s.strip() and not s.startswith('#')]
                        if lines:
                            p = lines[-1].replace('(', ' ').replace(')', ' ').replace(',', ' ').split()
                            if len(p) > 6: return abs(float(p[3]) + float(p[6]))
                except: pass
    return 0.0

def grafik_olustur_ve_kaydet(solver_dizini, kayit_yolu, vaka_adi):
    pp_dir = os.path.join(solver_dizini, "postProcessing")
    force_file = None
    for root, dirs, files in os.walk(pp_dir):
        for f in files:
            if "force" in f.lower() and f.endswith(".dat") and "patch" not in root.lower():
                force_file = os.path.join(root, f)
                break
    if force_file:
        try:
            itler, fpx, fpy, fpz, fvx, fvy, fvz = [], [], [], [], [], [], []
            with open(force_file, 'r') as f:
                for line in f:
                    if line.startswith('#') or not line.strip(): continue
                    p = line.replace('(', ' ').replace(')', ' ').replace(',', ' ').split()
                    if len(p) > 6:
                        itler.append(int(p[0]))
                        fpx.append(float(p[1])); fpy.append(float(p[2])); fpz.append(float(p[3]))
                        fvx.append(float(p[4])); fvy.append(float(p[5])); fvz.append(float(p[6]))
            plt.figure(figsize=(10, 5))
            plt.plot(itler, fpx, label='Fx (pressure)', alpha=0.6); plt.plot(itler, fpy, label='Fy (pressure)', alpha=0.6)
            plt.plot(itler, fpz, label='Fz (pressure)', linewidth=2)
            plt.plot(itler, fvx, label='Fx (viscous)', linestyle='--'); plt.plot(itler, fvy, label='Fy (viscous)', linestyle='--')
            plt.plot(itler, fvz, label='Fz (viscous)', linestyle='--', linewidth=2)
            plt.title(f"Force Convergence - {vaka_adi}"); plt.xlabel("Iteration"); plt.ylabel("Force [N]")
            plt.legend(loc='upper right', fontsize='x-small', ncol=2); plt.grid(True, alpha=0.3)
            plt.savefig(os.path.join(kayit_yolu, "Kuvvet_Grafigi.png"), dpi=120); plt.close()
        except: pass

def tabloyu_png_yap(sonuclar, kayit_yolu):
    if not sonuclar: return
    headers = ["Aciklik%", "Hiz(m/s)", "P_In(Pa)", "P_Out(Pa)", "Force(N)"]
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.axis('off')
    tbl = ax.table(cellText=sonuclar, colLabels=headers, loc='center', cellLoc='center')
    tbl.auto_set_font_size(False); tbl.set_fontsize(10); tbl.scale(1.2, 1.8)
    plt.title("VALF ANALIZI KUVVET TABLOSU", pad=20, fontweight='bold')
    plt.savefig(os.path.join(kayit_yolu, "Yarim_Sonuc_Tablosu.png"), bbox_inches='tight', dpi=150); plt.close()

# ============================================================
# --- 2. ÇOKLU ARAYÜZ VE MOTOR ENTEGRASYONU ---
# ============================================================
class CFD_UI:
    def __init__(self):
        self.form = QtWidgets.QWidget()
        self.form.setWindowTitle("CFD Parametrik Otomasyon")
        self.layout = QtWidgets.QVBoxLayout(self.form)

        # --- ÇOKLU HIZ GİRİŞİ ---
        self.hiz_label = QtWidgets.QLabel("Hız Değerleri (m/s) [Virgülle ayırın]:")
        self.layout.addWidget(self.hiz_label)
        self.hiz_input = QtWidgets.QLineEdit("2, 3, 5") 
        self.layout.addWidget(self.hiz_input)

        # --- ÇOKLU AÇIKLIK ORANI GİRİŞİ ---
        self.aciklik_label = QtWidgets.QLabel("Açıklık Oranları (%) [Virgülle ayırın]:")
        self.layout.addWidget(self.aciklik_label)
        self.aciklik_input = QtWidgets.QLineEdit("30, 60, 90") 
        self.layout.addWidget(self.aciklik_input)

        self.layout.addSpacing(10)

        # --- BAŞLAT BUTONU ---
        self.btn_baslat = QtWidgets.QPushButton("🚀 Kombinasyonları Başlat")
        self.btn_baslat.setStyleSheet("background-color: #28a745; color: white; font-weight: bold; padding: 8px;")
        self.btn_baslat.clicked.connect(self.hesapla)
        self.layout.addWidget(self.btn_baslat)

    def hesapla(self):
        # Kullanıcının virgülle girdiği verileri Python Listesine çevirme
        try:
            velocities = [float(v.strip()) for v in self.hiz_input.text().split(',')]
            openings = [int(o.strip()) for o in self.aciklik_input.text().split(',')]
        except ValueError:
            FreeCAD.Console.PrintError("Lutfen degerleri sadece rakam ve virgül kullanarak girin!\n")
            return
            
        toplam_analiz = len(velocities) * len(openings)
        FreeCAD.Console.PrintMessage(f"\n--- {toplam_analiz} ADET CFD ANALIZI BASLIYOR ---\n")

        try:
            all_results = []
            output_base = "C:/SurguValf_Analizleri"
            if not os.path.exists(output_base): os.makedirs(output_base)
            csv_file = os.path.join(output_base, "Valf_Eksik_Rapor.csv")

            with open(csv_file, mode='w', newline='') as f:
                csv.writer(f).writerow(["Aciklik%", "Hiz(m/s)", "P_In(Pa)", "P_Out(Pa)", "Force(N)"])

            counter = 0
            # döngü
            for op in openings:
                for vel in velocities:
                    counter += 1
                    case_name = f"Open_{op}_Vel_{vel}"
                    subfolder = os.path.join(output_base, case_name)
                    if not os.path.exists(subfolder): os.makedirs(subfolder)
                    
                    FreeCAD.Console.PrintMessage(f"[{counter}/{toplam_analiz}] Isleniyor: Aciklik %{op}, Hiz {vel}m/s...\n")
                    QtCore.QCoreApplication.processEvents() # FREECAD'IN DONMASINI ENGELLEME
                    
                    # Parametreleri Güncelle (Spreadsheet)
                    FreeCAD.ActiveDocument.Spreadsheet.set('B1', f"{vel} m/s")
                    FreeCAD.ActiveDocument.Spreadsheet.set('B2', str(op))
                    FreeCAD.ActiveDocument.recompute()
                    QtCore.QCoreApplication.processEvents()

                    FreeCAD.ActiveDocument.CfdAnalysis.OutputPath = subfolder
                    
                    # Mesh İşlemleri
                    from CfdOF.Mesh import CfdMeshTools
                    from CfdOF import CfdTools, CfdConsoleProcess
                    cart_mesh = CfdMeshTools.CfdMeshTools(FreeCAD.ActiveDocument.Cut_Mesh)
                    cart_mesh.mesh_case_dir = os.path.join(subfolder, "meshCase")
                    if not os.path.exists(cart_mesh.mesh_case_dir): os.makedirs(cart_mesh.mesh_case_dir)
                    cart_mesh.writeMesh()
                    
                    env = CfdTools.getRunEnvironment()
                    m_p = CfdConsoleProcess.CfdConsoleProcess()
                    m_p.start(CfdTools.makeRunCommand('Allmesh.bat', source_env=False), env_vars=env, working_dir=cart_mesh.mesh_case_dir)
                    m_p.waitForFinished()
                    
                    # Çözücü (Solver) İşlemleri
                    from CfdOF.Solve import CfdCaseWriterFoam
                    FreeCAD.ActiveDocument.CfdSolver.Proxy.case_writer = CfdCaseWriterFoam.CfdCaseWriterFoam(FreeCAD.ActiveDocument.CfdAnalysis)
                    FreeCAD.ActiveDocument.CfdSolver.Proxy.case_writer.writeCase()
                    solver_dir = os.path.abspath(os.path.join(CfdTools.getOutputPath(FreeCAD.ActiveDocument.CfdAnalysis), FreeCAD.ActiveDocument.CfdSolver.InputCaseName))
                    
                    from CfdOF.Solve import CfdRunnableFoam
                    s_run = CfdRunnableFoam.CfdRunnableFoam(FreeCAD.ActiveDocument.CfdAnalysis, FreeCAD.ActiveDocument.CfdSolver)
                    cmd_s = s_run.getSolverCmd(solver_dir)
                    if cmd_s:
                        s_proc = CfdConsoleProcess.CfdConsoleProcess(stdout_hook=s_run.processOutput)
                        s_proc.start(cmd_s, env_vars=env, working_dir=solver_dir)
                        s_proc.waitForFinished()

                    # Ajanlar ve Fotoğrafçılar
                    grafik_olustur_ve_kaydet(solver_dir, subfolder, case_name)
                    f_z = oku_kuvvet(solver_dir)

                    row = [op, vel, "ParaView'dan Bak", "ParaView'dan Bak", round(f_z, 2)]
                    all_results.append(row)
                    
                    with open(csv_file, mode='a', newline='') as f: csv.writer(f).writerow(row)
                    
            # Bütün analizler bitince Toplu Tabloyu Görseli Hazırla
            tabloyu_png_yap(all_results, output_base)
            FreeCAD.Console.PrintMessage("\n" + "="*80 + "\n")
            FreeCAD.Console.PrintMessage(f"BUTUN KOMBİNASYONLAR BİTTİ! Sonuclar C:/SurguValf_Analizleri klasorunde.\n")
            FreeCAD.Console.PrintMessage("="*80 + "\n")

        except Exception as e:
            FreeCAD.Console.PrintError(f"\n!!! HATA OLUSTU: {str(e)} !!!\n")