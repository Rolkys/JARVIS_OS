"""
Modulo de calculadora avanzada por voz para JARVIS
"""
import re
import logging
import math
import sympy as sp

logger = logging.getLogger("JARVIS.Calculator")

class Calculator:
    """Calculadora avanzada con soporte para algebra, derivadas, matrices y mas"""
    
    def __init__(self):
        self.operations = {
            "mas": "+",
            "suma": "+",
            "sumar": "+",
            "y": "+",
            "menos": "-",
            "resta": "-",
            "restar": "-",
            "por": "*",
            "multiplicado": "*",
            "multiplicar": "*",
            "entre": "/",
            "dividido": "/",
            "dividir": "/",
            "elevado a": "**",
            "potencia de": "**",
            "raiz cuadrada de": "sqrt",
            "raiz de": "sqrt",
        }
    
    def parse_and_calculate(self, command: str) -> str:
        """Interpreta un comando y lo resuelve"""
        command_lower = command.lower().strip()
        
        for word in ["calcula", "calculame", "cuanto es", "cual es", "resuelve"]:
            command_lower = command_lower.replace(word, "")
        command_lower = command_lower.strip()
        
        # Detectar tipo de operacion
        if "derivada" in command_lower:
            return self._calculate_derivative(command_lower)
        elif "integral" in command_lower:
            return self._calculate_integral(command_lower)
        elif "ecuacion" in command_lower and ("segundo grado" in command_lower or "cuadratica" in command_lower):
            return self._solve_quadratic(command_lower)
        elif "ecuacion" in command_lower:
            return self._solve_equation(command_lower)
        elif "matriz" in command_lower and ("determinante" in command_lower):
            return self._matrix_determinant(command_lower)
        elif "matriz" in command_lower and ("inversa" in command_lower):
            return self._matrix_inverse(command_lower)
        elif "matriz" in command_lower:
            return self._matrix_operation(command_lower)
        elif "raiz cuadrada de" in command_lower or "raiz de" in command_lower:
            return self._calculate_sqrt(command_lower)
        elif "factorial" in command_lower:
            return self._calculate_factorial(command_lower)
        elif "logaritmo" in command_lower:
            return self._calculate_log(command_lower)
        elif "seno" in command_lower or "coseno" in command_lower or "tangente" in command_lower:
            return self._calculate_trig(command_lower)
        else:
            return self._calculate_basic(command_lower)
    
    def _extract_numbers(self, text: str) -> list:
        """Extrae todos los numeros de un texto"""
        return [float(n) for n in re.findall(r'-?\d+\.?\d*', text)]
    
    def _format_number(self, num) -> str:
        """Formatea un numero para mostrarlo bonito"""
        if isinstance(num, sp.Basic):
            return str(num)
        if num == int(num):
            return str(int(num))
        return f"{num:.4f}".rstrip('0').rstrip('.')
    
    # ---- DERIVADAS ----
    def _calculate_derivative(self, command: str) -> str:
        """Calcula la derivada de una expresion"""
        expr_match = re.search(r'de\s+(.+?)(?:\s+respecto|\s+con|\s*$)', command)
        var_match = re.search(r'(?:respecto a|con)\s+(\w+)', command)
        
        if expr_match:
            expr_str = expr_match.group(1).strip().replace(" ", "")
            var = var_match.group(1) if var_match else "x"
            
            try:
                x = sp.Symbol(var)
                expr = sp.sympify(expr_str)
                derivative = sp.diff(expr, x)
                return f"La derivada de {expr} respecto a {var} es {derivative}"
            except Exception as e:
                return f"Error al derivar: {str(e)}"
        
        return "Di por ejemplo: derivada de x al cuadrado mas 3x respecto a x"
    
    # ---- INTEGRALES ----
    def _calculate_integral(self, command: str) -> str:
        """Calcula la integral de una expresion"""
        expr_match = re.search(r'de\s+(.+?)(?:\s+respecto|\s+con|\s*$)', command)
        var_match = re.search(r'(?:respecto a|con)\s+(\w+)', command)
        
        if expr_match:
            expr_str = expr_match.group(1).strip().replace(" ", "")
            var = var_match.group(1) if var_match else "x"
            
            try:
                x = sp.Symbol(var)
                expr = sp.sympify(expr_str)
                integral = sp.integrate(expr, x)
                return f"La integral de {expr} respecto a {var} es {integral} mas constante"
            except Exception as e:
                return f"Error al integrar: {str(e)}"
        
        return "Di por ejemplo: integral de x al cuadrado respecto a x"
    
    # ---- ECUACIONES ----
    def _solve_quadratic(self, command: str) -> str:
        """Resuelve ecuacion de segundo grado ax^2 + bx + c = 0"""
        numbers = self._extract_numbers(command)
        
        # Ecuacion cuadratica: ax^2 + bx + c = 0
        if len(numbers) >= 3:
            a, b, c = numbers[0], numbers[1], numbers[2]
            x = sp.Symbol('x')
            eq = a*x**2 + b*x + c
            solutions = sp.solve(eq, x)
            
            response = f"Ecuacion: {a}x^2 + {b}x + {c} = 0. "
            if len(solutions) == 0:
                response += "No tiene soluciones reales"
            elif len(solutions) == 1:
                response += f"Solucion: x = {solutions[0]}"
            else:
                response += f"Soluciones: x1 = {solutions[0]}, x2 = {solutions[1]}"
            return response
        
        # Tambien aceptar formato "a b c" sueltos
        if len(numbers) >= 3:
            a, b, c = numbers[0], numbers[1], numbers[2]
            discriminant = b**2 - 4*a*c
            
            if discriminant < 0:
                return f"La ecuacion {a}x^2 + {b}x + {c} = 0 no tiene soluciones reales"
            
            x1 = (-b + math.sqrt(discriminant)) / (2*a)
            x2 = (-b - math.sqrt(discriminant)) / (2*a)
            
            if x1 == x2:
                return f"Solucion unica: x = {self._format_number(x1)}"
            return f"Soluciones: x1 = {self._format_number(x1)}, x2 = {self._format_number(x2)}"
        
        return "Di los coeficientes. Ejemplo: ecuacion de segundo grado 1 5 6"
    
    def _solve_equation(self, command: str) -> str:
        """Resuelve una ecuacion simple"""
        expr_str = command.replace("ecuacion", "").strip()
        
        if "=" in expr_str:
            parts = expr_str.split("=")
            try:
                x = sp.Symbol('x')
                left = sp.sympify(parts[0].strip())
                right = sp.sympify(parts[1].strip())
                eq = sp.Eq(left, right)
                solutions = sp.solve(eq, x)
                
                if solutions:
                    return f"Soluciones: {solutions}"
                return "No tiene solucion"
            except Exception as e:
                return f"Error: {str(e)}"
        
        return "Di la ecuacion completa. Ejemplo: 2x mas 3 igual a 7"
    
    # ---- MATRICES ----
    def _matrix_determinant(self, command: str) -> str:
        """Calcula el determinante de una matriz"""
        numbers = self._extract_numbers(command)
        
        # Detectar tamano de matriz cuadrada
        n = int(math.sqrt(len(numbers)))
        
        if n * n == len(numbers) and n > 0:
            matrix = sp.Matrix(n, n, numbers)
            det = matrix.det()
            return f"Determinante de la matriz {n}x{n}: {self._format_number(det)}"
        
        return "Necesito una matriz cuadrada. Di los numeros seguidos. Ejemplo: determinante de matriz 1 2 3 4"
    
    def _matrix_inverse(self, command: str) -> str:
        """Calcula la inversa de una matriz"""
        numbers = self._extract_numbers(command)
        n = int(math.sqrt(len(numbers)))
        
        if n * n == len(numbers) and n > 0:
            matrix = sp.Matrix(n, n, numbers)
            
            if matrix.det() == 0:
                return "Esta matriz no tiene inversa (determinante cero)"
            
            inverse = matrix.inv()
            return f"Inversa de la matriz {n}x{n}: {inverse}"
        
        return "Di los numeros de la matriz. Ejemplo: inversa de matriz 1 0 0 1"
    
    def _matrix_operation(self, command: str) -> str:
        """Operaciones basicas con matrices"""
        # Suma o resta
        if "mas" in command or "+" in command or "menos" in command or "-" in command:
            numbers = self._extract_numbers(command)
            mid = len(numbers) // 2
            
            n1 = int(math.sqrt(2))
            # Simplificamos: detectar si es suma/resta de matrices 2x2
            if len(numbers) == 8:  # Dos matrices 2x2
                matrix_a = sp.Matrix(2, 2, numbers[:4])
                matrix_b = sp.Matrix(2, 2, numbers[4:])
                
                if "menos" in command or "-" in command:
                    result = matrix_a - matrix_b
                    op = "menos"
                else:
                    result = matrix_a + matrix_b
                    op = "mas"
                
                return f"Matriz A {op} Matriz B = {result}"
            
            return "Para suma de matrices di 8 numeros. Ejemplo: matriz 1 2 3 4 mas 5 6 7 8"
        
        return "Di: determinante de matriz, inversa de matriz, o suma de matrices"
    
    # ---- BASICO ----
    def _calculate_basic(self, command: str) -> str:
        """Operaciones basicas"""
        numbers = re.findall(r'-?\d+\.?\d*', command)
        
        if len(numbers) < 2:
            # Intentar evaluar expresion con SymPy
            try:
                expr = sp.sympify(command)
                return f"Resultado: {self._format_number(expr)}"
            except:
                return "Necesito al menos dos numeros para calcular"
        
        num1 = float(numbers[0])
        num2 = float(numbers[1])
        
        for word, operator in self.operations.items():
            if word in command and operator not in ["sqrt"]:
                try:
                    if operator == "+":
                        result = num1 + num2
                    elif operator == "-":
                        result = num1 - num2
                    elif operator == "*":
                        result = num1 * num2
                    elif operator == "/":
                        if num2 == 0:
                            return "No se puede dividir entre cero"
                        result = num1 / num2
                    elif operator == "**":
                        result = num1 ** num2
                    else:
                        continue
                    
                    return self._format_basic_result(num1, num2, operator, result)
                except:
                    continue
        
        return "No entendi la operacion"
    
    def _format_basic_result(self, num1, num2, operator, result) -> str:
        """Formatea resultado basico"""
        symbols = {"+": "mas", "-": "menos", "*": "por", "/": "entre", "**": "elevado a"}
        op_word = symbols.get(operator, operator)
        return f"{self._format_number(num1)} {op_word} {self._format_number(num2)} es {self._format_number(result)}"
    
    # ---- FUNCIONES ESPECIALES ----
    def _calculate_sqrt(self, command: str) -> str:
        """Raiz cuadrada"""
        numbers = self._extract_numbers(command)
        if numbers:
            num = numbers[0]
            if num < 0:
                return "No puedo calcular la raiz de un numero negativo en los reales"
            result = math.sqrt(num)
            return f"Raiz cuadrada de {self._format_number(num)} = {self._format_number(result)}"
        return "No encontre el numero"
    
    def _calculate_factorial(self, command: str) -> str:
        """Factorial"""
        numbers = self._extract_numbers(command)
        if numbers:
            n = int(numbers[0])
            if n < 0:
                return "No existe factorial de numeros negativos"
            if n > 100:
                return "Numero demasiado grande"
            result = math.factorial(n)
            return f"{n} factorial = {result}"
        return "Di el numero"
    
    def _calculate_log(self, command: str) -> str:
        """Logaritmo"""
        numbers = self._extract_numbers(command)
        if len(numbers) >= 1:
            if len(numbers) >= 2:
                base, num = numbers[0], numbers[1]
                result = math.log(num, base)
                return f"Logaritmo base {self._format_number(base)} de {self._format_number(num)} = {self._format_number(result)}"
            else:
                num = numbers[0]
                if num <= 0:
                    return "No existe logaritmo de numeros negativos o cero"
                result = math.log10(num)
                return f"Logaritmo base 10 de {self._format_number(num)} = {self._format_number(result)}"
        return "Di el numero"
    
    def _calculate_trig(self, command: str) -> str:
        """Funciones trigonometricas"""
        numbers = self._extract_numbers(command)
        if numbers:
            angle = numbers[0]
            rad = math.radians(angle)
            
            if "seno" in command:
                result = math.sin(rad)
                return f"Seno de {self._format_number(angle)} grados = {self._format_number(result)}"
            elif "coseno" in command:
                result = math.cos(rad)
                return f"Coseno de {self._format_number(angle)} grados = {self._format_number(result)}"
            elif "tangente" in command:
                if abs(math.cos(rad)) < 0.0001:
                    return "Tangente indefinida (coseno = 0)"
                result = math.tan(rad)
                return f"Tangente de {self._format_number(angle)} grados = {self._format_number(result)}"
        
        return "Di el angulo. Ejemplo: seno de 45"