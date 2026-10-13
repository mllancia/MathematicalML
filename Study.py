#!/usr/bin/env python3
"""
Study Time Tracker 2026
Desktop application to track study time by subject with daily progress charts
Data is automatically saved to ~/.study_tracker_data.json
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.dates as mdates
import time
import threading

class StudyTimeTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("Study Time Tracker 2026")
        self.root.geometry("1200x900")
        self.root.configure(bg='#f0f4f8')
        
        # Data file path
        self.data_file = os.path.join(os.path.expanduser("~"), ".study_tracker_data.json")
        
        # Initialize variables
        self.subjects = {}
        self.daily_data = {}  # Format: {"YYYY-MM-DD": {"subject": seconds}}
        self.current_subject = tk.StringVar()
        self.chart_view = tk.StringVar(value="total")
        self.selected_subject_view = tk.StringVar()
        self.is_running = False
        self.elapsed_time = 0
        self.timer_thread = None
        
        # Load saved data
        self.load_data()
        
        # Create GUI
        self.create_widgets()
        
        # Update display
        self.update_time_display()
        self.update_charts()
        
        print(f"📁 Data file location: {self.data_file}")
        
    def load_data(self):
        """Load saved study data from file"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.subjects = data.get('subjects', {})
                    self.daily_data = data.get('daily_data', {})
                print(f"✓ Data loaded: {len(self.subjects)} subjects found")
                print(f"✓ Days tracked: {len(self.daily_data)}")
                print(f"✓ Total study time: {sum(self.subjects.values())/3600:.1f} hours")
            else:
                print("No saved data found, starting fresh")
        except Exception as e:
            print(f"Error loading data: {e}")
            self.subjects = {}
            self.daily_data = {}
    
    def save_data(self):
        """Save study data to file"""
        try:
            data = {
                'subjects': self.subjects,
                'daily_data': self.daily_data
            }
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"✓ Data saved: {self.data_file}")
        except Exception as e:
            print(f"Error saving data: {e}")
            messagebox.showerror("Error", f"Failed to save data: {e}")
    
    def clear_all_data(self):
        """Clear all data (useful for new year)"""
        result = messagebox.askyesnocancel(
            "Clear All Data", 
            "This will delete ALL study data permanently!\n\n"
            "Are you sure you want to continue?\n\n"
            "💡 Tip: Consider backing up your data first."
        )
        
        if result:
            # Double confirmation
            confirm = messagebox.askokcancel(
                "Final Confirmation",
                "⚠️ FINAL WARNING ⚠️\n\n"
                "All subjects and study time will be deleted!\n\n"
                "Click OK to DELETE ALL DATA"
            )
            
            if confirm:
                self.subjects = {}
                self.daily_data = {}
                self.current_subject.set('')
                self.selected_subject_view.set('')
                self.elapsed_time = 0
                self.save_data()
                self.subject_combo['values'] = []
                self.subject_view_combo['values'] = []
                self.update_charts()
                self.update_stats()
                self.update_time_display()
                messagebox.showinfo("Success", "All data has been cleared!")
                print("✓ All data cleared")
    
    def create_widgets(self):
        """Create all GUI widgets"""
        
        # Title
        title_frame = tk.Frame(self.root, bg='#4f46e5', pady=15)
        title_frame.pack(fill='x')
        tk.Label(title_frame, text="📚 Study Time Tracker 2026", 
                font=('Arial', 24, 'bold'), bg='#4f46e5', fg='white').pack()
        
        # Main container
        main_container = tk.Frame(self.root, bg='#f0f4f8')
        main_container.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Left panel - Controls
        left_panel = tk.Frame(main_container, bg='white', padx=20, pady=20)
        left_panel.pack(side='left', fill='both', padx=(0, 10))
        
        # Subject selection
        tk.Label(left_panel, text="Select Subject:", 
                font=('Arial', 12, 'bold'), bg='white').pack(anchor='w', pady=(0, 5))
        
        subject_frame = tk.Frame(left_panel, bg='white')
        subject_frame.pack(fill='x', pady=5)
        
        self.subject_combo = ttk.Combobox(subject_frame, textvariable=self.current_subject, 
                                          font=('Arial', 11), width=25, state='readonly')
        self.subject_combo['values'] = list(self.subjects.keys())
        self.subject_combo.pack(fill='x', pady=5)
        
        btn_frame = tk.Frame(subject_frame, bg='white')
        btn_frame.pack(fill='x', pady=5)
        
        tk.Button(btn_frame, text="+ New", command=self.add_subject,
                 bg='#10b981', fg='white', font=('Arial', 9, 'bold'),
                 padx=10, pady=5).pack(side='left', padx=(0, 5))
        
        tk.Button(btn_frame, text="🗑️ Delete", command=self.delete_subject,
                 bg='#ef4444', fg='white', font=('Arial', 9, 'bold'),
                 padx=10, pady=5).pack(side='left')
        
        # Timer display
        timer_frame = tk.Frame(left_panel, bg='#e0e7ff', pady=20, padx=20)
        timer_frame.pack(fill='x', pady=20)
        
        tk.Label(timer_frame, text="Current Session:", 
                font=('Arial', 11), bg='#e0e7ff').pack()
        
        self.time_label = tk.Label(timer_frame, text="00:00:00", 
                                   font=('Arial', 42, 'bold'), 
                                   bg='#e0e7ff', fg='#4f46e5')
        self.time_label.pack()
        
        # Control buttons
        button_frame = tk.Frame(left_panel, bg='white')
        button_frame.pack(pady=10)
        
        self.start_btn = tk.Button(button_frame, text="▶ Start", command=self.start_timer,
                                   bg='#10b981', fg='white', font=('Arial', 11, 'bold'),
                                   padx=20, pady=8)
        self.start_btn.pack(pady=3, fill='x')
        
        self.pause_btn = tk.Button(button_frame, text="⏸ Pause", command=self.pause_timer,
                                   bg='#f59e0b', fg='white', font=('Arial', 11, 'bold'),
                                   padx=20, pady=8, state='disabled')
        self.pause_btn.pack(pady=3, fill='x')
        
        self.stop_btn = tk.Button(button_frame, text="⏹ Stop", command=self.stop_timer,
                                  bg='#ef4444', fg='white', font=('Arial', 11, 'bold'),
                                  padx=20, pady=8, state='disabled')
        self.stop_btn.pack(pady=3, fill='x')
        
        # Stats
        stats_frame = tk.Frame(left_panel, bg='white')
        stats_frame.pack(fill='x', pady=10)
        
        stat1 = tk.Frame(stats_frame, bg='#e0e7ff', padx=15, pady=12)
        stat1.pack(fill='x', pady=5)
        tk.Label(stat1, text="Total Time", font=('Arial', 10), bg='#e0e7ff').pack()
        self.total_time_label = tk.Label(stat1, text="0.0h", 
                                        font=('Arial', 20, 'bold'), 
                                        bg='#e0e7ff', fg='#4f46e5')
        self.total_time_label.pack()
        
        stat2 = tk.Frame(stats_frame, bg='#d1fae5', padx=15, pady=12)
        stat2.pack(fill='x', pady=5)
        tk.Label(stat2, text="Subjects", font=('Arial', 10), bg='#d1fae5').pack()
        self.subjects_count_label = tk.Label(stat2, text="0", 
                                            font=('Arial', 20, 'bold'), 
                                            bg='#d1fae5', fg='#10b981')
        self.subjects_count_label.pack()
        
        stat3 = tk.Frame(stats_frame, bg='#fef3c7', padx=15, pady=12)
        stat3.pack(fill='x', pady=5)
        tk.Label(stat3, text="Days Tracked", font=('Arial', 10), bg='#fef3c7').pack()
        self.days_count_label = tk.Label(stat3, text="0", 
                                        font=('Arial', 20, 'bold'), 
                                        bg='#fef3c7', fg='#f59e0b')
        self.days_count_label.pack()
        
        # Clear data button
        tk.Button(left_panel, text="🧹 Clear All Data", command=self.clear_all_data,
                 bg='#dc2626', fg='white', font=('Arial', 9, 'bold'),
                 padx=15, pady=8).pack(pady=10, fill='x')
        
        # Right panel - Charts
        right_panel = tk.Frame(main_container, bg='white', padx=15, pady=15)
        right_panel.pack(side='right', fill='both', expand=True)
        
        # Chart view selection
        view_frame = tk.Frame(right_panel, bg='white')
        view_frame.pack(fill='x', pady=(0, 10))
        
        tk.Label(view_frame, text="📊 Chart View:", 
                font=('Arial', 12, 'bold'), bg='white').pack(side='left', padx=(0, 10))
        
        tk.Radiobutton(view_frame, text="Total Daily Progress", 
                      variable=self.chart_view, value="total",
                      font=('Arial', 10), bg='white',
                      command=self.update_charts).pack(side='left', padx=5)
        
        tk.Radiobutton(view_frame, text="Individual Subject", 
                      variable=self.chart_view, value="individual",
                      font=('Arial', 10), bg='white',
                      command=self.update_charts).pack(side='left', padx=5)
        
        # Subject selector for individual view
        self.subject_view_frame = tk.Frame(view_frame, bg='white')
        self.subject_view_frame.pack(side='left', padx=10)
        
        self.subject_view_combo = ttk.Combobox(self.subject_view_frame, 
                                              textvariable=self.selected_subject_view,
                                              font=('Arial', 9), width=20, state='readonly')
        self.subject_view_combo.bind('<<ComboboxSelected>>', lambda e: self.update_charts())
        
        # Chart canvas
        self.figure = Figure(figsize=(9, 7), facecolor='white', dpi=100)
        self.canvas = FigureCanvasTkAgg(self.figure, right_panel)
        self.canvas.get_tk_widget().pack(fill='both', expand=True)
    
    def add_subject(self):
        """Add a new subject"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add New Subject")
        dialog.geometry("350x140")
        dialog.configure(bg='white')
        dialog.transient(self.root)
        dialog.grab_set()
        
        tk.Label(dialog, text="Subject Name:", font=('Arial', 11, 'bold'), 
                bg='white').pack(pady=10)
        
        entry = tk.Entry(dialog, font=('Arial', 11), width=30)
        entry.pack(pady=5, padx=20)
        entry.focus()
        
        def save_subject():
            name = entry.get().strip()
            if name:
                if name not in self.subjects:
                    self.subjects[name] = 0
                    self.subject_combo['values'] = list(self.subjects.keys())
                    self.subject_view_combo['values'] = list(self.subjects.keys())
                    self.current_subject.set(name)
                    self.save_data()
                    self.update_charts()
                    self.update_stats()
                    dialog.destroy()
                else:
                    messagebox.showwarning("Warning", "Subject already exists!")
            else:
                messagebox.showwarning("Warning", "Please enter a subject name!")
        
        tk.Button(dialog, text="Add Subject", command=save_subject, 
                 bg='#10b981', fg='white', font=('Arial', 10, 'bold'),
                 padx=30, pady=8).pack(pady=10)
        
        entry.bind('<Return>', lambda e: save_subject())
    
    def delete_subject(self):
        """Delete selected subject"""
        subject = self.current_subject.get()
        if not subject:
            messagebox.showwarning("Warning", "Please select a subject to delete!")
            return
        
        if messagebox.askyesno("Confirm Delete", 
                              f"Delete '{subject}' and all its data?\n\n"
                              f"Time: {self.subjects[subject]/3600:.2f} hours"):
            # Remove from subjects
            del self.subjects[subject]
            
            # Remove from daily data
            for date in self.daily_data:
                if subject in self.daily_data[date]:
                    del self.daily_data[date][subject]
            
            self.subject_combo['values'] = list(self.subjects.keys())
            self.subject_view_combo['values'] = list(self.subjects.keys())
            self.current_subject.set('')
            self.selected_subject_view.set('')
            self.save_data()
            self.update_charts()
            self.update_stats()
    
    def start_timer(self):
        """Start the timer"""
        if not self.current_subject.get():
            messagebox.showwarning("Warning", "Please select or add a subject first!")
            return
        
        self.is_running = True
        self.start_btn.config(state='disabled')
        self.pause_btn.config(state='normal')
        self.stop_btn.config(state='normal')
        self.subject_combo.config(state='disabled')
        
        if self.timer_thread is None or not self.timer_thread.is_alive():
            self.timer_thread = threading.Thread(target=self.run_timer, daemon=True)
            self.timer_thread.start()
    
    def run_timer(self):
        """Timer thread function"""
        while self.is_running:
            time.sleep(1)
            self.elapsed_time += 1
            self.update_time_display()
    
    def pause_timer(self):
        """Pause the timer"""
        self.is_running = False
        self.start_btn.config(state='normal')
        self.pause_btn.config(state='disabled')
    
    def stop_timer(self):
        """Stop the timer and save time"""
        self.is_running = False
        
        subject = self.current_subject.get()
        if subject and self.elapsed_time > 0:
            # Update total time
            old_time = self.subjects.get(subject, 0)
            self.subjects[subject] = old_time + self.elapsed_time
            
            # Update daily data
            today = datetime.now().strftime("%Y-%m-%d")
            if today not in self.daily_data:
                self.daily_data[today] = {}
            
            self.daily_data[today][subject] = self.daily_data[today].get(subject, 0) + self.elapsed_time
            
            print(f"✓ Saved {self.elapsed_time/60:.1f} minutes to '{subject}' on {today}")
            self.save_data()
            self.update_charts()
            self.update_stats()
        
        self.elapsed_time = 0
        self.update_time_display()
        
        self.start_btn.config(state='normal')
        self.pause_btn.config(state='disabled')
        self.stop_btn.config(state='disabled')
        self.subject_combo.config(state='readonly')
    
    def update_time_display(self):
        """Update timer display"""
        hours = self.elapsed_time // 3600
        minutes = (self.elapsed_time % 3600) // 60
        seconds = self.elapsed_time % 60
        time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        self.time_label.config(text=time_str)
    
    def update_stats(self):
        """Update statistics display"""
        total_seconds = sum(self.subjects.values())
        total_hours = total_seconds / 3600
        self.total_time_label.config(text=f"{total_hours:.1f}h")
        self.subjects_count_label.config(text=str(len(self.subjects)))
        self.days_count_label.config(text=str(len(self.daily_data)))
    
    def update_charts(self):
        """Update the charts based on selected view"""
        self.figure.clear()
        
        view_mode = self.chart_view.get()
        
        if not self.subjects or not self.daily_data:
            ax = self.figure.add_subplot(111)
            ax.text(0.5, 0.5, 'No study data yet\nStart tracking!', 
                   ha='center', va='center', fontsize=18, color='gray')
            ax.axis('off')
            self.subject_view_frame.pack_forget()
            self.canvas.draw()
            self.update_stats()
            return
        
        if view_mode == "total":
            self.subject_view_frame.pack_forget()
            self.plot_total_daily_progress()
        else:
            self.subject_view_frame.pack(side='left', padx=10)
            self.subject_view_combo.pack()
            if not self.selected_subject_view.get() and self.subjects:
                subjects_list = list(self.subjects.keys())
                if subjects_list:
                    self.selected_subject_view.set(subjects_list[0])
                self.subject_view_combo['values'] = subjects_list
            self.plot_individual_daily_progress()
        
        self.canvas.draw()
        self.update_stats()
    
    def plot_total_daily_progress(self):
        """Plot total daily study time progress"""
        # Prepare data
        sorted_dates = sorted(self.daily_data.keys())
        
        if not sorted_dates:
            ax = self.figure.add_subplot(111)
            ax.text(0.5, 0.5, 'No daily data yet\nStart studying!', 
                   ha='center', va='center', fontsize=18, color='gray')
            ax.axis('off')
            return
        
        dates = [datetime.strptime(d, "%Y-%m-%d") for d in sorted_dates]
        daily_hours = []
        cumulative_hours = []
        cumsum = 0
        
        for date_str in sorted_dates:
            daily_total = sum(self.daily_data[date_str].values()) / 3600
            daily_hours.append(daily_total)
            cumsum += daily_total
            cumulative_hours.append(cumsum)
        
        # Plot 1: Daily hours
        ax1 = self.figure.add_subplot(211)
        ax1.plot(dates, daily_hours, marker='o', linewidth=2, markersize=6, 
                color='#10b981', label='Daily Hours')
        ax1.fill_between(dates, daily_hours, alpha=0.3, color='#10b981')
        ax1.set_ylabel('Hours', fontsize=11, fontweight='bold')
        ax1.set_title('📊 Daily Study Time', fontsize=13, fontweight='bold', pad=15)
        ax1.grid(True, alpha=0.3, linestyle='--')
        ax1.legend(loc='upper left')
        
        # Format x-axis
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        ax1.xaxis.set_major_locator(mdates.AutoDateLocator())
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
        
        # Plot 2: Cumulative hours
        ax2 = self.figure.add_subplot(212)
        ax2.plot(dates, cumulative_hours, marker='s', linewidth=2, markersize=6,
                color='#4f46e5', label='Cumulative Hours')
        ax2.fill_between(dates, cumulative_hours, alpha=0.3, color='#4f46e5')
        ax2.set_xlabel('Date', fontsize=11, fontweight='bold')
        ax2.set_ylabel('Total Hours', fontsize=11, fontweight='bold')
        ax2.set_title('📈 Cumulative Study Time', fontsize=13, fontweight='bold', pad=15)
        ax2.grid(True, alpha=0.3, linestyle='--')
        ax2.legend(loc='upper left')
        
        # Format x-axis
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        ax2.xaxis.set_major_locator(mdates.AutoDateLocator())
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
        
        self.figure.tight_layout(pad=2)
    
    def plot_individual_daily_progress(self):
        """Plot individual subject daily progress"""
        subject = self.selected_subject_view.get()
        
        if not subject or subject not in self.subjects:
            ax = self.figure.add_subplot(111)
            ax.text(0.5, 0.5, 'Select a subject to view details', 
                   ha='center', va='center', fontsize=16, color='gray')
            ax.axis('off')
            return
        
        # Collect daily data for this subject
        subject_daily_data = {}
        for date_str, subjects_dict in self.daily_data.items():
            if subject in subjects_dict:
                subject_daily_data[date_str] = subjects_dict[subject]
        
        if not subject_daily_data:
            ax = self.figure.add_subplot(111)
            ax.text(0.5, 0.5, f'No daily data for {subject}\nStart studying this subject!', 
                   ha='center', va='center', fontsize=16, color='gray')
            ax.axis('off')
            return
        
        sorted_dates = sorted(subject_daily_data.keys())
        dates = [datetime.strptime(d, "%Y-%m-%d") for d in sorted_dates]
        daily_hours = [subject_daily_data[d] / 3600 for d in sorted_dates]
        
        cumulative_hours = []
        cumsum = 0
        for h in daily_hours:
            cumsum += h
            cumulative_hours.append(cumsum)
        
        # Plot 1: Daily hours for subject
        ax1 = self.figure.add_subplot(211)
        ax1.plot(dates, daily_hours, marker='o', linewidth=2, markersize=6,
                color='#f59e0b', label=f'{subject} - Daily')
        ax1.fill_between(dates, daily_hours, alpha=0.3, color='#f59e0b')
        ax1.set_ylabel('Hours', fontsize=11, fontweight='bold')
        ax1.set_title(f'📚 Daily Study Time - {subject}', fontsize=13, fontweight='bold', pad=15)
        ax1.grid(True, alpha=0.3, linestyle='--')
        ax1.legend(loc='upper left')
        
        # Format x-axis
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        ax1.xaxis.set_major_locator(mdates.AutoDateLocator())
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
        
        # Plot 2: Cumulative hours for subject
        ax2 = self.figure.add_subplot(212)
        ax2.plot(dates, cumulative_hours, marker='s', linewidth=2, markersize=6,
                color='#8b5cf6', label=f'{subject} - Cumulative')
        ax2.fill_between(dates, cumulative_hours, alpha=0.3, color='#8b5cf6')
        ax2.set_xlabel('Date', fontsize=11, fontweight='bold')
        ax2.set_ylabel('Total Hours', fontsize=11, fontweight='bold')
        ax2.set_title(f'📈 Cumulative Progress - {subject}', fontsize=13, fontweight='bold', pad=15)
        ax2.grid(True, alpha=0.3, linestyle='--')
        ax2.legend(loc='upper left')
        
        # Format x-axis
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        ax2.xaxis.set_major_locator(mdates.AutoDateLocator())
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
        
        # Add total info
        total_hours = self.subjects[subject] / 3600
        ax2.text(0.02, 0.98, f'Total: {total_hours:.1f}h', 
                transform=ax2.transAxes, fontsize=11, fontweight='bold',
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        self.figure.tight_layout(pad=2)

def main():
    root = tk.Tk()
    app = StudyTimeTracker(root)
    root.mainloop()

if __name__ == "__main__":
    main()