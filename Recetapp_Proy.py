import json
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class RecetarioInteligente:
    def __init__(self):
        # Configuración de base de datos SQLite
        self.conn = sqlite3.connect('recetario.db')
        self.crear_esquema_base_datos()
        
        # Inicializar ventana principal
        self.root = tk.Tk()
        self.root.title("Recetario Inteligente")
        self.root.geometry("800x600")
        
        # Variables de control
        self.ingredientes_var = tk.StringVar()
        self.dieta_var = tk.StringVar(value="Todos")
        
        # Configurar interfaz
        self.configurar_interfaz()
    def calcular_valor_nutricional_receta(self, receta_id):
            """Calcular valor nutricional total de una receta"""
            cursor = self.conn.cursor()
            
            # Consulta para obtener ingredientes y sus cantidades en la receta
            cursor.execute('''
            SELECT i.nombre, ri.cantidad, 
                i.calorias, i.proteinas, i.carbohidratos, i.grasas, i.fibra, i.sodio
            FROM receta_ingredientes ri
            JOIN ingredientes i ON ri.ingrediente_id = i.id
            WHERE ri.receta_id = ?
            ''', (receta_id,))
            
            ingredientes = cursor.fetchall()
            
            # Calcular valores nutricionales totales
            totales = {
                'calorias': 0,
                'proteinas': 0,
                'carbohidratos': 0,
                'grasas': 0,
                'fibra': 0,
                'sodio': 0
            }
            
            desglose_ingredientes = []
            
            for nombre, cantidad, cal, prot, carb, gras, fib, sod in ingredientes:
                # Calcular valores proporcionales a la cantidad
                factor = cantidad / 100  # Asumiendo que los valores nutricionales son por 100g
                
                desglose = {
                    'nombre': nombre,
                    'calorias': cal * factor,
                    'proteinas': prot * factor,
                    'carbohidratos': carb * factor,
                    'grasas': gras * factor,
                    'fibra': fib * factor,
                    'sodio': sod * factor
                }
                
                desglose_ingredientes.append(desglose)
                
                # Sumar a totales
                for key in totales:
                    totales[key] += desglose[key]
            
            return totales, desglose_ingredientes
    def visualizar_analisis_nutricional(self, receta_id):
            """Crear ventana de análisis nutricional con gráficos"""
            # Obtener valores nutricionales
            totales, desglose = self.calcular_valor_nutricional_receta(receta_id)
            
            # Crear ventana de análisis
            ventana_analisis = tk.Toplevel(self.root)
            ventana_analisis.title("Análisis Nutricional")
            ventana_analisis.geometry("800x600")
            
            # Frame para valores totales
            frame_totales = ttk.Frame(ventana_analisis)
            frame_totales.pack(padx=10, pady=10, fill='x')
            
            # Mostrar valores totales
            for key, valor in totales.items():
                ttk.Label(frame_totales, text=f"{key.capitalize()}: {valor:.2f}").pack(side='left', padx=5)
            
            # Crear figura para gráficos
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
            
            # Gráfico de pastel de macronutrientes
            macronutrientes = [
                totales['proteinas'], 
                totales['carbohidratos'], 
                totales['grasas']
            ]
            labels = ['Proteínas', 'Carbohidratos', 'Grasas']
            ax1.pie(macronutrientes, labels=labels, autopct='%1.1f%%', startangle=90)
            ax1.set_title('Distribución de Macronutrientes')
            
            # Gráfico de barras de ingredientes
            ingredientes = [ing['nombre'] for ing in desglose]
            calorias = [ing['calorias'] for ing in desglose]
            ax2.bar(ingredientes, calorias)
            ax2.set_title('Contribución Calórica por Ingrediente')
            ax2.set_xlabel('Ingredientes')
            ax2.set_ylabel('Calorías')
            plt.setp(ax2.get_xticklabels(), rotation=45, ha='right')
            
            # Ajustar layout
            plt.tight_layout()
            
            # Incrustar gráfico en Tkinter
            canvas = FigureCanvasTkAgg(fig, master=ventana_analisis)
            canvas_widget = canvas.get_tk_widget()
            canvas_widget.pack(fill='both', expand=True)
            
            # Tabla de desglose de ingredientes
            columns = ('Ingrediente', 'Calorías', 'Proteínas', 'Carbohidratos', 'Grasas', 'Fibra', 'Sodio')
            tabla = ttk.Treeview(ventana_analisis, columns=columns, show='headings')
            
            for col in columns:
                tabla.heading(col, text=col)
                tabla.column(col, width=100, anchor='center')
            
            # Insertar datos en la tabla
            for ing in desglose:
                tabla.insert('', 'end', values=(
                    ing['nombre'], 
                    f"{ing['calorias']:.2f}", 
                    f"{ing['proteinas']:.2f}", 
                    f"{ing['carbohidratos']:.2f}", 
                    f"{ing['grasas']:.2f}", 
                    f"{ing['fibra']:.2f}", 
                    f"{ing['sodio']:.2f}"
                ))
            
            tabla.pack(padx=10, pady=10, fill='x')    
    def crear_esquema_base_datos(self):
        """Crear esquema de base de datos SQLite"""
        cursor = self.conn.cursor()
        
        # Tabla de ingredientes
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS ingredientes (
            id INTEGER PRIMARY KEY,
            nombre TEXT UNIQUE,
            calorias REAL,
            proteinas REAL,
            carbohidratos REAL,
            grasas REAL,
            fibra REAL,
            sodio REAL
        )''')
        
        # Tabla de recetas
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS recetas (
            id INTEGER PRIMARY KEY,
            nombre TEXT UNIQUE,
            tipo_dieta TEXT,
            instrucciones TEXT
        )''')
        
        # Tabla de ingredientes por receta
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS receta_ingredientes (
            receta_id INTEGER,
            ingrediente_id INTEGER,
            cantidad REAL,
            FOREIGN KEY(receta_id) REFERENCES recetas(id),
            FOREIGN KEY(ingrediente_id) REFERENCES ingredientes(id)
        )''')
        
        self.conn.commit()
    def mostrar_recetas(self):
        """Modificar método para agregar botón de análisis nutricional"""
        ingredientes = {ing.strip() for ing in self.ingredientes_var.get().split(',')}
        dieta = self.dieta_var.get()

        # Limpiar frame anterior
        for widget in self.resultados_frame.winfo_children():
            widget.destroy()

        recetas = self.encontrar_recetas(dict.fromkeys(ingredientes), dieta)

        if not recetas:
            ttk.Label(self.resultados_frame, text="No se encontraron recetas").pack()
            return

        # Crear tabla de recetas con scrollbar
        columns = ('Nombre', 'Instrucciones', 'Análisis')
        tabla = ttk.Treeview(self.resultados_frame, columns=columns, show='headings')
        
        # Configurar columnas con anchos específicos
        tabla.column('Nombre', width=200)
        tabla.column('Instrucciones', width=400)
        tabla.column('Análisis', width=100)
        
        for col in columns:
            tabla.heading(col, text=col)
        
        # Añadir scrollbar vertical
        scrollbar = ttk.Scrollbar(self.resultados_frame, orient="vertical", command=tabla.yview)
        tabla.configure(yscroll=scrollbar.set)
        
        for receta in recetas:
            # Limitar las instrucciones a 200 caracteres para vista previa
            instrucciones_preview = receta[2][:200] + '...' if len(receta[2]) > 200 else receta[2]
            tabla.insert('', 'end', values=(receta[1], instrucciones_preview, 'Ver Análisis'), tags=(str(receta[0]),))
        
        # Configurar evento de doble clic
        tabla.bind('<Double-1>', self.on_tabla_doble_clic)
        
        # Mostrar tabla y scrollbar
        tabla.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Botón de análisis nutricional
        ttk.Button(
            self.resultados_frame,
            text="Ver Análisis Nutricional",
            command=lambda: self.visualizar_analisis_nutricional(receta[0])
        ).pack(pady=5)
    def on_tabla_doble_clic(self, event):
        """Manejar doble clic en la tabla de recetas para mostrar instrucciones completas"""
        tabla = event.widget
        
        # Verificar si hay una selección
        if not tabla.selection():
            return
        
        item_seleccionado = tabla.selection()[0]
        
        # Verificar si el ítem tiene tags
        tags = tabla.item(item_seleccionado)['tags']
        if not tags:
            return
        
        receta_id = tags[0]  # Asegúrate de que receta_id es un entero
        receta_id = int(receta_id)
        
        # Obtener instrucciones completas de la base de datos
        cursor = self.conn.cursor()
        cursor.execute('SELECT nombre, instrucciones FROM recetas WHERE id = ?', (receta_id,))
        receta = cursor.fetchone()
        
        # Crear ventana emergente con instrucciones completas
        ventana_instrucciones = tk.Toplevel(self.root)
        ventana_instrucciones.title(f"Instrucciones de {receta[0]}")
        ventana_instrucciones.geometry("600x400")
        
        # Añadir scrollbar a las instrucciones
        texto_instrucciones = tk.Text(ventana_instrucciones, wrap=tk.WORD)
        texto_instrucciones.insert(tk.END, receta[1])
        texto_instrucciones.config(state=tk.DISABLED)  # Hacer el texto de solo lectura
        
        scrollbar_instrucciones = ttk.Scrollbar(ventana_instrucciones, command=texto_instrucciones.yview)
        texto_instrucciones.configure(yscrollcommand=scrollbar_instrucciones.set)
        
        texto_instrucciones.pack(side='left', fill='both', expand=True)
        scrollbar_instrucciones.pack(side='right', fill='y')
        
        # Botón de análisis nutricional
        ttk.Button(
            ventana_instrucciones, 
            text="Análisis Nutricional", 
            command=lambda rid=receta_id: self.visualizar_analisis_nutricional(rid)
        ).pack(pady=5)
    def mostrar_analisis_nutricional_general(self, recetas_ids):
        """Mostrar análisis nutricional consolidado para múltiples recetas"""
        ventana_analisis = tk.Toplevel(self.root)
        ventana_analisis.title("Análisis Nutricional General")
        ventana_analisis.geometry("800x600")
        
        # Crear figura para gráficos
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        # Recopilar datos nutricionales de todas las recetas
        totales_consolidados = {
            'calorias': 0,
            'proteinas': 0,
            'carbohidratos': 0,
            'grasas': 0,
            'fibra': 0,
            'sodio': 0
        }
        
        ingredientes_desglose = []
        
        # Calcular valores para cada receta
        for receta_id in recetas_ids:
            totales, desglose = self.calcular_valor_nutricional_receta(receta_id)
            
            # Consolidar totales
            for key in totales_consolidados:
                totales_consolidados[key] += totales[key]
            
            # Agregar desglose de ingredientes
            ingredientes_desglose.extend(desglose)
        
        # Gráfico de pastel de macronutrientes
        macronutrientes = [
            totales_consolidados['proteinas'], 
            totales_consolidados['carbohidratos'], 
            totales_consolidados['grasas']
        ]
        labels = ['Proteínas', 'Carbohidratos', 'Grasas']
        ax1.pie(macronutrientes, labels=labels, autopct='%1.1f%%', startangle=90)
        ax1.set_title('Distribución de Macronutrientes')
        
        # Gráfico de barras de ingredientes (top 10)
        ingredientes_ordenados = sorted(
            ingredientes_desglose, 
            key=lambda x: x['calorias'], 
            reverse=True
        )[:10]  # Tomar los 10 ingredientes con más calorías
        
        ingredientes = [ing['nombre'] for ing in ingredientes_ordenados]
        calorias = [ing['calorias'] for ing in ingredientes_ordenados]
        
        ax2.bar(ingredientes, calorias)
        ax2.set_title('Top 10 Ingredientes por Calorías')
        ax2.set_xlabel('Ingredientes')
        ax2.set_ylabel('Calorías')
        plt.setp(ax2.get_xticklabels(), rotation=45, ha='right')
        
        # Ajustar layout
        plt.tight_layout()
        
        # Incrustar gráfico en Tkinter
        canvas = FigureCanvasTkAgg(fig, master=ventana_analisis)
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(fill='both', expand=True)
        
        # Mostrar valores totales consolidados
        frame_totales = ttk.Frame(ventana_analisis)
        frame_totales.pack(padx=10, pady=10, fill='x')
        
        for key, valor in totales_consolidados.items():
            ttk.Label(frame_totales, text=f"{key.capitalize()}: {valor:.2f}").pack(side='left', padx=5)
    def agregar_ingrediente(self, nombre, calorias, proteinas, carbohidratos, grasas, fibra, sodio):
        """Agregar ingrediente a la base de datos"""
        cursor = self.conn.cursor()
        try:
            cursor.execute('''
            INSERT OR REPLACE INTO ingredientes 
            (nombre, calorias, proteinas, carbohidratos, grasas, fibra, sodio) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (nombre, calorias, proteinas, carbohidratos, grasas, fibra, sodio))
            self.conn.commit()
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"No se pudo agregar el ingrediente: {e}")

    def agregar_receta(self, nombre, tipo_dieta, instrucciones, ingredientes):
        """Agregar receta a la base de datos"""
        cursor = self.conn.cursor()
        try:
            # Insertar receta
            cursor.execute('INSERT OR REPLACE INTO recetas (nombre, tipo_dieta, instrucciones) VALUES (?, ?, ?)',
                           (nombre, tipo_dieta, instrucciones))
            receta_id = cursor.lastrowid
            
            # Insertar ingredientes de la receta
            for ingrediente in ingredientes:
                cursor.execute('SELECT id FROM ingredientes WHERE nombre = ?', (ingrediente['nombre'],))
                ingrediente_id = cursor.fetchone()[0]
                
                cursor.execute('''
                INSERT INTO receta_ingredientes (receta_id, ingrediente_id, cantidad) 
                VALUES (?, ?, ?)
                ''', (receta_id, ingrediente_id, ingrediente['cantidad']))
            
            self.conn.commit()
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"No se pudo agregar la receta: {e}")

    def encontrar_recetas(self, ingredientes_disponibles, tipo_dieta="Todos"):
        """Encontrar recetas según ingredientes disponibles y tipo de dieta"""
        cursor = self.conn.cursor()
        
        # Consulta SQL para encontrar recetas
        query = '''
        SELECT r.id, r.nombre, r.instrucciones 
        FROM recetas r
        WHERE (? = 'Todos' OR r.tipo_dieta = ?)
        AND r.id IN (
            SELECT receta_id 
            FROM (
                SELECT receta_id, 
                       COUNT(DISTINCT ingrediente_id) as ingredientes_match,
                       COUNT(DISTINCT ingrediente_id) as total_ingredientes
                FROM receta_ingredientes ri
                JOIN ingredientes i ON ri.ingrediente_id = i.id
                WHERE i.nombre IN ({})
                GROUP BY receta_id
            ) matches
            WHERE ingredientes_match = total_ingredientes
        )
        '''.format(','.join(['?']*len(ingredientes_disponibles)))
        
        params = [tipo_dieta, tipo_dieta] + list(ingredientes_disponibles.keys())
        cursor.execute(query, params)
        
        return cursor.fetchall()

    def generar_lista_compras(self, recetas):
        """Generar lista de compras basada en recetas seleccionadas"""
        lista_compras = {}
        
        for receta_id in recetas:
            cursor = self.conn.cursor()
            cursor.execute('''
            SELECT i.nombre, ri.cantidad 
            FROM receta_ingredientes ri
            JOIN ingredientes i ON ri.ingrediente_id = i.id
            WHERE ri.receta_id = ?
            ''', (receta_id,))
            
            for ingrediente, cantidad in cursor.fetchall():
                if ingrediente not in lista_compras:
                    lista_compras[ingrediente] = cantidad
                else:
                    lista_compras[ingrediente] += cantidad
        
        return lista_compras

    def configurar_interfaz(self):
        """Configurar interfaz gráfica"""
        # Frame de ingredientes
        ingredientes_frame = ttk.LabelFrame(self.root, text="Ingredientes Disponibles")
        ingredientes_frame.pack(padx=10, pady=10, fill="x")

        ttk.Label(ingredientes_frame, text="Ingredientes (separados por coma):").pack()
        ingredientes_entry = ttk.Entry(ingredientes_frame, textvariable=self.ingredientes_var, width=50)
        ingredientes_entry.pack(padx=10, pady=5)

        # Selector de dieta
        dietas = ["Todos", "Vegetariano", "Vegano", "Sin Gluten", "Bajo en Carbohidratos"]
        ttk.Label(ingredientes_frame, text="Tipo de Dieta:").pack()
        dieta_selector = ttk.Combobox(ingredientes_frame, textvariable=self.dieta_var, values=dietas)
        dieta_selector.pack(padx=10, pady=5)

        # Botón de búsqueda
        ttk.Button(ingredientes_frame, text="Buscar Recetas", command=self.mostrar_recetas).pack(pady=5)

        # Frame de resultados
        self.resultados_frame = ttk.Frame(self.root)
        self.resultados_frame.pack(padx=10, pady=10, fill="both", expand=True)

    def mostrar_lista_compras(self, recetas):
        """Mostrar lista de compras"""
        lista_compras = self.generar_lista_compras(recetas)
        
        ventana_compras = tk.Toplevel(self.root)
        ventana_compras.title("Lista de Compras")
        
        for ingrediente, cantidad in lista_compras.items():
            ttk.Label(ventana_compras, text=f"{ingrediente}: {cantidad} gramos").pack()

    def ejecutar(self):
        """Iniciar aplicación con más ingredientes de ejemplo"""
        # Agregar más ingredientes con valores nutricionales
        ingredientes_ejemplo = [
            ("pollo", 165, 31, 0, 3.6, 0, 74),
            ("arroz", 130, 2.7, 28, 0.3, 0.4, 1),
            ("tomate", 18, 0.9, 3.9, 0.2, 1.2, 5),
            ("aceite de oliva", 884, 0, 0, 100, 0, 0),
            ("cebolla", 40, 1.1, 9.3, 0.1, 1.7, 4),
            ("ajo", 149, 6.4, 33.1, 0.5, 2.1, 17)
        ]
        
        for ingrediente in ingredientes_ejemplo:
            self.agregar_ingrediente(*ingrediente)
        
        # Agregar receta de ejemplo con más detalles
        self.agregar_receta(
            "Arroz con Pollo", 
            "Todos", 
            "1. Cortar el pollo\n2. Cocinar arroz\n3. Agregar tomate y cebolla\n4. Mezclar y servir", 
            [
                {"nombre": "pollo", "cantidad": 200},
                {"nombre": "arroz", "cantidad": 150},
                {"nombre": "tomate", "cantidad": 50},
                {"nombre": "cebolla", "cantidad": 30},
                {"nombre": "aceite de oliva", "cantidad": 10}
            ]
        )
        
        self.root.mainloop()

if __name__ == "__main__":
    app = RecetarioInteligente()
    app.ejecutar()