import tkinter as tk
from tkinter import ttk, messagebox
import re
import json
import os
import time
from abc import ABC, abstractmethod
from datetime import datetime
import threading

# ============================== EXCEPTION CUSTOM ==============================
class ValidationError(Exception):
    """Exception untuk validasi input"""
    pass

class FileOperationError(Exception):
    """Exception untuk operasi file"""
    pass

# ============================== REGEX PATTERNS ==============================
class RegexPatterns:
    """Kelas untuk menyimpan pola regex"""
    NIM_PATTERN = r'^[0-9]{12}$'  # 12 digit angka
    NAME_PATTERN = r'^[A-Za-z\s.,-]{3,50}$'  # Huruf, spasi, titik, koma, strip
    EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    PHONE_PATTERN = r'^08[0-9]{8,11}$'  # Nomor HP Indonesia

# ============================== ABSTRACT CLASS ==============================
class DataOperations(ABC):
    """Abstract class untuk operasi data"""
    @abstractmethod
    def display_data(self):
        pass

    @abstractmethod
    def save_to_file(self):
        pass

    @abstractmethod
    def load_from_file(self):
        pass

# ============================== CLASS MAHASISWA ==============================
class Mahasiswa:
    """Kelas untuk merepresentasikan data mahasiswa"""
    def __init__(self, nim='', nama='', jurusan='', email='', telepon='', ipk=0.0):
        self._nim = str(nim)
        self._nama = str(nama)
        self._jurusan = str(jurusan)
        self._email = str(email)
        self._telepon = str(telepon)
        self._ipk = float(ipk)
        self._created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Getter methods
    @property
    def nim(self):
        return self._nim

    @property
    def nama(self):
        return self._nama

    @property
    def jurusan(self):
        return self._jurusan

    @property
    def email(self):
        return self._email

    @property
    def telepon(self):
        return self._telepon

    @property
    def ipk(self):
        return self._ipk

    @property
    def created_at(self):
        return self._created_at

    @property
    def updated_at(self):
        return self._updated_at

    # Setter methods dengan validasi
    @nim.setter
    def nim(self, value):
        if re.match(RegexPatterns.NIM_PATTERN, str(value)):
            self._nim = str(value)
            self._updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        else:
            raise ValidationError("NIM harus 12 digit angka!")

    @nama.setter
    def nama(self, value):
        if re.match(RegexPatterns.NAME_PATTERN, str(value)):
            self._nama = str(value)
            self._updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        else:
            raise ValidationError("Nama hanya boleh huruf, spasi, titik, koma, strip (3-50 karakter)!")

    @jurusan.setter
    def jurusan(self, value):
        self._jurusan = str(value)
        self._updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @email.setter
    def email(self, value):
        if value == "" or re.match(RegexPatterns.EMAIL_PATTERN, value):
            self._email = value
            self._updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        else:
            raise ValidationError("Format email tidak valid!")

    @telepon.setter
    def telepon(self, value):
        if value == "" or re.match(RegexPatterns.PHONE_PATTERN, value):
            self._telepon = value
            self._updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        else:
            raise ValidationError("Nomor telepon harus dimulai dengan 08 dan 10-13 digit!")

    @ipk.setter
    def ipk(self, value):
        try:
            ipk_value = float(value)
            if 0.0 <= ipk_value <= 4.0:
                self._ipk = ipk_value
                self._updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            else:
                raise ValidationError("IPK harus antara 0.0 - 4.0!")
        except ValueError:
            raise ValidationError("IPK harus berupa angka!")

    def to_dict(self):
        """Konversi objek ke dictionary"""
        return {
            'nim': self._nim,
            'nama': self._nama,
            'jurusan': self._jurusan,
            'email': self._email,
            'telepon': self._telepon,
            'ipk': self._ipk,
            'created_at': self._created_at,
            'updated_at': self._updated_at
        }

    @classmethod
    def from_dict(cls, data):
        """Membuat objek dari dictionary"""
        mahasiswa = cls(
            nim=data.get('nim', ''),
            nama=data.get('nama', ''),
            jurusan=data.get('jurusan', ''),
            email=data.get('email', ''),
            telepon=data.get('telepon', ''),
            ipk=data.get('ipk', 0.0)
        )
        mahasiswa._created_at = data.get('created_at', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        mahasiswa._updated_at = data.get('updated_at', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        return mahasiswa

    def __str__(self):
        return f"{self._nim} - {self._nama} - {self._jurusan} - IPK: {self._ipk:.2f}"

# ============================== CLASS MANAJER DATA ==============================
class DataMahasiswaManager(DataOperations):
    """Kelas untuk mengelola data mahasiswa dengan array dan pointer"""
    def __init__(self):
        self._data_mahasiswa = []  # Array untuk menyimpan data
        self._current_index = 0     # Pointer untuk navigasi
        self._filename = "data_mahasiswa.json"
        self._autosave = True
        self._sort_history = []

    # CRUD dasar
    def add_mahasiswa(self, mahasiswa: Mahasiswa):
        """Menambahkan mahasiswa baru ke array"""
        # Cek duplikasi NIM
        for mhs in self._data_mahasiswa:
            if mhs.nim == mahasiswa.nim:
                raise ValidationError(f"NIM {mahasiswa.nim} sudah terdaftar!")
        
        self._data_mahasiswa.append(mahasiswa)
        if self._autosave:
            self._autosave_to_file()

    def edit_mahasiswa(self, index, mahasiswa: Mahasiswa):
        if 0 <= index < len(self._data_mahasiswa):
            # Cek duplikasi NIM dengan data lain
            for i, mhs in enumerate(self._data_mahasiswa):
                if i != index and mhs.nim == mahasiswa.nim:
                    raise ValidationError(f"NIM {mahasiswa.nim} sudah terdaftar!")
            
            self._data_mahasiswa[index] = mahasiswa
            if self._autosave:
                self._autosave_to_file()
            return True
        return False

    def delete_mahasiswa(self, index):
        if 0 <= index < len(self._data_mahasiswa):
            deleted = self._data_mahasiswa.pop(index)
            # adjust pointer if needed
            if self._current_index >= len(self._data_mahasiswa):
                self._current_index = max(0, len(self._data_mahasiswa) - 1)
            if self._autosave:
                self._autosave_to_file()
            return deleted
        return None

    def get_mahasiswa(self, index):
        if 0 <= index < len(self._data_mahasiswa):
            return self._data_mahasiswa[index]
        return None

    def get_all_mahasiswa(self):
        return self._data_mahasiswa.copy()

    def get_count(self):
        return len(self._data_mahasiswa)

    # pointer navigation
    def next(self):
        if self._current_index < len(self._data_mahasiswa) - 1:
            self._current_index += 1
        return self._current_index

    def prev(self):
        if self._current_index > 0:
            self._current_index -= 1
        return self._current_index

    def get_current(self):
        if self._data_mahasiswa and 0 <= self._current_index < len(self._data_mahasiswa):
            return self._data_mahasiswa[self._current_index]
        return None

    def get_current_index(self):
        return self._current_index

    def set_current_index(self, idx):
        if 0 <= idx < len(self._data_mahasiswa):
            self._current_index = idx
        elif self._data_mahasiswa:
            self._current_index = 0
        else:
            self._current_index = -1

    def display_data(self):
        result = []
        for i, mhs in enumerate(self._data_mahasiswa):
            result.append(f"{i+1}. {mhs}")
        return "\n".join(result)

    # ============ SEARCH ============
    def linear_search(self, keyword, field='nama'):
        results = []
        keyword = keyword.lower()
        for mhs in self._data_mahasiswa:
            try:
                value = str(getattr(mhs, field, '')).lower()
                if keyword in value:
                    results.append(mhs)
            except AttributeError:
                continue
        return results

    def binary_search(self, nim):
        if not self._data_mahasiswa:
            return None
        
        # Buat salinan terurut untuk pencarian
        sorted_data = sorted(self._data_mahasiswa.copy(), key=lambda x: x.nim)
        left, right = 0, len(sorted_data) - 1
        
        while left <= right:
            mid = (left + right) // 2
            current_nim = sorted_data[mid].nim
            if current_nim == nim:
                # Cari index asli di data utama
                for i, mhs in enumerate(self._data_mahasiswa):
                    if mhs.nim == nim:
                        return mhs
            elif current_nim < nim:
                left = mid + 1
            else:
                right = mid - 1
        return None

    def sequential_search(self, keyword, field='nama'):
        return self.linear_search(keyword, field)

    def search_by_multiple(self, criteria):
        """Mencari dengan multiple criteria"""
        results = self._data_mahasiswa.copy()
        for field, value in criteria.items():
            if value:
                results = [mhs for mhs in results if value.lower() in str(getattr(mhs, field, '')).lower()]
        return results

    # ============ SORTING ============
    def bubble_sort(self, field='nim', ascending=True):
        n = len(self._data_mahasiswa)
        for i in range(n-1):
            swapped = False
            for j in range(n-i-1):
                try:
                    val1 = getattr(self._data_mahasiswa[j], field)
                    val2 = getattr(self._data_mahasiswa[j+1], field)
                    
                    # Handle comparison for different types
                    compare_result = (val1 > val2) if ascending else (val1 < val2)
                    
                    if compare_result:
                        self._data_mahasiswa[j], self._data_mahasiswa[j+1] = self._data_mahasiswa[j+1], self._data_mahasiswa[j]
                        swapped = True
                except (AttributeError, TypeError):
                    continue
            if not swapped:
                break
        
        self._record_sort(field, ascending, 'Bubble Sort')

    def selection_sort(self, field='nim', ascending=True):
        n = len(self._data_mahasiswa)
        for i in range(n):
            sel = i
            for j in range(i+1, n):
                try:
                    if ascending:
                        if getattr(self._data_mahasiswa[j], field) < getattr(self._data_mahasiswa[sel], field):
                            sel = j
                    else:
                        if getattr(self._data_mahasiswa[j], field) > getattr(self._data_mahasiswa[sel], field):
                            sel = j
                except (AttributeError, TypeError):
                    continue
            if sel != i:
                self._data_mahasiswa[i], self._data_mahasiswa[sel] = self._data_mahasiswa[sel], self._data_mahasiswa[i]
        
        self._record_sort(field, ascending, 'Selection Sort')

    def insertion_sort(self, field='nim', ascending=True):
        for i in range(1, len(self._data_mahasiswa)):
            key = self._data_mahasiswa[i]
            j = i - 1
            try:
                while j >= 0 and ((getattr(key, field) < getattr(self._data_mahasiswa[j], field)) if ascending else (getattr(key, field) > getattr(self._data_mahasiswa[j], field))):
                    self._data_mahasiswa[j + 1] = self._data_mahasiswa[j]
                    j -= 1
            except (AttributeError, TypeError):
                continue
            self._data_mahasiswa[j + 1] = key
        
        self._record_sort(field, ascending, 'Insertion Sort')

    def quick_sort(self, field='nim', ascending=True):
        """Implementasi Quick Sort"""
        def _quick_sort(arr):
            if len(arr) <= 1:
                return arr
            pivot = arr[len(arr) // 2]
            left = [x for x in arr if getattr(x, field) < getattr(pivot, field)]
            middle = [x for x in arr if getattr(x, field) == getattr(pivot, field)]
            right = [x for x in arr if getattr(x, field) > getattr(pivot, field)]
            
            if ascending:
                return _quick_sort(left) + middle + _quick_sort(right)
            else:
                return _quick_sort(right) + middle + _quick_sort(left)
        
        self._data_mahasiswa = _quick_sort(self._data_mahasiswa)
        self._record_sort(field, ascending, 'Quick Sort')

    def _record_sort(self, field, ascending, algorithm):
        """Mencatat riwayat sorting"""
        self._sort_history.append({
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'field': field,
            'ascending': ascending,
            'algorithm': algorithm,
            'count': len(self._data_mahasiswa)
        })

    # ============ STATISTICS ============
    def get_statistics(self):
        if not self._data_mahasiswa:
            return {}
        
        ipk_values = [mhs.ipk for mhs in self._data_mahasiswa]
        jurusan_count = {}
        for mhs in self._data_mahasiswa:
            jurusan_count[mhs.jurusan] = jurusan_count.get(mhs.jurusan, 0) + 1
        
        return {
            'total': len(self._data_mahasiswa),
            'avg_ipk': sum(ipk_values) / len(ipk_values),
            'max_ipk': max(ipk_values),
            'min_ipk': min(ipk_values),
            'jurusan_distribution': jurusan_count,
            'total_sort_operations': len(self._sort_history)
        }

    # ============ FILE OPERATIONS ============
    def save_to_file(self, filename=None):
        try:
            save_filename = filename or self._filename
            data = [mhs.to_dict() for mhs in self._data_mahasiswa]
            
            # Tambah metadata
            metadata = {
                'metadata': {
                    'saved_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'total_records': len(data),
                    'version': '2.0'
                },
                'data': data
            }
            
            with open(save_filename, 'w', encoding='utf-8') as file:
                json.dump(metadata, file, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            raise FileOperationError(f"Gagal menyimpan file: {str(e)}")

    def load_from_file(self, filename=None):
        try:
            load_filename = filename or self._filename
            if os.path.exists(load_filename):
                with open(load_filename, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                
                # Handle format baru dan lama
                if isinstance(data, dict) and 'data' in data:
                    data_list = data['data']
                else:
                    data_list = data
                
                self._data_mahasiswa = [Mahasiswa.from_dict(item) for item in data_list]
                self._current_index = 0 if self._data_mahasiswa else -1
                return True
            return False
        except json.JSONDecodeError:
            raise FileOperationError("File data korup atau format tidak valid!")
        except Exception as e:
            raise FileOperationError(f"Gagal memuat file: {str(e)}")

    def _autosave_to_file(self):
        """Autosave dengan thread untuk tidak mengganggu UI"""
        def save_thread():
            try:
                self.save_to_file()
            except:
                pass
        
        thread = threading.Thread(target=save_thread, daemon=True)
        thread.start()

    def export_to_csv(self, filename="data_mahasiswa.csv"):
        """Export data ke CSV"""
        try:
            import csv
            with open(filename, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(['NIM', 'Nama', 'Jurusan', 'Email', 'Telepon', 'IPK', 'Created At', 'Updated At'])
                for mhs in self._data_mahasiswa:
                    writer.writerow([mhs.nim, mhs.nama, mhs.jurusan, mhs.email, mhs.telepon, 
                                    f"{mhs.ipk:.2f}", mhs.created_at, mhs.updated_at])
            return True
        except Exception as e:
            raise FileOperationError(f"Gagal export ke CSV: {str(e)}")

# ============================== GUI APPLICATION ==============================
class MahasiswaApp:
    """Kelas utama untuk aplikasi GUI"""
    def __init__(self, root):
        self.root = root
        self.root.title("Manajemen Data Mahasiswa - Enhanced Version")
        self.root.geometry("1200x800")
        self.root.configure(bg='#2E7D32')  # Hijau gelap
        
        # Set minimum size
        self.root.minsize(1000, 700)
        
        # Inisialisasi data manager
        self.data_manager = DataMahasiswaManager()
        
        # Load data dari file (jika ada)
        self.load_initial_data()
        
        # Setup GUI
        self.setup_styles()
        self.create_widgets()
        self.update_display()
        
        # Auto-save timer
        self.setup_autosave()

    def setup_autosave(self):
        """Setup timer untuk auto-save"""
        def autosave():
            try:
                self.data_manager.save_to_file()
            except:
                pass
            self.root.after(30000, autosave)  # Auto-save setiap 30 detik
        
        self.root.after(30000, autosave)

    def load_initial_data(self):
        """Load data awal dengan error handling"""
        try:
            if not self.data_manager.load_from_file():
                messagebox.showinfo("Info", "📄 File data tidak ditemukan. Membuat data baru.")
        except FileOperationError as e:
            messagebox.showwarning("Peringatan", f"⚠ {str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"❌ Gagal memuat data: {str(e)}")

    def setup_styles(self):
        """Setup styles untuk widget"""
        self.style = ttk.Style()
        try:
            self.style.theme_use('clam')
        except:
            pass

        self.colors = {
            'primary': '#2E7D32',
            'secondary': '#4CAF50',
            'accent': '#FFEB3B',
            'background': '#E8F5E9',
            'text': '#212121',
            'error': '#F44336',
            'warning': '#FF9800',
            'info': '#2196F3'
        }

        # Configure styles
        self.style.configure('TFrame', background=self.colors['primary'])
        self.style.configure('TLabel', background=self.colors['primary'], foreground='white')
        self.style.configure('TButton', background=self.colors['secondary'], foreground='black')
        self.style.configure('TLabelframe', background=self.colors['primary'], foreground='white')
        self.style.configure('TLabelframe.Label', background=self.colors['primary'], foreground='white')
        
        self.style.configure('Title.TLabel', font=('Arial', 18, 'bold'), 
                           background=self.colors['primary'], foreground=self.colors['accent'])
        self.style.configure('Subtitle.TLabel', font=('Arial', 11, 'bold'),
                           background=self.colors['primary'], foreground='white')
        
        self.style.configure('Primary.TButton', background=self.colors['secondary'], 
                           foreground='white', font=('Arial', 9, 'bold'))
        self.style.configure('Secondary.TButton', background=self.colors['info'], 
                           foreground='white', font=('Arial', 9))
        
        self.style.configure('Treeview', background=self.colors['background'], 
                           fieldbackground=self.colors['background'], foreground=self.colors['text'])
        self.style.configure('Treeview.Heading', background=self.colors['secondary'], 
                           foreground='black', font=('Arial', 9, 'bold'))
        self.style.map('Treeview', background=[('selected', '#81C784')])
        
        self.style.configure('Error.TLabel', background=self.colors['error'], foreground='white')
        self.style.configure('Success.TLabel', background=self.colors['secondary'], foreground='white')

    def create_widgets(self):
        """Membuat semua widget GUI"""
        # Main container
        main_container = ttk.Frame(self.root, padding="5")
        main_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        main_container.grid_rowconfigure(0, weight=1)
        main_container.grid_columnconfigure(0, weight=1)
        
        # Create notebook (tabbed interface)
        self.notebook = ttk.Notebook(main_container)
        self.notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Tab 1: Data Management
        self.create_data_tab()
        
        # Tab 2: Search & Sort
        self.create_search_sort_tab()
        
        # Tab 3: Statistics
        self.create_statistics_tab()
        
        # Status bar
        self.create_status_bar(main_container)

    def create_data_tab(self):
        """Membuat tab untuk manajemen data"""
        data_tab = ttk.Frame(self.notebook)
        self.notebook.add(data_tab, text="📝 Data Management")
        
        # Title
        title_frame = ttk.Frame(data_tab)
        title_frame.pack(fill=tk.X, padx=10, pady=10)
        ttk.Label(title_frame, text="MANAJEMEN DATA MAHASISWA", 
                 style='Title.TLabel').pack()
        ttk.Label(title_frame, text="Sistem Pengelolaan Data Mahasiswa Terintegrasi",
                 style='Subtitle.TLabel').pack()
        
        # Content frame dengan grid
        content_frame = ttk.Frame(data_tab)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Left side: Input form
        input_frame = ttk.LabelFrame(content_frame, text="📋 Form Input Data", padding="15")
        input_frame.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.W), padx=(0, 10), pady=5)
        
        self.create_input_form(input_frame)
        
        # Right side: Data table
        table_frame = ttk.LabelFrame(content_frame, text="📊 Data Mahasiswa", padding="10")
        table_frame.grid(row=0, column=1, sticky=(tk.N, tk.S, tk.E, tk.W), pady=5)
        
        # Configure grid weights
        content_frame.grid_rowconfigure(0, weight=1)
        content_frame.grid_columnconfigure(1, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        self.create_data_table(table_frame)
        
        # Navigation buttons
        self.create_navigation_buttons(content_frame)

    def create_input_form(self, parent):
        """Membuat form input data"""
        fields = [
            ("NIM (12 digit):", "nim", "entry"),
            ("Nama Lengkap:", "nama", "entry"),
            ("Jurusan:", "jurusan", "combo"),
            ("Email:", "email", "entry"),
            ("Telepon:", "telepon", "entry"),
            ("IPK (0.0-4.0):", "ipk", "entry")
        ]
        
        self.entries = {}
        jurusan_options = [
            "Teknik Informatika", "Sistem Informasi", "Teknik Komputer",
            "Manajemen Informatika", "Ilmu Komputer", "Teknologi Informasi",
            "Teknik Elektro", "Teknik Industri", "Teknik Sipil",
            "Akuntansi", "Manajemen", "Hukum", "Lainnya"
        ]
        
        for i, (label, field, widget_type) in enumerate(fields):
            # Label
            lbl = ttk.Label(parent, text=label, font=('Arial', 9, 'bold'))
            lbl.grid(row=i, column=0, sticky=tk.W, pady=8, padx=(0, 10))
            
            # Widget input
            if widget_type == "entry":
                entry = ttk.Entry(parent, width=35, font=('Arial', 9))
                entry.grid(row=i, column=1, pady=8, sticky=tk.W)
                self.entries[field] = entry
                
                # Bind Enter key untuk navigasi
                entry.bind('<Return>', lambda e, f=field: self.focus_next_field(f))
                
            elif widget_type == "combo":
                combo = ttk.Combobox(parent, values=jurusan_options, 
                                   state="readonly", width=33, font=('Arial', 9))
                combo.grid(row=i, column=1, pady=8, sticky=tk.W)
                combo.set("Teknik Informatika")
                self.entries[field] = combo
        
        # Action buttons frame
        btn_frame = ttk.Frame(parent)
        btn_frame.grid(row=len(fields), column=0, columnspan=2, pady=20)
        
        button_configs = [
            ("➕ Tambah", self.add_mahasiswa, '#4CAF50'),
            ("✏️ Update", self.update_mahasiswa, '#2196F3'),
            ("🗑️ Hapus", self.delete_mahasiswa, '#F44336'),
            ("🧹 Clear", self.clear_fields, '#FF9800'),
            ("📋 Detail", self.show_details, '#9C27B0')
        ]
        
        for text, command, color in button_configs:
            btn = tk.Button(btn_frame, text=text, command=command,
                          bg=color, fg='white', font=('Arial', 9, 'bold'),
                          padx=10, pady=5, bd=0, cursor='hand2')
            btn.pack(side=tk.LEFT, padx=5)
            btn.bind("<Enter>", lambda e, b=btn: b.config(brightness=0.9))
            btn.bind("<Leave>", lambda e, b=btn: b.config(brightness=1.0))

    def focus_next_field(self, current_field):
        """Focus ke field berikutnya saat tekan Enter"""
        field_order = ['nim', 'nama', 'jurusan', 'email', 'telepon', 'ipk']
        try:
            current_idx = field_order.index(current_field)
            next_field = field_order[current_idx + 1] if current_idx + 1 < len(field_order) else 'nim'
            self.entries[next_field].focus()
        except:
            pass

    def create_data_table(self, parent):
        """Membuat tabel data"""
        # Frame untuk treeview dan scrollbar
        tree_frame = ttk.Frame(parent)
        tree_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Define columns
        columns = ('No', 'NIM', 'Nama', 'Jurusan', 'IPK', 'Status')
        
        # Create treeview
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=15)
        
        # Define column headings and widths
        col_configs = [
            ('No', 50, 'center'),
            ('NIM', 120, 'center'),
            ('Nama', 200, 'w'),
            ('Jurusan', 150, 'center'),
            ('IPK', 80, 'center'),
            ('Status', 100, 'center')
        ]
        
        for col, width, anchor in col_configs:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width, anchor=anchor)
        
        # Add scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Grid layout
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # Bind events
        self.tree.bind('<<TreeviewSelect>>', self.on_tree_select)
        self.tree.bind('<Double-Button-1>', self.on_tree_double_click)
        
        # Context menu
        self.create_context_menu()

    def create_context_menu(self):
        """Membuat context menu untuk treeview"""
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Edit Data", command=self.edit_selected)
        self.context_menu.add_command(label="Hapus Data", command=self.delete_mahasiswa)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Lihat Detail", command=self.show_details)
        self.context_menu.add_command(label="Salin NIM", command=self.copy_nim)
        
        self.tree.bind('<Button-3>', self.show_context_menu)

    def show_context_menu(self, event):
        """Menampilkan context menu"""
        try:
            self.tree.selection_set(self.tree.identify_row(event.y))
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def copy_nim(self):
        """Copy NIM ke clipboard"""
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            nim = item['values'][1]
            self.root.clipboard_clear()
            self.root.clipboard_append(nim)
            self.show_toast("NIM disalin ke clipboard!")

    def show_toast(self, message):
        """Menampilkan toast notification"""
        toast = tk.Toplevel(self.root)
        toast.overrideredirect(True)
        toast.geometry(f"300x50+{self.root.winfo_x()+450}+{self.root.winfo_y()+700}")
        
        label = tk.Label(toast, text=message, bg='#333', fg='white', 
                        font=('Arial', 10), padx=20, pady=10)
        label.pack(fill=tk.BOTH, expand=True)
        
        toast.after(2000, toast.destroy)

    def create_navigation_buttons(self, parent):
        """Membuat navigation buttons"""
        nav_frame = ttk.LabelFrame(parent, text="🔄 Navigasi & Kontrol", padding="15")
        nav_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        # Navigation buttons
        nav_btn_frame = ttk.Frame(nav_frame)
        nav_btn_frame.pack(pady=5)
        
        nav_buttons = [
            ("⏮ First", self.first_mahasiswa),
            ("⏪ Prev", self.prev_mahasiswa),
            ("Next ⏩", self.next_mahasiswa),
            ("Last ⏭", self.last_mahasiswa),
            ("🔍 Find", self.show_search_dialog)
        ]
        
        for text, command in nav_buttons:
            btn = ttk.Button(nav_btn_frame, text=text, command=command, 
                           style='Primary.TButton', width=12)
            btn.pack(side=tk.LEFT, padx=5)
        
        # Position display
        self.position_var = tk.StringVar(value="Posisi: 0/0")
        pos_label = ttk.Label(nav_frame, textvariable=self.position_var, 
                            font=('Arial', 10, 'bold'))
        pos_label.pack(pady=5)
        
        # File operations
        file_btn_frame = ttk.Frame(nav_frame)
        file_btn_frame.pack(pady=10)
        
        file_buttons = [
            ("💾 Save", self.save_data),
            ("📂 Load", self.load_data),
            ("📤 Export", self.export_data),
            ("🔄 Refresh", self.update_display),
            ("🗑️ Reset", self.reset_data)
        ]
        
        for text, command in file_buttons:
            btn = ttk.Button(file_btn_frame, text=text, command=command,
                           style='Secondary.TButton', width=10)
            btn.pack(side=tk.LEFT, padx=3)

    def create_search_sort_tab(self):
        """Membuat tab untuk search dan sort"""
        search_tab = ttk.Frame(self.notebook)
        self.notebook.add(search_tab, text="🔍 Search & Sort")
        
        # Search section
        search_frame = ttk.LabelFrame(search_tab, text="🔍 Advanced Search", padding="20")
        search_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.create_search_section(search_frame)
        
        # Sort section
        sort_frame = ttk.LabelFrame(search_tab, text="📊 Sorting Algorithms", padding="20")
        sort_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.create_sort_section(sort_frame)

    def create_search_section(self, parent):
        """Membuat section untuk search"""
        # Search criteria
        criteria_frame = ttk.Frame(parent)
        criteria_frame.pack(fill=tk.X, pady=10)
        
        search_fields = [
            ("NIM:", "nim"),
            ("Nama:", "nama"),
            ("Jurusan:", "jurusan"),
            ("Email:", "email")
        ]
        
        self.search_entries = {}
        for i, (label, field) in enumerate(search_fields):
            ttk.Label(criteria_frame, text=label).grid(row=i//2, column=(i%2)*2, 
                                                      sticky=tk.W, padx=5, pady=5)
            entry = ttk.Entry(criteria_frame, width=25)
            entry.grid(row=i//2, column=(i%2)*2+1, sticky=tk.W, padx=5, pady=5)
            self.search_entries[field] = entry
        
        # Search buttons
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(pady=15)
        
        search_methods = [
            ("Linear Search", self.do_linear_search),
            ("Binary Search", self.do_binary_search),
            ("Quick Search", self.do_quick_search),
            ("Clear", self.clear_search)
        ]
        
        for text, command in search_methods:
            btn = ttk.Button(btn_frame, text=text, command=command,
                           style='Primary.TButton', width=15)
            btn.pack(side=tk.LEFT, padx=5)

    def create_sort_section(self, parent):
        """Membuat section untuk sorting"""
        # Sort options
        options_frame = ttk.Frame(parent)
        options_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(options_frame, text="Sort by:").pack(side=tk.LEFT, padx=5)
        
        self.sort_field_var = tk.StringVar(value="nim")
        sort_fields = ttk.Combobox(options_frame, textvariable=self.sort_field_var,
                                 values=['nim', 'nama', 'jurusan', 'ipk', 'created_at'],
                                 state="readonly", width=15)
        sort_fields.pack(side=tk.LEFT, padx=5)
        
        self.sort_order_var = tk.StringVar(value="asc")
        ttk.Radiobutton(options_frame, text="Ascending", variable=self.sort_order_var,
                       value="asc").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(options_frame, text="Descending", variable=self.sort_order_var,
                       value="desc").pack(side=tk.LEFT, padx=10)
        
        # Sort buttons
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(pady=15)
        
        sort_algorithms = [
            ("Bubble Sort", self.do_bubble_sort),
            ("Selection Sort", self.do_selection_sort),
            ("Insertion Sort", self.do_insertion_sort),
            ("Quick Sort", self.do_quick_sort)
        ]
        
        for text, command in sort_algorithms:
            btn = ttk.Button(btn_frame, text=text, command=command,
                           style='Primary.TButton', width=15)
            btn.pack(side=tk.LEFT, padx=5)
        
        # Results display
        results_frame = ttk.LabelFrame(parent, text="📈 Performance", padding="10")
        results_frame.pack(fill=tk.X, pady=10)
        
        self.sort_results_var = tk.StringVar(value="Waktu eksekusi akan ditampilkan di sini...")
        ttk.Label(results_frame, textvariable=self.sort_results_var,
                 font=('Arial', 9)).pack()

    def create_statistics_tab(self):
        """Membuat tab untuk statistics"""
        stats_tab = ttk.Frame(self.notebook)
        self.notebook.add(stats_tab, text="📈 Statistics")
        
        # Statistics display
        stats_frame = ttk.LabelFrame(stats_tab, text="📊 Statistik Data", padding="20")
        stats_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.stats_text = tk.Text(stats_frame, height=15, width=60,
                                font=('Consolas', 10), bg=self.colors['background'])
        scrollbar = ttk.Scrollbar(stats_frame, command=self.stats_text.yview)
        self.stats_text.configure(yscrollcommand=scrollbar.set)
        
        self.stats_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        stats_frame.grid_rowconfigure(0, weight=1)
        stats_frame.grid_columnconfigure(0, weight=1)
        
        # Update button
        ttk.Button(stats_tab, text="🔄 Update Statistics", 
                  command=self.update_statistics, style='Primary.TButton').pack(pady=10)

    def create_status_bar(self, parent):
        """Membuat status bar"""
        status_bar = tk.Frame(parent, bg='#1B5E20', height=25)
        status_bar.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        
        self.status_var = tk.StringVar()
        self.status_var.set(f"📊 Jumlah data: {self.data_manager.get_count()} | 💾 Auto-save aktif")
        
        status_label = tk.Label(status_bar, textvariable=self.status_var,
                               bg='#1B5E20', fg='white', font=('Arial', 9))
        status_label.pack(side=tk.LEFT, padx=10)
        
        # Timer
        self.time_var = tk.StringVar()
        time_label = tk.Label(status_bar, textvariable=self.time_var,
                            bg='#1B5E20', fg='white', font=('Arial', 9))
        time_label.pack(side=tk.RIGHT, padx=10)
        
        self.update_time()

    def update_time(self):
        """Update waktu di status bar"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_var.set(f"🕒 {current_time}")
        self.root.after(1000, self.update_time)

    # ==================== EVENT HANDLERS ====================
    def add_mahasiswa(self):
        try:
            nim = self.entries['nim'].get().strip()
            nama = self.entries['nama'].get().strip()
            jurusan = self.entries['jurusan'].get().strip()
            email = self.entries['email'].get().strip()
            telepon = self.entries['telepon'].get().strip()
            ipk = self.entries['ipk'].get().strip()

            if not nim or not nama:
                raise ValidationError("NIM dan Nama harus diisi!")

            if len(nim) != 12 or not nim.isdigit():
                raise ValidationError("NIM harus 12 digit angka!")

            mahasiswa = Mahasiswa()
            mahasiswa.nim = nim
            mahasiswa.nama = nama
            mahasiswa.jurusan = jurusan
            mahasiswa.email = email
            mahasiswa.telepon = telepon

            if ipk:
                mahasiswa.ipk = ipk
            else:
                mahasiswa.ipk = 0.0

            self.data_manager.add_mahasiswa(mahasiswa)
            self.update_display()
            self.clear_fields()
            self.show_toast("✅ Data berhasil ditambahkan!")
            
        except ValidationError as e:
            messagebox.showerror("Validasi Error", f"❌ {str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"❌ Terjadi kesalahan: {str(e)}")

    def update_mahasiswa(self):
        try:
            selection = self.tree.selection()
            if not selection:
                messagebox.showwarning("Peringatan", "⚠ Pilih data yang akan diupdate!")
                return

            item = self.tree.item(selection[0])
            values = item['values']
            index = int(values[0]) - 1

            nim = self.entries['nim'].get().strip()
            nama = self.entries['nama'].get().strip()
            jurusan = self.entries['jurusan'].get().strip()
            email = self.entries['email'].get().strip()
            telepon = self.entries['telepon'].get().strip()
            ipk = self.entries['ipk'].get().strip()

            if not nim or not nama:
                raise ValidationError("NIM dan Nama harus diisi!")

            mahasiswa = Mahasiswa()
            mahasiswa.nim = nim
            mahasiswa.nama = nama
            mahasiswa.jurusan = jurusan
            mahasiswa.email = email
            mahasiswa.telepon = telepon

            if ipk:
                mahasiswa.ipk = ipk
            else:
                mahasiswa.ipk = 0.0

            if self.data_manager.edit_mahasiswa(index, mahasiswa):
                self.update_display()
                self.clear_fields()
                self.show_toast("✅ Data berhasil diupdate!")
            else:
                messagebox.showerror("Error", "❌ Gagal mengupdate data!")
                
        except ValidationError as e:
            messagebox.showerror("Validasi Error", f"❌ {str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"❌ Terjadi kesalahan: {str(e)}")

    def delete_mahasiswa(self):
        try:
            selection = self.tree.selection()
            if not selection:
                messagebox.showwarning("Peringatan", "⚠ Pilih data yang akan dihapus!")
                return

            if not messagebox.askyesno("Konfirmasi", "🗑 Apakah Anda yakin ingin menghapus data ini?"):
                return

            item = self.tree.item(selection[0])
            values = item['values']
            index = int(values[0]) - 1

            deleted = self.data_manager.delete_mahasiswa(index)
            if deleted:
                self.update_display()
                self.clear_fields()
                self.show_toast(f"✅ Data {deleted.nama} berhasil dihapus!")
            else:
                messagebox.showerror("Error", "❌ Gagal menghapus data!")
                
        except Exception as e:
            messagebox.showerror("Error", f"❌ Terjadi kesalahan: {str(e)}")

    def edit_selected(self):
        """Edit data yang dipilih dari context menu"""
        selection = self.tree.selection()
        if selection:
            self.update_mahasiswa()

    def show_details(self):
        """Menampilkan detail data"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Peringatan", "⚠ Pilih data untuk melihat detail!")
            return

        item = self.tree.item(selection[0])
        values = item['values']
        index = int(values[0]) - 1
        mhs = self.data_manager.get_mahasiswa(index)
        
        if mhs:
            details = f"""
📋 DETAIL MAHASISWA

📝 Identitas:
• NIM      : {mhs.nim}
• Nama     : {mhs.nama}
• Jurusan  : {mhs.jurusan}

📞 Kontak:
• Email    : {mhs.email if mhs.email else '-'}
• Telepon  : {mhs.telepon if mhs.telepon else '-'}

📊 Akademik:
• IPK      : {mhs.ipk:.2f}
• Status   : {'Lulus' if mhs.ipk >= 2.0 else 'Belum Lulus'}

📅 Timeline:
• Dibuat   : {mhs.created_at}
• Diupdate : {mhs.updated_at}
"""
            messagebox.showinfo("Detail Mahasiswa", details)

    def do_linear_search(self):
        keyword = self.search_entries['nim'].get().strip() or \
                 self.search_entries['nama'].get().strip() or \
                 self.search_entries['jurusan'].get().strip() or \
                 self.search_entries['email'].get().strip()
        
        if not keyword:
            messagebox.showwarning("Peringatan", "⚠ Masukkan keyword pencarian!")
            return

        start_time = time.time()
        results = self.data_manager.linear_search(keyword, 'nama')
        end_time = time.time()
        
        self.display_search_results(results, "Linear Search", end_time - start_time)

    def do_binary_search(self):
        nim = self.search_entries['nim'].get().strip()
        if not nim:
            messagebox.showwarning("Peringatan", "⚠ Masukkan NIM untuk Binary Search!")
            return

        start_time = time.time()
        result = self.data_manager.binary_search(nim)
        end_time = time.time()
        
        results = [result] if result else []
        self.display_search_results(results, "Binary Search", end_time - start_time)

    def do_quick_search(self):
        criteria = {}
        for field, entry in self.search_entries.items():
            value = entry.get().strip()
            if value:
                criteria[field] = value
        
        if not criteria:
            messagebox.showwarning("Peringatan", "⚠ Masukkan minimal satu kriteria pencarian!")
            return

        start_time = time.time()
        results = self.data_manager.search_by_multiple(criteria)
        end_time = time.time()
        
        self.display_search_results(results, "Quick Search", end_time - start_time)

    def clear_search(self):
        for entry in self.search_entries.values():
            entry.delete(0, tk.END)
        self.update_display()

    def display_search_results(self, results, algorithm, exec_time):
        if results:
            self.update_treeview(results)
            messagebox.showinfo("Hasil Pencarian", 
                              f"✅ {algorithm}\n"
                              f"📊 Ditemukan {len(results)} data\n"
                              f"⏱ Waktu eksekusi: {exec_time*1000:.3f} ms")
        else:
            messagebox.showinfo("Hasil Pencarian", "🔍 Data tidak ditemukan!")

    def do_bubble_sort(self):
        self.perform_sort('bubble')

    def do_selection_sort(self):
        self.perform_sort('selection')

    def do_insertion_sort(self):
        self.perform_sort('insertion')

    def do_quick_sort(self):
        self.perform_sort('quick')

    def perform_sort(self, algorithm):
        try:
            field = self.sort_field_var.get()
            ascending = self.sort_order_var.get() == 'asc'
            
            if not self.data_manager.get_all_mahasiswa():
                messagebox.showwarning("Peringatan", "⚠ Tidak ada data untuk diurutkan!")
                return

            start_time = time.time()
            
            if algorithm == 'bubble':
                self.data_manager.bubble_sort(field, ascending)
                algo_name = "Bubble Sort"
            elif algorithm == 'selection':
                self.data_manager.selection_sort(field, ascending)
                algo_name = "Selection Sort"
            elif algorithm == 'insertion':
                self.data_manager.insertion_sort(field, ascending)
                algo_name = "Insertion Sort"
            elif algorithm == 'quick':
                self.data_manager.quick_sort(field, ascending)
                algo_name = "Quick Sort"
            else:
                return

            end_time = time.time()
            exec_time = (end_time - start_time) * 1000
            
            self.update_display()
            self.sort_results_var.set(f"{algo_name} selesai dalam {exec_time:.3f} ms")
            self.show_toast(f"✅ Data berhasil diurutkan dengan {algo_name}")
            
        except Exception as e:
            messagebox.showerror("Error", f"❌ Terjadi kesalahan: {str(e)}")

    def save_data(self):
        try:
            self.data_manager.save_to_file()
            self.show_toast("✅ Data berhasil disimpan!")
        except FileOperationError as e:
            messagebox.showerror("Error", f"❌ {str(e)}")

    def load_data(self):
        try:
            if self.data_manager.load_from_file():
                self.update_display()
                self.show_toast("✅ Data berhasil dimuat!")
            else:
                messagebox.showinfo("Info", "📄 File data tidak ditemukan.")
        except FileOperationError as e:
            messagebox.showerror("Error", f"❌ {str(e)}")

    def export_data(self):
        try:
            filename = tk.filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
            )
            if filename:
                self.data_manager.export_to_csv(filename)
                self.show_toast(f"✅ Data berhasil diexport ke {filename}")
        except FileOperationError as e:
            messagebox.showerror("Error", f"❌ {str(e)}")

    def reset_data(self):
        if messagebox.askyesno("Konfirmasi", "⚠ Apakah Anda yakin ingin mereset semua data?"):
            self.data_manager = DataMahasiswaManager()
            self.update_display()
            self.clear_fields()
            self.show_toast("✅ Semua data telah direset!")

    def first_mahasiswa(self):
        self.data_manager.set_current_index(0)
        self.display_current_mahasiswa()

    def last_mahasiswa(self):
        count = self.data_manager.get_count()
        if count > 0:
            self.data_manager.set_current_index(count - 1)
            self.display_current_mahasiswa()

    def show_search_dialog(self):
        """Dialog untuk pencarian langsung"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Cari Data")
        dialog.geometry("400x150")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Masukkan NIM atau Nama:").pack(pady=10)
        
        search_entry = ttk.Entry(dialog, width=40)
        search_entry.pack(pady=5)
        search_entry.focus()
        
        def do_search():
            keyword = search_entry.get().strip()
            if keyword:
                results = self.data_manager.linear_search(keyword, 'nama')
                if results:
                    self.update_treeview(results)
                    dialog.destroy()
                    self.show_toast(f"✅ Ditemukan {len(results)} data")
                else:
                    messagebox.showinfo("Hasil", "Data tidak ditemukan")
        
        ttk.Button(dialog, text="Cari", command=do_search).pack(pady=10)
        search_entry.bind('<Return>', lambda e: do_search())

    def update_statistics(self):
        stats = self.data_manager.get_statistics()
        if not stats:
            self.stats_text.delete(1.0, tk.END)
            self.stats_text.insert(1.0, "Tidak ada data yang dapat dianalisis.")
            return
        
        stats_text = f"""
{'='*60}
{'STATISTIK DATA MAHASISWA':^60}
{'='*60}

📊 JUMLAH DATA:
• Total Mahasiswa  : {stats['total']}
• Operasi Sorting  : {stats.get('total_sort_operations', 0)}

📈 STATISTIK IPK:
• Rata-rata IPK    : {stats['avg_ipk']:.2f}
• IPK Tertinggi    : {stats['max_ipk']:.2f}
• IPK Terendah     : {stats['min_ipk']:.2f}

🎓 DISTRIBUSI JURUSAN:
"""
        for jurusan, count in stats['jurusan_distribution'].items():
            percentage = (count / stats['total']) * 100
            stats_text += f"• {jurusan:<25} : {count:>3} ({percentage:.1f}%)\n"
        
        stats_text += f"\n{'='*60}\n"
        stats_text += f"Diperbarui: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(1.0, stats_text)

    # ==================== HELPER METHODS ====================
    def update_display(self):
        """Update tampilan data di treeview"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Insert new data
        data = self.data_manager.get_all_mahasiswa()
        for i, mhs in enumerate(data, 1):
            status = "Lulus" if mhs.ipk >= 2.0 else "Belum"
            self.tree.insert('', 'end', values=(
                i, mhs.nim, mhs.nama, mhs.jurusan, f"{mhs.ipk:.2f}", status
            ))
        
        # Update statistics
        count = len(data)
        if count > 0:
            avg_ipk = sum(m.ipk for m in data) / count
            self.status_var.set(f"📊 Jumlah data: {count} | 📈 IPK Rata-rata: {avg_ipk:.2f} | 💾 Auto-save aktif")
        else:
            self.status_var.set(f"📊 Jumlah data: {count} | 💾 Auto-save aktif")
        
        # Update position
        current_idx = self.data_manager.get_current_index()
        total = count
        self.position_var.set(f"Posisi: {current_idx + 1 if total > 0 else 0}/{total}")
        
        # Update statistics tab
        self.update_statistics()

    def update_treeview(self, data_list):
        """Update treeview dengan data tertentu"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        for i, mhs in enumerate(data_list, 1):
            status = "Lulus" if mhs.ipk >= 2.0 else "Belum"
            self.tree.insert('', 'end', values=(
                i, mhs.nim, mhs.nama, mhs.jurusan, f"{mhs.ipk:.2f}", status
            ))
        
        self.status_var.set(f"📊 Menampilkan {len(data_list)} data dari pencarian")

    def clear_fields(self):
        """Clear semua field input"""
        for field, widget in self.entries.items():
            try:
                if isinstance(widget, ttk.Entry):
                    widget.delete(0, tk.END)
                elif isinstance(widget, ttk.Combobox):
                    widget.set("Teknik Informatika")
            except:
                pass

    def prev_mahasiswa(self):
        """Navigate ke data sebelumnya"""
        index = self.data_manager.prev()
        self.display_current_mahasiswa(index)

    def next_mahasiswa(self):
        """Navigate ke data berikutnya"""
        index = self.data_manager.next()
        self.display_current_mahasiswa(index)

    def display_current_mahasiswa(self, index=None):
        """Display data mahasiswa saat ini ke form"""
        if index is None:
            index = self.data_manager.get_current_index()
        
        mhs = self.data_manager.get_current()
        if mhs:
            try:
                self.entries['nim'].delete(0, tk.END)
                self.entries['nim'].insert(0, mhs.nim)
                self.entries['nama'].delete(0, tk.END)
                self.entries['nama'].insert(0, mhs.nama)
                self.entries['jurusan'].set(mhs.jurusan)
                self.entries['email'].delete(0, tk.END)
                self.entries['email'].insert(0, mhs.email)
                self.entries['telepon'].delete(0, tk.END)
                self.entries['telepon'].insert(0, mhs.telepon)
                self.entries['ipk'].delete(0, tk.END)
                self.entries['ipk'].insert(0, f"{mhs.ipk:.2f}")
            except Exception as e:
                print(f"Error displaying data: {e}")

        total = self.data_manager.get_count()
        self.position_var.set(f"Posisi: {index + 1 if total > 0 else 0}/{total}")

    def on_tree_select(self, event):
        """Handle treeview selection"""
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            values = item['values']
            index = int(values[0]) - 1
            mhs = self.data_manager.get_mahasiswa(index)
            if mhs:
                self.data_manager.set_current_index(index)
                self.display_current_mahasiswa(index)

    def on_tree_double_click(self, event):
        """Handle treeview double click"""
        self.show_details()

    def exit_app(self):
        """Exit application"""
        if messagebox.askyesno("Konfirmasi", "🚪 Apakah Anda yakin ingin keluar?"):
            try:
                self.data_manager.save_to_file()
            except:
                pass
            self.root.quit()

# ============================== MAIN FUNCTION ==============================
def main():
    root = tk.Tk()
    
    # Set icon if exists
    try:
        root.iconbitmap('icon.ico')
    except:
        pass
    
    app = MahasiswaApp(root)
    
    # Center window on screen
    root.update_idletasks()
    width = root.winfo_width() or 1200
    height = root.winfo_height() or 800
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    # Handle window close event
    root.protocol("WM_DELETE_WINDOW", app.exit_app)
    
    # Bind keyboard shortcuts
    root.bind('<Control-s>', lambda e: app.save_data())
    root.bind('<Control-f>', lambda e: app.show_search_dialog())
    root.bind('<Control-n>', lambda e: app.clear_fields())
    root.bind('<Escape>', lambda e: root.focus())
    
    root.mainloop()

if __name__ == "__main__":
    main()
