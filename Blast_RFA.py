# =============================================================================
# Blast_RFA(발파암 파쇄입도 예측 프로그램) v1.0 
# Copyright © 2025-present JY EnC Corp. All rights reserved.
# =============================================================================

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import math
import pandas as pd
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

# --- 0. 전역 변수 및 설정 ---
graph_settings = {'xmin': 0.1, 'xmax': 1000}
comparison_data = []
last_result = {}

# --- 1. 계산 보조 함수 ---
def parse_value_from_string(selection, key):
    if not selection: return None
    try:
        value_str = selection.split(f'{key}=')[1].split(')')[0]
        return float(value_str)
    except (IndexError, ValueError):
        try: 
            value_str = selection.split(f'{key}: ')[1].replace(')', '')
            return float(value_str)
        except (IndexError, ValueError): return None

# --- 2. GUI 이벤트 처리 함수 ---
def on_rmd_type_change(event):
    selection = rmd_type_combo.get()
    ucd_frame.grid_remove(); joint_frame.grid_remove()
    if selection == "거대 암반 (Massive)": ucd_frame.grid()
    elif selection == "절리 암반 (Jointed)": ucd_frame.grid(); joint_frame.grid()

def show_rws_help():
    title = "도움말: 폭약 위력 계수 (RWS)"
    message = (
        "ANFO 폭약을 100으로 기준했을 때, 다른 폭약의 상대적인 파괴력을 나타내는 계수입니다.\n\n"
        "일반적인 값 예시:\n"
        "  - ANFO: 100\n"
        "  - 에멀젼 폭약 (Emulsion): 110 ~ 130\n"
        "  - 다이너마이트 (Dynamite): 120 ~ 150\n"
        "  - 슬러리 폭약 (Slurry): 100 ~ 120"
    )
    messagebox.showinfo(title, message)

def show_cp_help():
    title = "도움말: 암반의 종파속도 (P-wave Velocity)"
    message = (
        "암반의 종류와 상태(풍화, 균열)에 따라 달라지는 값입니다.\n\n"
        "일반적인 값 예시 (단위: km/s):\n"
        "  - 화강암 (신선): 4.5 ~ 5.5\n"
        "  - 화강암 (풍화): 2.0 ~ 4.0\n"
        "  - 석회암 (신선): 4.0 ~ 6.0\n"
        "  - 석회암 (풍화): 2.0 ~ 3.5\n"
        "  - 사암 (신선): 2.5 ~ 4.5\n\n"
        "정확한 값은 현장 탄성파 탐사 자료를 참고하세요."
    )
    messagebox.showinfo(title, message)
    
def open_graph_settings():
    settings_win = tk.Toplevel(window); settings_win.title("그래프 설정"); settings_win.geometry("300x150")
    settings_win.transient(window)
    tk.Label(settings_win, text="X축 최소 (cm):").pack(pady=5); xmin_entry = tk.Entry(settings_win); xmin_entry.pack()
    if graph_settings['xmin']: xmin_entry.insert(0, str(graph_settings['xmin']))
    tk.Label(settings_win, text="X축 최대 (cm):").pack(pady=5); xmax_entry = tk.Entry(settings_win); xmax_entry.pack()
    if graph_settings['xmax']: xmax_entry.insert(0, str(graph_settings['xmax']))
    def apply_settings():
        try:
            graph_settings['xmin'] = float(xmin_entry.get()) if xmin_entry.get() else None
            graph_settings['xmax'] = float(xmax_entry.get()) if xmax_entry.get() else None
            settings_win.destroy()
            if last_result: plot_distribution(last_result['x50'], last_result['n'])
            update_comparison_graph()
        except ValueError: messagebox.showerror("입력 오류", "유효한 숫자를 입력하세요.", parent=settings_win)
    tk.Button(settings_win, text="적용", command=apply_settings).pack(pady=10)

def toggle_timing_inputs():
    if timing_var.get(): timing_frame.grid()
    else: timing_frame.grid_remove()

# --- 3. 핵심 기능 함수 ---
def plot_distribution(x50_mm, n):
    ax1.clear()
    if n <= 0: n = 0.5 
    x50_cm = x50_mm / 10.0; Xc_cm = x50_cm / (math.log(2)**(1/n))
    xmin = graph_settings['xmin'] or 0.1; xmax = graph_settings['xmax'] or 1000
    x = np.logspace(np.log10(xmin), np.log10(xmax), 400); y = 100 * (1 - np.exp(-(x / Xc_cm)**n))
    ax1.plot(x, y, color='b'); ax1.set_xscale('log'); ax1.set_title("Fragmentation Curve")
    ax1.set_xlabel("Partial Size (cm)"); ax1.set_ylabel("Passing (%)"); ax1.grid(True, which='both', linestyle='--')
    p80_cm = Xc_cm * ((-math.log(1-0.8))**(1/n)); p20_cm = Xc_cm * ((-math.log(1-0.2))**(1/n))
    ax1.plot([p80_cm, p80_cm], [0, 80], 'r--'); ax1.plot([p80_cm, xmin], [80, 80], 'r--')
    ax1.plot([x50_cm, x50_cm], [0, 50], 'g--'); ax1.plot([x50_cm, xmin], [50, 50], 'g--')
    ax1.plot([p20_cm, p20_cm], [0, 20], 'k--'); ax1.plot([p20_cm, xmin], [20, 20], 'k--')
    ax1.set_xlim(xmin, xmax); ax1.set_ylim(0, 105); canvas1.draw()

def add_to_comparison():
    if not last_result: messagebox.showwarning("추가 오류", "먼저 계산을 실행하세요."); return
    legend_name = simpledialog.askstring("범례 이름", "비교 그래프에 표시될 범례 이름을 입력하세요:", parent=window)
    if not legend_name: return
    data = last_result['data']
    details = f"A={data['암석계수(A)']}, Q={data['장약량(Q)']}, B={data['버든(B)']}, RWS={data['폭약위력계수']}, d={data['천공경(d)']}"
    comparison_data.append({'legend': legend_name, 'details': details, 'x50': last_result['x50'], 'n': last_result['n']})
    update_comparison_list(); update_comparison_graph(); right_notebook.select(comparison_tab)

def update_comparison_list():
    for i in comparison_tree.get_children(): comparison_tree.delete(i)
    for i, item in enumerate(comparison_data):
        comparison_tree.insert("", "end", iid=i, text=item['legend'], values=(item['details'],))

def remove_from_comparison():
    for item_id in reversed(comparison_tree.selection()): del comparison_data[int(item_id)]
    update_comparison_list(); update_comparison_graph()

def clear_comparison():
    comparison_data.clear(); update_comparison_list(); update_comparison_graph()

def update_comparison_graph():
    ax2.clear(); colors = ['b', 'g', 'r', 'c', 'm', 'y', 'k']; linestyles = ['-', '--', '-.', ':']
    xmin = graph_settings['xmin'] or 0.1; xmax = graph_settings['xmax'] or 1000
    for i, data in enumerate(comparison_data):
        x50_mm, n = data['x50'], data['n']
        if n <= 0: n = 0.5
        x50_cm = x50_mm / 10.0; Xc_cm = x50_cm / (math.log(2)**(1/n))
        x = np.logspace(np.log10(xmin), np.log10(xmax), 400); y = 100 * (1 - np.exp(-(x / Xc_cm)**n))
        ax2.plot(x, y, color=colors[i % len(colors)], linestyle=linestyles[i % len(linestyles)], label=data['legend'])
    ax2.set_xscale('log'); ax2.set_title("Comparison of Curves"); ax2.set_xlabel("Partial Size (cm)"); ax2.set_ylabel("Passing (%)")
    ax2.grid(True, which='both', linestyle='--'); ax2.set_xlim(xmin, xmax); ax2.set_ylim(0, 105)
    if comparison_data: ax2.legend();
    canvas2.draw()

def save_data(is_graph=False, is_comparison_graph=False):
    if not last_result and not (is_graph or is_comparison_graph): messagebox.showwarning("저장 오류", "먼저 계산을 실행하세요."); return
    if is_comparison_graph and not comparison_data: messagebox.showwarning("저장 오류", "비교할 데이터가 없습니다."); return
    try:
        if is_graph or is_comparison_graph:
            fig_to_save = fig2 if is_comparison_graph else fig1
            file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png"), ("JPG", "*.jpg")], title="그래프 저장")
            if file_path: fig_to_save.savefig(file_path, dpi=300, bbox_inches='tight')
        else:
            file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")], title="결과 저장")
            if file_path:
                pd.concat([pd.DataFrame([last_result['data']]), pd.DataFrame(last_result['graph_data'])], axis=1).to_csv(file_path, index=False, encoding='utf-8-sig')
        if file_path: messagebox.showinfo("저장 완료", f"파일이 저장되었습니다:\n{file_path}")
    except Exception as e: messagebox.showerror("저장 실패", f"파일 저장 중 오류 발생: {e}")

def calculate_fragmentation():
    try:
        for label in precise_result_labels.values(): label.config(text="")
        
        selected_tab_index = notebook.index(notebook.select()); rock_factor_A, method_description = 0, ""
        timing_factor_At = 1.0
        
        if selected_tab_index == 0: method_description = "방법 1: 간편 분류"; rock_factor_A = parse_value_from_string(simple_mode_combo.get(), ', A')
        elif selected_tab_index == 1: method_description = "방법 2: RMR 점수"; rock_factor_A = parse_value_from_string(rmr_combo.get(), ', A')
        elif selected_tab_index == 2: method_description = "방법 3: 종합 점수"; rock_factor_A = sum(parse_value_from_string(s, '(점수') for s in [rating_combos[k].get() for k in rating_combos])
        elif selected_tab_index == 3:
            method_description = "방법 4: 정밀 계산"; rmd_type = rmd_type_combo.get()
            if not rmd_type: messagebox.showerror("입력 오류", "암반 종류를 선택하세요."); return
            density = float(precise_entries['density'].get()); rdi = 25 * density - 50; rmd, hf = 0, 0
            if rmd_type == "가루/푸석한 암반 (Friable)": rmd, hf = 10, 0; precise_result_labels['rmd_result'].config(text=f"▶ RMD=10, HF=0")
            elif rmd_type == "거대 암반 (Massive)": ucd = float(precise_entries['ucd'].get()); rmd, hf = ucd/5, ucd/5; precise_result_labels['rmd_result'].config(text=f"▶ RMD=UCS/5={rmd:.2f}"); precise_result_labels['hf_result'].config(text=f"▶ HF=UCS/5={hf:.2f}")
            elif rmd_type == "절리 암반 (Jointed)":
                ucd = float(precise_entries['ucd'].get()); jcf = parse_value_from_string(precise_combos['jcf'].get(), '(JCF'); jps = parse_value_from_string(precise_combos['jps'].get(), '(JPS'); jpa = parse_value_from_string(precise_combos['jpa'].get(), '(JPA')
                if None in [jcf, jps, jpa]: messagebox.showerror("입력 오류", "절리 항목을 선택하세요."); return
                rmd = jcf + jps + jpa; hf = ucd/5; precise_result_labels['rmd_result'].config(text=f"▶ RMD=JCF+JPS+JPA={rmd:.2f}"); precise_result_labels['hf_result'].config(text=f"▶ HF=UCS/5={hf:.2f}")
            precise_result_labels['rdi_result'].config(text=f"▶ RDI=25*SG-50={rdi:.2f}"); rock_factor_A = 0.06 * (rmd + rdi + hf)
        elif selected_tab_index == 4: method_description = "방법 5: 수동 입력"; rock_factor_A = float(manual_A_entry.get())
        
        Q = float(entry_Q.get()); S_anfo = float(entry_S_anfo.get()); B = float(entry_B.get()); S = float(entry_S.get()); d = float(entry_d.get()); H = float(entry_H.get())
        
        if selected_tab_index == 3 and timing_var.get():
            T = float(precise_entries['T'].get()); Cp = float(precise_entries['Cp'].get())
            if Cp <= 0: messagebox.showerror("입력 오류", "종파속도(Cp)는 0보다 커야 합니다."); return
            T_max = (15.6 / Cp) * B; T_ratio = T / T_max
            if 0 < T_ratio < 1: timing_factor_At = 0.66 * (T_ratio**3) - 0.13 * (T_ratio**2) - 1.58 * T_ratio + 2.1
            elif T_ratio >= 1: timing_factor_At = 0.9 + 0.1 * (T_ratio - 1)
            precise_result_labels['At_result'].config(text=f"▶ At={timing_factor_At:.2f}")

        q = Q / (B*S*H); x50_cm = rock_factor_A * timing_factor_At * (q**-0.8) * (Q**(1/6)) * ((115/S_anfo)**0.635)
        
        x50_mm = x50_cm * 10; n = (2.2 - 14 * (B/d)) * math.sqrt((1 + S/B)/2)
        if n <= 0: messagebox.showwarning("계산 경고", "균등 지수(n)가 0 이하입니다.")
        
        plot_distribution(x50_mm, n)
        
        Xc = x50_mm / (math.log(2)**(1/n)) if n > 0 else x50_mm
        p80_mm = Xc * ((-math.log(1 - 0.8))**(1/n)) if n > 0 else x50_mm; p50_mm = x50_mm; p20_mm = Xc * ((-math.log(1 - 0.2))**(1/n)) if n > 0 else x50_mm
        
        # ✨✨✨ 결과 출력창 업데이트 로직 수정 ✨✨✨
        result_text.config(state=tk.NORMAL)
        result_text.delete('1.0', tk.END)
        result_text.insert(tk.END, f"--- 계산 조건 ({method_description}) ---\n"
                                   f"적용된 암석 계수 (A): {rock_factor_A:.2f}\n"
                                   f"적용된 시간 계수 (At): {timing_factor_At:.2f}\n\n"
                                   "--- 계산 결과 ---\n"
                                   f"비장약량 (q): {q:.3f} kg/m³\n"
                                   f"평균 입도 (X50): {p50_mm:.2f} mm\n"
                                   f"균등 지수 (n): {n:.2f}\n\n"
                                   "--- 예상 입도 분포 ---\n"
                                   f"80% 통과 입도 (P80): {p80_mm:.2f} mm\n"
                                   f"50% 통과 입도 (P50): {p50_mm:.2f} mm\n"
                                   f"20% 통과 입도 (P20): {p20_mm:.2f} mm\n")
        
        graph_data_for_saving = {"Passing(%)": [], "Partial Size(cm)": []}
        if n > 0:
            Xc_cm = (x50_mm / 10.0) / (math.log(2)**(1/n))
            result_text.insert(tk.END, "\n--- 그래프 데이터 ---\n"); result_text.insert(tk.END, "Partial Size(cm) | Passing(%)\n"); result_text.insert(tk.END, "-"*28 + "\n")
            for y_percent in range(1, 100):
                x_cm = Xc_cm * ((-math.log(1 - y_percent/100))**(1/n))
                result_text.insert(tk.END, f"{x_cm:<17.3f} | {y_percent}\n")
                graph_data_for_saving["Passing(%)"].append(y_percent); graph_data_for_saving["Partial Size(cm)"].append(f"{x_cm:.3f}")
        
        result_text.config(state=tk.DISABLED)
        
        last_result.clear()
        last_result['x50'] = x50_mm
        last_result['n'] = n
        last_result['graph_data'] = graph_data_for_saving # 저장용 데이터에 그래프 데이터 추가
        last_result['data'] = {"계산방식": method_description, "암석계수(A)": f"{rock_factor_A:.2f}", "시간계수(At)":f"{timing_factor_At:.2f}", "장약량(Q)": Q, "폭약위력계수": S_anfo, "버든(B)": B, "스페이싱(S)": S, "천공경(d)": d, "벤치높이(H)": H, "비장약량(q)": f"{q:.3f}", "평균입도(X50)": f"{x50_mm:.2f}", "균등지수(n)": f"{n:.2f}", "P80": f"{p80_mm:.2f}", "P20": f"{p20_mm:.2f}"}
        add_to_comparison_button.config(state=tk.NORMAL)

    except (ValueError, TypeError): messagebox.showerror("입력 오류", "모든 필드에 유효한 값을 입력/선택하세요.")
    except Exception as e: messagebox.showerror("계산 오류", f"오류가 발생했습니다: {e}")

# --- 5. GUI 설정 ---
window = tk.Tk(); window.title("Blast_RFA (Kuz-Ram 모델 기반 파쇄입도 예측) v1.0"); window.geometry("1470x820")
# ... (이하 GUI 레이아웃 코드는 이전과 동일) ...
main_frame = tk.Frame(window); main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
left_frame = tk.Frame(main_frame, width=550); left_frame.pack(side=tk.LEFT, fill=tk.Y); left_frame.pack_propagate(False)
right_notebook = ttk.Notebook(main_frame); right_notebook.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
single_result_tab = ttk.Frame(right_notebook); comparison_tab = ttk.Frame(right_notebook)
right_notebook.add(single_result_tab, text=" 현재 결과 그래프 "); right_notebook.add(comparison_tab, text=" 결과 비교 ")
program_title_label = tk.Label(left_frame, text="발파암 파쇄입도 예측 프로그램", font=("Helvetica", 16, "bold")); program_title_label.pack(pady=(0, 10))
rock_factor_label = tk.Label(left_frame, text="암석특성 입력 (방법 1~5)", font=("Helvetica", 12)); rock_factor_label.pack(pady=(0, 5))
tab_frame=tk.Frame(left_frame);tab_frame.pack(fill="x");notebook=ttk.Notebook(tab_frame);notebook.pack(fill="x");tabs=[ttk.Frame(notebook,padding=10) for _ in range(5)];tab_names=["방법 1: 간편 분류","방법 2: RMR 점수","방법 3: 종합 점수","방법 4: 정밀 계산","방법 5: 수동 입력"];
for tab,name in zip(tabs,tab_names):notebook.add(tab,text=f" {name} ");tab1,tab2,tab3,tab4,tab5=tabs
simple_mode_options = ["풍화암 (f=3~5, A=3.0)", "연암 (f=5~8, A=5.0)", "보통암 (f=8~10, A=7.0)", "균열이 있는 경암 (f=10~14, A=10.0)", "매우 균질한 경암 (f=12~16, A=13.0)"]
simple_mode_combo = ttk.Combobox(tab1, values=simple_mode_options, state="readonly", width=45); simple_mode_combo.pack()
rmr_options = ["Very Good Rock (RMR 81-100, A=13.0)", "Good Rock (RMR 61-80, A=12.0)", "Fair Rock (RMR 41-60, A=10.0)", "Poor Rock (RMR 21-40, A=8.0)", "Very Poor Rock (RMR 0-20, A=7.0)"]
rmr_combo = ttk.Combobox(tab2, values=rmr_options, state="readonly", width=45); rmr_combo.pack()
manual_A_entry = tk.Entry(tab5); manual_A_entry.pack()
rating_frame = tk.Frame(tab3); rating_frame.pack(); rating_combos = {}
rating_info = { "r1": ("1. 강도 (R1):", ["UCS < 75 MPa (점수: 1)", "UCS 75-150 MPa (점수: 2)", "UCS 150-225 MPa (점수: 3)", "UCS > 225 MPa (점수: 4)"]), "r2": ("2. 구조 (R2, 절리간격):", ["> 3 m (점수: 1)", "1 - 3 m (점수: 2)", "0.3 - 1 m (점수: 3)", "0.1 - 0.3 m (점수: 4)", "< 0.1 m (점수: 5)"]), "r3": ("3. 방향 (R3):", ["자유면과 평행하게 경사 (점수: 1)", "수평 (점수: 2)", "자유면 방향으로 경사 (점수: 3)", "수직 (점수: 4)"]), "r4": ("4. 밀도 (R4):", ["< 2.3 t/m³ (점수: 1)", "2.3 - 2.6 t/m³ (점수: 2)", "> 2.6 t/m³ (점수: 3)"])};
for i,(key,(text,opts)) in enumerate(rating_info.items()): tk.Label(rating_frame,text=text).grid(row=i,column=0,sticky='w'); combo = ttk.Combobox(rating_frame,values=opts,state="readonly",width=30); combo.grid(row=i,column=1,pady=2); rating_combos[key] = combo
ttk.Separator(rating_frame, orient='horizontal').grid(row=4, columnspan=2, sticky='ew', pady=10); tk.Label(rating_frame,text="A = R1+R2+R3+R4").grid(row=5,columnspan=2)
precise_frame = tk.Frame(tab4); precise_frame.pack(); tk.Label(precise_frame,text="1. 암반 종류:").grid(row=0,column=0,sticky='w'); rmd_type_combo = ttk.Combobox(precise_frame,values=["가루/푸석한 암반 (Friable)","거대 암반 (Massive)","절리 암반 (Jointed)"],state="readonly",width=25); rmd_type_combo.grid(row=0,column=1,sticky='w'); rmd_type_combo.bind("<<ComboboxSelected>>",on_rmd_type_change)
precise_entries,precise_combos,precise_result_labels={},{},{}; 
tk.Label(precise_frame,text="2. 밀도 (g/cc):").grid(row=1,column=0,sticky='w'); precise_entries['density']=tk.Entry(precise_frame,width=10); precise_entries['density'].grid(row=1,column=1,sticky='w'); precise_result_labels['rdi_result']=tk.Label(precise_frame,fg='blue'); precise_result_labels['rdi_result'].grid(row=1,column=2,sticky='w')
ucd_frame = tk.Frame(precise_frame); ucd_frame.grid(row=2,column=0,columnspan=3,sticky='w'); tk.Label(ucd_frame,text="3. UCS (MPa):").grid(row=0,column=0,sticky='w'); precise_entries['ucd']=tk.Entry(ucd_frame,width=10); precise_entries['ucd'].grid(row=0,column=1,sticky='w'); precise_result_labels['hf_result']=tk.Label(ucd_frame,fg='blue'); precise_result_labels['hf_result'].grid(row=0,column=2,sticky='w')
joint_frame = tk.Frame(precise_frame); joint_frame.grid(row=3,column=0,columnspan=3,sticky='w'); joint_info = { "jcf": ("  - JCF (상태):", ["Tight Joints (JCF: 1.0)", "Relaxed Joints (JCF: 1.5)", "Gouge-filled (JCF: 2.0)"]), "jps": ("  - JPS (간격):", ["Spacing < 0.1m (JPS: 10)", "Spacing 0.1-0.3m (JPS: 20)", "Spacing > 0.3m (JPS: 80)"]), "jpa": ("  - JPA (방향):", ["Dip into face (JPA: 20)", "Strike parallel (JPA: 30)", "Dip out of face (JPA: 40)"])};
for i,(key,(text,opts)) in enumerate(joint_info.items()): tk.Label(joint_frame,text=text).grid(row=i,column=0,sticky='w'); combo = ttk.Combobox(joint_frame,values=opts,state="readonly",width=25); combo.grid(row=i,column=1,sticky='w'); precise_combos[key] = combo
precise_result_labels['rmd_result']=tk.Label(precise_frame,fg='blue'); precise_result_labels['rmd_result'].grid(row=4,columnspan=3,sticky='w')
ucd_frame.grid_remove(); joint_frame.grid_remove(); 
ttk.Separator(precise_frame, orient='horizontal').grid(row=5, columnspan=3, sticky='ew', pady=5)
timing_var = tk.BooleanVar(); timing_check = tk.Checkbutton(precise_frame, text="지연 시간 고려", variable=timing_var, command=toggle_timing_inputs); timing_check.grid(row=6, column=0, sticky='w')
timing_frame = tk.Frame(precise_frame); timing_frame.grid(row=7,column=0,columnspan=3,sticky='w')
cp_label_frame = tk.Frame(timing_frame); cp_label_frame.grid(row=1, column=0, sticky='w')
tk.Label(cp_label_frame, text="  - Cp (km/s):").pack(side=tk.LEFT)
tk.Button(cp_label_frame, text="?", command=show_cp_help, font=('Helvetica', 8, 'bold'), width=2).pack(side=tk.LEFT, padx=2)
precise_entries['T']=tk.Entry(timing_frame,width=10); precise_entries['T'].grid(row=0,column=1,sticky='w')
tk.Label(timing_frame, text="  - T (ms):").grid(row=0, column=0, sticky='w')
precise_entries['Cp']=tk.Entry(timing_frame,width=10); precise_entries['Cp'].grid(row=1,column=1,sticky='w')
precise_result_labels['At_result']=tk.Label(timing_frame,fg='blue'); precise_result_labels['At_result'].grid(row=0,column=2,rowspan=2,sticky='w',padx=5)
timing_frame.grid_remove()
ttk.Separator(precise_frame, orient='horizontal').grid(row=8, columnspan=3, sticky='ew', pady=10); tk.Label(precise_frame,text="A' = A * At").grid(row=9,columnspan=3)
common_frame_container = tk.LabelFrame(left_frame,text="공통 발파 설계 변수",padx=10,pady=10); common_frame_container.pack(fill="x",padx=10,pady=5)
common_params_info = [("공당 장약량 (Q) [kg]:",'Q'),("폭약 위력 계수 (RWS)",'S_anfo'),("버든 (B) [m]:",'B'),("스페이싱 (S) [m]:",'S'),("천공 직경 (d) [mm]:",'d'),("벤치 높이 (H) [m]:",'H')]; entry_widgets = {};
for i,(text,key) in enumerate(common_params_info):
    row,col=i%3,(i//3)*2; label_frame=tk.Frame(common_frame_container); label_frame.grid(row=row,column=col,sticky='w')
    tk.Label(label_frame,text=text).pack(side='left');
    if key=='S_anfo': tk.Button(label_frame,text="?",command=show_rws_help,width=2).pack(side='left', padx=2)
    entry=tk.Entry(common_frame_container,width=10); entry.grid(row=row,column=col+1,sticky='w'); entry_widgets[key]=entry
entry_Q,entry_S_anfo,entry_B,entry_S,entry_d,entry_H=[entry_widgets[k] for k in ['Q','S_anfo','B','S','d','H']]

left_button_frame=tk.Frame(left_frame);left_button_frame.pack(pady=10)
tk.Button(left_button_frame,text="결과 계산",command=calculate_fragmentation,font=('',14,'bold'),bg='lightblue').pack(side=tk.LEFT,padx=5)
tk.Button(left_button_frame, text="결과 저장", command=lambda: save_data(is_graph=False), font=('', 14, 'bold')).pack(side=tk.LEFT, padx=5)
add_to_comparison_button=tk.Button(left_button_frame,text="비교 리스트에 추가",command=add_to_comparison,font=('',14,'bold'),state=tk.DISABLED);add_to_comparison_button.pack(side=tk.LEFT,padx=5)
result_frame=tk.LabelFrame(left_frame,text="계산 결과");result_frame.pack(fill="both",expand=True,padx=10,pady=5)
result_text=tk.Text(result_frame,bg='#f0f0f0',font=('Courier',10),height=10); result_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
result_scrollbar = ttk.Scrollbar(result_frame, orient='vertical', command=result_text.yview); result_scrollbar.pack(side=tk.RIGHT, fill='y')
result_text['yscrollcommand'] = result_scrollbar.set

# 5.2. 오른쪽 프레임 구성
graph_button_frame_single=tk.Frame(single_result_tab);graph_button_frame_single.pack(fill=tk.X,pady=5)
tk.Button(graph_button_frame_single,text="그래프 저장",command=lambda:save_data(True),font=('',12,'bold')).pack(side=tk.RIGHT,padx=5)
tk.Button(graph_button_frame_single,text="그래프 설정",command=open_graph_settings,font=('',12,'bold')).pack(side=tk.RIGHT,padx=5)
fig1=Figure(figsize=(8,7),dpi=100);ax1=fig1.add_subplot(111);canvas1=FigureCanvasTkAgg(fig1,master=single_result_tab);canvas1.get_tk_widget().pack(fill=tk.BOTH,expand=True)
comparison_top_frame=tk.Frame(comparison_tab);comparison_top_frame.pack(fill=tk.X,pady=5)
tk.Button(comparison_top_frame,text="선택 항목 삭제",command=remove_from_comparison).pack(side=tk.LEFT,padx=5)
tk.Button(comparison_top_frame,text="전체 삭제",command=clear_comparison).pack(side=tk.LEFT,padx=5)
tk.Button(comparison_top_frame,text="비교 그래프 저장",command=lambda: save_data(is_comparison_graph=True), font=('',12,'bold')).pack(side=tk.RIGHT,padx=5)
tk.Button(comparison_top_frame,text="그래프 설정",command=open_graph_settings,font=('',12,'bold')).pack(side=tk.RIGHT,padx=5)
comparison_list_frame=tk.Frame(comparison_tab);comparison_list_frame.pack(fill=tk.X,pady=5)
comparison_tree=ttk.Treeview(comparison_list_frame,columns=("details"),show="tree headings", height=3);comparison_tree.heading("#0",text="범례 이름");comparison_tree.column("#0",width=120);comparison_tree.heading("details",text="세부 조건");comparison_tree.pack(side=tk.LEFT,fill=tk.BOTH,expand=True)
scrollbar=ttk.Scrollbar(comparison_list_frame,orient="vertical",command=comparison_tree.yview);scrollbar.pack(side='right',fill='y');comparison_tree.configure(yscrollcommand=scrollbar.set)
comparison_graph_frame=tk.Frame(comparison_tab);comparison_graph_frame.pack(fill=tk.BOTH,expand=True,pady=5)
fig2=Figure(figsize=(8,5),dpi=100);ax2=fig2.add_subplot(111);canvas2=FigureCanvasTkAgg(fig2,master=comparison_graph_frame);canvas2.get_tk_widget().pack(fill=tk.BOTH,expand=True)

# 5.3. 저작권 라벨
copyright_label=tk.Label(window,text="Copyright © 2025-present JY EnC Corp. All rights reserved.",font=('Helvetica',8),fg='gray');copyright_label.pack(side=tk.BOTTOM,pady=5)

# --- 6. 프로그램 시작 ---
plot_distribution(1000.0, 1.5)
update_comparison_graph()
window.mainloop()