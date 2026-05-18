"""
Modulo de conversion de unidades para JARVIS
"""
import re
import logging

logger = logging.getLogger("JARVIS.Converter")

class UnitConverter:
    """Convierte entre diferentes unidades de medida"""

    def __init__(self):
        self.conversions = {
            # Longitud (base: metros)
            "kilometros": {"base": "metros", "factor": 1000},
            "km": {"base": "metros", "factor": 1000},
            "metros": {"base": "metros", "factor": 1},
            "m": {"base": "metros", "factor": 1},
            "centimetros": {"base": "metros", "factor": 0.01},
            "cm": {"base": "metros", "factor": 0.01},
            "milimetros": {"base": "metros", "factor": 0.001},
            "mm": {"base": "metros", "factor": 0.001},
            "millas": {"base": "metros", "factor": 1609.34},
            "yardas": {"base": "metros", "factor": 0.9144},
            "pies": {"base": "metros", "factor": 0.3048},
            "pulgadas": {"base": "metros", "factor": 0.0254},

            # Masa (base: kilogramos)
            "kilogramos": {"base": "kilogramos", "factor": 1},
            "kg": {"base": "kilogramos", "factor": 1},
            "gramos": {"base": "kilogramos", "factor": 0.001},
            "g": {"base": "kilogramos", "factor": 0.001},
            "toneladas": {"base": "kilogramos", "factor": 1000},
            "libras": {"base": "kilogramos", "factor": 0.453592},
            "onzas": {"base": "kilogramos", "factor": 0.0283495},

            # Temperatura
            "celsius": {"base": "celsius", "factor": 1},
            "fahrenheit": {"base": "celsius", "factor": "special"},
            "kelvin": {"base": "celsius", "factor": "special"},

            # Volumen (base: litros)
            "litros": {"base": "litros", "factor": 1},
            "l": {"base": "litros", "factor": 1},
            "mililitros": {"base": "litros", "factor": 0.001},
            "ml": {"base": "litros", "factor": 0.001},
            "galones": {"base": "litros", "factor": 3.78541},

            # Velocidad (base: km/h)
            "km/h": {"base": "km/h", "factor": 1},
            "kilometros por hora": {"base": "km/h", "factor": 1},
            "m/s": {"base": "km/h", "factor": 3.6},
            "metros por segundo": {"base": "km/h", "factor": 3.6},
            "mph": {"base": "km/h", "factor": 1.60934},
            "millas por hora": {"base": "km/h", "factor": 1.60934},

            # Tiempo (base: segundos)
            "segundos": {"base": "segundos", "factor": 1},
            "minutos": {"base": "segundos", "factor": 60},
            "horas": {"base": "segundos", "factor": 3600},
            "dias": {"base": "segundos", "factor": 86400},

            # Datos (base: bytes)
            "bytes": {"base": "bytes", "factor": 1},
            "kilobytes": {"base": "bytes", "factor": 1024},
            "kb": {"base": "bytes", "factor": 1024},
            "megabytes": {"base": "bytes", "factor": 1048576},
            "mb": {"base": "bytes", "factor": 1048576},
            "gigabytes": {"base": "bytes", "factor": 1073741824},
            "gb": {"base": "bytes", "factor": 1073741824},
            "terabytes": {"base": "bytes", "factor": 1099511627776},
            "tb": {"base": "bytes", "factor": 1099511627776},
        }

        self.currencies = {
            "euros": 1.0, "eur": 1.0,
            "dolares": 1.08, "usd": 1.08,
            "libras": 0.86, "gbp": 0.86,
            "yenes": 156.0, "jpy": 156.0,
            "pesos": 18.5, "mxn": 18.5,
            "bitcoin": 0.000016, "btc": 0.000016,
        }

    def parse_and_convert(self, command: str) -> str:
        """Interpreta un comando de conversion"""
        command_lower = command.lower().strip()

        for word in ["convierte", "convertir", "conversion", "pasar", "pasa", "cuantos", "cuantas", "son"]:
            command_lower = command_lower.replace(word, "")
        command_lower = command_lower.strip()

        for currency in self.currencies:
            if currency in command_lower:
                return self._convert_currency(command_lower)

        return self._convert_unit(command_lower)

    def _convert_unit(self, command: str) -> str:
        """Convierte entre unidades de medida"""
        numbers = re.findall(r'-?\d+\.?\d*', command)

        if not numbers:
            return "No encontre un numero para convertir"

        value = float(numbers[0])
        from_unit = None
        to_unit = None

        match = re.search(rf'{numbers[0]}\s*(\w+(?:\s+\w+)?)\s+(?:a|en)\s+(\w+(?:\s+\w+)?)', command)

        if match:
            from_unit = match.group(1).strip()
            to_unit = match.group(2).strip()
        else:
            units_found = []
            for unit in sorted(self.conversions.keys(), key=len, reverse=True):
                if unit in command and unit not in units_found:
                    units_found.append(unit)
                if len(units_found) == 2:
                    break

            if len(units_found) >= 2:
                idx_from = command.find(units_found[0])
                idx_to = command.find(units_found[1])
                if idx_from < idx_to:
                    from_unit, to_unit = units_found[0], units_found[1]
                else:
                    from_unit, to_unit = units_found[1], units_found[0]

        if not from_unit or not to_unit:
            return "No entendi las unidades. Di: convierte 5 kilometros a millas"

        if from_unit == to_unit:
            return f"{self._fmt(value)} {from_unit} son {self._fmt(value)} {to_unit} (misma unidad)"

        if from_unit not in self.conversions:
            return f"No conozco la unidad '{from_unit}'"
        if to_unit not in self.conversions:
            return f"No conozco la unidad '{to_unit}'"

        from_info = self.conversions[from_unit]
        to_info = self.conversions[to_unit]

        if from_info["base"] != to_info["base"]:
            return f"No puedo convertir {from_unit} a {to_unit}. Son unidades diferentes"

        if from_info["factor"] == "special" or to_info["factor"] == "special":
            return self._convert_temperature(value, from_unit, to_unit)

        base_value = value * from_info["factor"]
        result = base_value / to_info["factor"]

        return f"{self._fmt(value)} {from_unit} = {self._fmt(result)} {to_unit}"

    def _convert_temperature(self, value: float, from_unit: str, to_unit: str) -> str:
        """Conversion especial de temperatura"""
        if from_unit == "fahrenheit":
            celsius = (value - 32) * 5/9
        elif from_unit == "kelvin":
            celsius = value - 273.15
        else:
            celsius = value

        if to_unit == "fahrenheit":
            result = celsius * 9/5 + 32
        elif to_unit == "kelvin":
            result = celsius + 273.15
        else:
            result = celsius

        return f"{self._fmt(value)} grados {from_unit} = {self._fmt(result)} grados {to_unit}"

    def _convert_currency(self, command: str) -> str:
        """Conversion de monedas"""
        numbers = re.findall(r'-?\d+\.?\d*', command)

        if not numbers:
            return "No encontre una cantidad para convertir"

        value = float(numbers[0])
        from_currency = None
        to_currency = None

        for currency in sorted(self.currencies.keys(), key=len, reverse=True):
            if currency in command:
                if from_currency is None:
                    from_currency = currency
                elif to_currency is None:
                    to_currency = currency
                    break

        if not from_currency or not to_currency:
            return "Di: convierte 50 euros a dolares"

        if from_currency not in self.currencies or to_currency not in self.currencies:
            return "Moneda no soportada"

        euros = value / self.currencies[from_currency]
        result = euros * self.currencies[to_currency]

        return f"{self._fmt(value)} {from_currency} = {self._fmt(result)} {to_currency}"

    def _fmt(self, num: float) -> str:
        """Formatea numero"""
        if num == int(num):
            return str(int(num))
        if abs(num) < 0.01 or abs(num) > 1000000:
            return f"{num:.6e}"
        return f"{num:.4f}".rstrip('0').rstrip('.')